import os
import shutil
import time
import json
import asyncio
import threading
import platform
import subprocess
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from watcher import start_watcher
from extractor import extract_text, get_snippet
from embedder import embed_text
from clusterer import cluster_embeddings, get_3d_positions, name_all_clusters, get_cluster_color, CATEGORY_MAP
from organiser import sync_folders, build_cluster_map
import state

# ─── Suppress noisy loggers ──────────────────────────────────────
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

# ─── Configuration ───────────────────────────────────────────────
ROOT_FOLDER = os.path.join(os.path.dirname(__file__), "..", "root")
ROOT_FOLDER = os.path.abspath(ROOT_FOLDER)
STAGING_FOLDER = os.path.join(ROOT_FOLDER, ".staging")
os.makedirs(ROOT_FOLDER, exist_ok=True)
os.makedirs(STAGING_FOLDER, exist_ok=True)

# ─── FastAPI App ─────────────────────────────────────────────────
app = FastAPI(title="SEFS API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

connected_clients: list[WebSocket] = []
main_loop: asyncio.AbstractEventLoop = None
pipeline_lock = threading.Lock()
ignore_paths: dict = {}  # norm_path -> timestamp
IGNORE_TTL = 15.0  # seconds to ignore a path after internal move (increased for manual moves)

# ─── Batched Recluster Scheduler ─────────────────────────────────
_RECLUSTER_DELAY = 5.0          # wait this long after last file event
_recluster_timer = None
_recluster_timer_lock = threading.Lock()
_startup_done = False


# ─── WebSocket (all logging suppressed) ──────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)

    try:
        await websocket.send_text(json.dumps(get_graph_state(), default=str))
        await websocket.send_text(json.dumps({
            "type": "activity_log",
            "logs": state.get_recent_logs()
        }, default=str))
    except Exception as e:
        print(f"[WS] Initial send error: {e}")

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in connected_clients:
            connected_clients.remove(websocket)


async def broadcast(data: dict):
    try:
        message = json.dumps(data, default=str)
    except Exception as e:
        print(f"[WS] JSON serialize error: {e}")
        return
    dead = []
    for ws in connected_clients:
        try:
            await ws.send_text(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        if ws in connected_clients:
            connected_clients.remove(ws)


def _broadcast_state():
    if main_loop and main_loop.is_running():
        asyncio.run_coroutine_threadsafe(broadcast(get_graph_state()), main_loop)


def _broadcast_log(entry: dict):
    if main_loop and main_loop.is_running():
        asyncio.run_coroutine_threadsafe(broadcast({
            "type": "activity_log_entry",
            "entry": entry,
        }), main_loop)


def log_and_broadcast(log_type: str, message: str, icon: str = "ℹ️"):
    entry = state.add_log(log_type, message, icon)
    _broadcast_log(entry)


# ─── REST Endpoints ───────────────────────────────────────────────
@app.get("/graph")
def get_graph():
    return get_graph_state()

@app.get("/health")
def health():
    return {"status": "ok", "files": len(state.files), "clusters": len(state.clusters)}

@app.get("/logs")
def get_logs():
    return {"logs": state.get_recent_logs()}

@app.get("/open")
def open_file(path: str):
    try:
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.run(["open", path])
        else:
            subprocess.run(["xdg-open", path])
        return {"status": "opened"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """Uploads files to .staging folder and triggers processing."""
    saved = []
    for file in files:
        ext = Path(file.filename).suffix.lower()
        if ext not in {'.pdf', '.txt'}:
            log_and_broadcast("warning", f"Skipped {file.filename} — unsupported type", "⚠️")
            continue

        dest = os.path.join(STAGING_FOLDER, file.filename)
        if os.path.exists(dest):
            stem = Path(file.filename).stem
            counter = 1
            while os.path.exists(dest):
                dest = os.path.join(STAGING_FOLDER, f"{stem}_{counter}{ext}")
                counter += 1

        with open(dest, "wb") as f:
            content = await file.read()
            f.write(content)

        saved.append(dest)
        log_and_broadcast("upload", f"Uploaded: {Path(dest).name}", "📤")

    # Ingest all uploaded files, then schedule ONE recluster
    if saved:
        threading.Thread(target=_ingest_batch_and_recluster, args=(saved,), daemon=True).start()

    return {"status": "ok", "uploaded": [Path(p).name for p in saved], "count": len(saved)}


# ═══════════════════════════════════════════════════════════════════
# CORE PIPELINE — Ingest is separate from Recluster
# ═══════════════════════════════════════════════════════════════════

def process_pipeline(event_type: str, file_path: str):
    """
    Called by watcher for EACH file event.
    Ingests the single file (extract+embed+store) then schedules a
    batched recluster. The recluster timer resets on every new file,
    so rapid arrivals produce only ONE recluster at the end.
    """
    with pipeline_lock:
        _ingest_one(event_type, file_path)
    _schedule_recluster()


def _is_ignored(file_path: str) -> bool:
    """Check if this path should be ignored (internal move)."""
    now = time.time()
    norm = os.path.abspath(file_path).lower()

    # Cleanup expired
    expired = [p for p, t in ignore_paths.items() if now - t > IGNORE_TTL]
    for p in expired:
        ignore_paths.pop(p, None)

    return norm in ignore_paths


def _ingest_one(event_type: str, file_path: str):
    """Extract + embed + store ONE file. Does NOT cluster or move files."""
    file_name = Path(file_path).name
    norm_path = os.path.abspath(file_path).lower()

    if _is_ignored(file_path):
        return

    if event_type == 'deleted':
        removed = False
        # Try exact path first
        if file_path in state.files:
            del state.files[file_path]
            removed = True
        else:
            # Try normalized path match (handles case/slash differences)
            for fp in list(state.files.keys()):
                if os.path.abspath(fp).lower() == norm_path:
                    del state.files[fp]
                    removed = True
                    break
        if not removed:
            # Last resort: match by filename where old path is also dead
            for fp in list(state.files.keys()):
                if state.files[fp]["name"] == file_name and not os.path.exists(fp):
                    del state.files[fp]
                    removed = True
                    break
        if removed:
            log_and_broadcast("delete", f"Removed: {file_name}", "🗑️")
            # Broadcast immediately so frontend sees the deletion right away
            _broadcast_state()
        return

    if event_type not in ('created', 'modified'):
        return

    # Detect moved file: same filename exists in state at a path that no longer exists
    for fp in list(state.files.keys()):
        if fp != file_path and state.files[fp]["name"] == file_name and not os.path.exists(fp):
            # This file was moved — update its path in state
            file_data = state.files.pop(fp)
            file_data["path"] = file_path
            state.files[file_path] = file_data
            log_and_broadcast("move", f"Moved: {file_name}", "📁")
            return

    # Skip duplicate modified events for identical content
    if file_path in state.files and event_type == 'modified':
        return

    if not os.path.exists(file_path):
        return

    log_and_broadcast("detect", f"Processing: {file_name}", "👁️")

    text = extract_text(file_path)
    if not text.strip():
        log_and_broadcast("warning", f"No text in {file_name}, skipping", "⚠️")
        return

    word_count = len(text.split())
    log_and_broadcast("extract", f"Extracted {word_count} words from {file_name}", "📄")

    embedding = embed_text(text)
    log_and_broadcast("embed", f"Embedded: {file_name}", "🧠")

    state.files[file_path] = {
        "name": file_name,
        "path": file_path,
        "text": text,
        "embedding": embedding,
        "snippet": get_snippet(text),
        "cluster_id": None,
        "sub_cluster": None,
        "position_3d": [0, 0, 0],
        "word_count": word_count,
    }


def _ingest_batch_and_recluster(file_paths: list):
    """Ingest multiple files then recluster once."""
    with pipeline_lock:
        for fp in file_paths:
            _ingest_one("created", fp)
    # Direct recluster for upload (don't wait for timer)
    _do_recluster()


def _schedule_recluster():
    """
    Schedule ONE recluster after _RECLUSTER_DELAY seconds of quiet.
    Each call resets the timer — rapid file arrivals batch together.
    """
    global _recluster_timer
    with _recluster_timer_lock:
        if _recluster_timer is not None:
            _recluster_timer.cancel()
        _recluster_timer = threading.Timer(_RECLUSTER_DELAY, _do_recluster)
        _recluster_timer.daemon = True
        _recluster_timer.start()


def _do_recluster():
    """Execute the single batched recluster."""
    global _recluster_timer
    with _recluster_timer_lock:
        _recluster_timer = None

    n = len(state.files)
    if n == 0:
        state.clusters = {}
        _broadcast_state()
        return

    log_and_broadcast("cluster", f"Clustering {n} files...", "📊")

    with pipeline_lock:
        _recluster_all()

    _broadcast_state()


def _recluster_all():
    """
    Re-cluster ALL files using a hybrid approach:
    1. First, detect per-file keyword categories (strong signal)
    2. Group files that share the same keyword category
    3. For uncategorized files, use embedding-based KMeans
    4. Name KMeans clusters via keyword matching or TF-IDF
    This avoids the problem of KMeans lumping dissimilar files together.
    """
    file_paths = list(state.files.keys())
    if not file_paths:
        state.clusters = {}
        return

    embeddings = np.array([state.files[fp]["embedding"] for fp in file_paths])
    if len(embeddings) == 0:
        state.clusters = {}
        return

    positions = get_3d_positions(embeddings)

    # ── Step 1: Per-file keyword category detection ────────
    import re as _re
    file_categories = {}  # index -> category name
    for i, fp in enumerate(file_paths):
        text = state.files[fp].get("text", "").lower()
        fname = state.files[fp].get("name", "").lower()
        combined = text + " " + fname

        best_cat = None
        best_score = 0
        for category, keywords in CATEGORY_MAP.items():
            score = 0
            match_count = 0
            for kw in keywords:
                pattern = r'\b' + _re.escape(kw.lower()) + r'\b'
                hits = len(_re.findall(pattern, combined))
                if hits > 0:
                    match_count += 1
                    score += hits
            if match_count >= 1 and score > best_score:
                best_score = score
                best_cat = category
        if best_cat and best_score >= 2:
            file_categories[i] = best_cat

    # ── Step 2: Build category-based groups ────────────────
    cat_groups = {}  # category_name -> [indices]
    uncategorized = []
    for i in range(len(file_paths)):
        cat = file_categories.get(i)
        if cat:
            cat_groups.setdefault(cat, []).append(i)
        else:
            uncategorized.append(i)

    # ── Step 3: For uncategorized, sub-cluster with KMeans ──
    next_cluster_id = 0
    # final_assignments: index -> cluster_id
    final_assignments = {}
    # cluster_names_final: cluster_id -> name
    cluster_names_final = {}

    for cat_name, indices in cat_groups.items():
        cid = next_cluster_id
        next_cluster_id += 1
        cluster_names_final[cid] = cat_name
        for idx in indices:
            final_assignments[idx] = cid

    if uncategorized:
        if len(uncategorized) >= 2:
            unc_embeddings = np.array([embeddings[i] for i in uncategorized])
            unc_labels, _ = cluster_embeddings(unc_embeddings)
            # Name each sub-cluster
            unc_cluster_data = {}
            for label in set(unc_labels):
                unc_indices = [uncategorized[j] for j, l in enumerate(unc_labels) if l == label]
                unc_cluster_data[label] = {
                    "texts": [state.files[file_paths[i]]["text"] for i in unc_indices],
                    "file_names": [state.files[file_paths[i]]["name"] for i in unc_indices],
                    "files": [file_paths[i] for i in unc_indices],
                    "indices": unc_indices,
                }
            unc_names = name_all_clusters(unc_cluster_data)
            for label in set(unc_labels):
                cid = next_cluster_id
                next_cluster_id += 1
                cluster_names_final[cid] = unc_names.get(label, f"Documents {cid}")
                for j, l in enumerate(unc_labels):
                    if l == label:
                        final_assignments[uncategorized[j]] = cid
        else:
            # Single uncategorized file
            cid = next_cluster_id
            next_cluster_id += 1
            cluster_names_final[cid] = "General Documents"
            for idx in uncategorized:
                final_assignments[idx] = cid

    # ── Step 4: De-duplicate cluster names ─────────────────
    seen_names = {}
    for cid, name in list(cluster_names_final.items()):
        if name in seen_names:
            # Merge into existing cluster
            existing_cid = seen_names[name]
            for idx, assigned_cid in list(final_assignments.items()):
                if assigned_cid == cid:
                    final_assignments[idx] = existing_cid
            del cluster_names_final[cid]
        else:
            seen_names[name] = cid

    # ── Step 5: Build cluster state ────────────────────────
    new_clusters = {}
    for cid, cname in cluster_names_final.items():
        file_count = sum(1 for v in final_assignments.values() if v == cid)
        if file_count == 0:
            continue
        new_clusters[int(cid)] = {
            "id": int(cid),
            "name": cname,
            "color": get_cluster_color(int(cid)),
            "file_count": file_count,
        }

    state.clusters = new_clusters

    # ── Step 6: Update file state ──────────────────────────
    for i, file_path in enumerate(file_paths):
        pos = positions[i]
        cid = final_assignments.get(i, 0)
        state.files[file_path]["cluster_id"] = int(cid)
        state.files[file_path]["sub_cluster"] = None
        state.files[file_path]["position_3d"] = pos.tolist() if hasattr(pos, 'tolist') else [float(x) for x in pos]

    # ── Step 7: Sync OS folders ────────────────────────────
    try:
        assignments = {fp: state.files[fp]["cluster_id"] for fp in file_paths}
        cluster_names_map = {cid: state.clusters[cid]["name"] for cid in state.clusters}
        cluster_map = build_cluster_map(ROOT_FOLDER, assignments, cluster_names_map)
        _premark_moves(cluster_map)
        moves = sync_folders(ROOT_FOLDER, cluster_map)
        _apply_moves(moves)
    except Exception as e:
        print(f"[PIPELINE] Folder sync error: {e}")

    log_and_broadcast("sync", f"Organized {len(file_paths)} files into {len(new_clusters)} folders ✓", "✅")


def _premark_moves(cluster_map: dict):
    """Pre-mark source AND destination paths as ignored BEFORE organiser moves files.
    This prevents the watcher from treating internal organiser moves as user actions."""
    now = time.time()
    root_path = Path(ROOT_FOLDER)
    
    for folder_name, file_paths_list in cluster_map.items():
        dest_folder = root_path / f"SEFS_{folder_name}"
        for file_path in file_paths_list:
            src = Path(file_path)
            if src.parent == dest_folder:
                continue
            # Mark source path as ignored (watcher would see 'deleted')
            ignore_paths[os.path.abspath(str(src)).lower()] = now
            # Mark destination path as ignored (watcher would see 'created')
            dest = dest_folder / src.name
            ignore_paths[os.path.abspath(str(dest)).lower()] = now


def _apply_moves(moves: dict):
    """Update state.files with new paths after organiser moves files."""
    if not moves:
        return

    now = time.time()
    for old_path, new_path in moves.items():
        # Mark both old and new paths as ignored so watcher won't re-trigger
        ignore_paths[os.path.abspath(new_path).lower()] = now
        ignore_paths[os.path.abspath(old_path).lower()] = now

        if old_path in state.files:
            file_data = state.files.pop(old_path)
            file_data["path"] = new_path
            state.files[new_path] = file_data


# ═══════════════════════════════════════════════════════════════════
# PERIODIC RECONCILIATION — catches missed events, ghost entries
# ═══════════════════════════════════════════════════════════════════

_RECONCILE_INTERVAL = 8  # seconds between reconciliation scans


def _start_reconciliation_loop():
    """Start background thread that periodically reconciles state with disk."""
    def _loop():
        while True:
            time.sleep(_RECONCILE_INTERVAL)
            if not _startup_done:
                continue
            try:
                _reconcile_state()
            except Exception as e:
                print(f"[RECONCILE] Error: {e}")

    t = threading.Thread(target=_loop, daemon=True)
    t.start()


def _reconcile_state():
    """
    Compare in-memory state against actual disk contents.
    - Remove entries for files that no longer exist (ghosts)
    - Detect new files on disk that aren't tracked
    - Recluster if anything changed
    """
    changed = False

    with pipeline_lock:
        # ── 1. Remove ghost entries (file no longer on disk) ──────────
        for fp in list(state.files.keys()):
            if not os.path.exists(fp):
                name = state.files[fp].get("name", Path(fp).name)
                del state.files[fp]
                log_and_broadcast("delete", f"Removed (missing): {name}", "🗑️")
                changed = True

        # ── 2. Scan disk for untracked files ─────────────────────────
        root = Path(ROOT_FOLDER)
        known = {os.path.abspath(fp).lower() for fp in state.files}

        new_files = []

        # Root-level files
        try:
            for f in root.iterdir():
                if f.is_file() and f.suffix.lower() in {'.pdf', '.txt'}:
                    if os.path.abspath(str(f)).lower() not in known:
                        new_files.append(str(f))
        except OSError:
            pass

        # Files inside SEFS_ folders
        try:
            for d in root.iterdir():
                if d.is_dir() and d.name.startswith("SEFS_"):
                    for f in d.rglob("*"):
                        if f.is_file() and f.suffix.lower() in {'.pdf', '.txt'}:
                            if os.path.abspath(str(f)).lower() not in known:
                                new_files.append(str(f))
        except OSError:
            pass

        # Files in .staging
        staging = root / ".staging"
        try:
            if staging.exists():
                for f in staging.iterdir():
                    if f.is_file() and f.suffix.lower() in {'.pdf', '.txt'}:
                        if os.path.abspath(str(f)).lower() not in known:
                            new_files.append(str(f))
        except OSError:
            pass

        for fp in new_files:
            _ingest_one("created", fp)
            changed = True

    if changed:
        # Broadcast immediately so frontend sees deletions
        _broadcast_state()
        # Schedule recluster to reorganize clusters and folders
        _schedule_recluster()


# ═══════════════════════════════════════════════════════════════════
# GRAPH STATE
# ═══════════════════════════════════════════════════════════════════

def _extract_keywords(text: str, top_n: int = 5) -> list:
    """Extract simple keywords from text by word frequency."""
    import re
    from collections import Counter
    STOPWORDS = {'the','a','an','is','are','was','were','be','been','being','have','has','had',
                 'do','does','did','will','would','shall','should','may','might','can','could',
                 'and','but','or','nor','for','yet','so','in','on','at','to','from','by','with',
                 'of','about','into','through','during','before','after','above','below','between',
                 'this','that','these','those','it','its','i','we','they','he','she','you','my',
                 'your','his','her','our','their','not','no','as','if','then','than','also','just',
                 'more','most','very','much','many','some','any','each','every','all','both','such',
                 'only','same','other','new','old','one','two','three','first','last','long','great',
                 'which','what','when','where','how','who','whom','there','here','up','out','over'}
    words = re.findall(r'[a-zA-Z]{3,}', text.lower())
    counts = Counter(w for w in words if w not in STOPWORDS)
    return [w for w, _ in counts.most_common(top_n)]


def get_graph_state() -> dict:
    """Build JSON-safe graph state for frontend."""
    files_list = []
    for fp, f in list(state.files.items()):
        try:
            cid = f.get("cluster_id")
            if cid is not None:
                cid = int(cid)
            cluster = state.clusters.get(cid, {})
            pos = f.get("position_3d", [0, 0, 0])
            if hasattr(pos, 'tolist'):
                pos = pos.tolist()
            elif not isinstance(pos, list):
                pos = [float(x) for x in pos]
            else:
                pos = [float(x) for x in pos]

            text = f.get("text", "")
            keywords = _extract_keywords(text) if text else []

            files_list.append({
                "id": str(fp),
                "path": str(fp),
                "name": str(f.get("name", "")),
                "snippet": str(f.get("snippet", "")),
                "word_count": int(f.get("word_count", 0)),
                "words": int(f.get("word_count", 0)),
                "cluster": cid,
                "cluster_id": cid,
                "cluster_name": str(cluster.get("name", "Unknown")),
                "color": str(cluster.get("color", "#888888")),
                "keywords": keywords,
                "x": float(pos[0]) if len(pos) > 0 else 0.0,
                "y": float(pos[1]) if len(pos) > 1 else 0.0,
                "position": pos,
            })
        except Exception as e:
            print(f"[GRAPH] Error serializing {fp}: {e}")

    # clusters as both list and object (Graph2D uses object, Dashboard uses list)
    clusters_list = []
    clusters_obj = {}
    for c in state.clusters.values():
        try:
            cdata = {
                "id": int(c["id"]),
                "name": str(c["name"]),
                "color": str(c["color"]),
                "file_count": int(c["file_count"]),
            }
            clusters_list.append(cdata)
            clusters_obj[int(c["id"])] = cdata
        except Exception as e:
            print(f"[GRAPH] Error serializing cluster: {e}")

    return {
        "type": "graph_update",
        "nodes": files_list,
        "files": files_list,
        "clusters": clusters_list,
        "clusters_map": clusters_obj,
        "total_files": len(files_list),
    }


# ═══════════════════════════════════════════════════════════════════
# STARTUP — scan existing files, ingest all, recluster once
# ═══════════════════════════════════════════════════════════════════

def _process_existing_files():
    """Scan watched folder for existing files, ingest all, cluster once."""
    global _startup_done
    root = Path(ROOT_FOLDER)
    log_and_broadcast("startup", "Scanning for existing files...", "🔍")

    all_files = []

    # Root-level files
    for f in root.iterdir():
        if f.is_file() and f.suffix.lower() in {'.pdf', '.txt'}:
            all_files.append(f)

    # Files inside SEFS_ folders (from previous runs)
    for d in root.iterdir():
        if d.is_dir() and d.name.startswith("SEFS_"):
            for f in d.rglob("*"):
                if f.is_file() and f.suffix.lower() in {'.pdf', '.txt'}:
                    all_files.append(f)

    # Files in .staging (from uploads that haven't been processed)
    staging = root / ".staging"
    if staging.exists():
        for f in staging.iterdir():
            if f.is_file() and f.suffix.lower() in {'.pdf', '.txt'}:
                all_files.append(f)

    if not all_files:
        log_and_broadcast("startup", "No files found. Drop files to begin!", "📂")
        _startup_done = True
        return

    log_and_broadcast("startup", f"Found {len(all_files)} files, processing...", "📂")

    with pipeline_lock:
        state.files = {}
        for f in all_files:
            file_path = str(f)
            file_name = f.name
            try:
                text = extract_text(file_path)
                if not text.strip():
                    continue

                embedding = embed_text(text)

                state.files[file_path] = {
                    "name": file_name,
                    "path": file_path,
                    "text": text,
                    "embedding": embedding,
                    "snippet": get_snippet(text),
                    "cluster_id": None,
                    "sub_cluster": None,
                    "position_3d": [0, 0, 0],
                    "word_count": len(text.split()),
                }
            except Exception as e:
                print(f"[STARTUP] Error processing {file_name}: {e}")

        if state.files:
            log_and_broadcast("cluster", f"Clustering {len(state.files)} files...", "📊")
            _recluster_all()

    _broadcast_state()
    _startup_done = True
    log_and_broadcast("startup", f"Ready — {len(state.files)} files organized.", "🚀")


@app.on_event("startup")
async def startup():
    global main_loop
    main_loop = asyncio.get_event_loop()

    log_and_broadcast("startup", "SEFS initializing...", "⚡")
    state.files = {}

    threading.Thread(target=_process_existing_files, daemon=True).start()
    threading.Thread(
        target=start_watcher,
        args=(ROOT_FOLDER, process_pipeline),
        daemon=True
    ).start()
    _start_reconciliation_loop()

    log_and_broadcast("startup", f"Watching: {ROOT_FOLDER}", "👁️")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False, log_level="warning")
