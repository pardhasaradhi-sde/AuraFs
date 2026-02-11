<p align="center">
  <h1 align="center">🧠 AuraFS — Semantic Entropy File System</h1>
  <p align="center">
    <strong>AI-Powered Intelligent File Organization</strong><br/>
    <em>Drop files. Watch them organize themselves.</em>
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white" alt="React 18" />
  <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Vite-6-646CFF?logo=vite&logoColor=white" alt="Vite 6" />
  <img src="https://img.shields.io/badge/License-MIT-green" alt="MIT License" />
</p>

---

## 📖 Table of Contents

1. [What is AuraFS?](#-what-is-aurafs)
2. [Key Features](#-key-features)
3. [System Architecture](#-system-architecture)
4. [Pipeline Flow](#-pipeline-flow)
5. [Technology Stack](#-technology-stack)
6. [Project Structure](#-project-structure)
7. [Module Deep Dive](#-module-deep-dive)
8. [Getting Started](#-getting-started)
9. [API Reference](#-api-reference)
10. [How It Works — Under the Hood](#-how-it-works--under-the-hood)
11. [Error Handling & Resilience](#-error-handling--resilience)
12. [Hackathon Details](#-hackathon-details)

---

## 🧠 What is AuraFS?

AuraFS (formerly SEFS — **S**emantic **E**ntropy **F**ile **S**ystem) is an **AI-powered file organization system** that automatically reads, understands, and sorts your documents into semantically meaningful folders — **in real time**.

Instead of manually creating folders and dragging files around, you simply **drop files into a watched directory** and AuraFS:

1. **Detects** the file via real-time OS-level monitoring
2. **Extracts** text content (PDF or TXT) with auto-encoding detection
3. **Embeds** the text into a 384-dimensional semantic vector using a neural network
4. **Classifies** files using a hybrid keyword + KMeans clustering approach
5. **Names** each cluster intelligently using LLM (Groq Llama 3.3 70B) with fallbacks
6. **Organizes** your OS folders automatically to match the semantic structure
7. **Broadcasts** every step live to a React dashboard via WebSocket

> **💡 Why is this different?**
> AuraFS goes beyond keyword matching — it understands *meaning*. A file about "revenue forecasting" and another about "quarterly earnings" will be grouped together even though they share no keywords, because their *semantic embeddings* are close in vector space. The hybrid approach then ensures that domain-specific files (legal contracts, financial reports) land in precisely named categories.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🔒 **Privacy-First** | Embeddings run 100% locally using `all-MiniLM-L6-v2` — your files never leave your machine |
| ⚡ **Real-Time** | Watchdog monitors your folder. New file? Organized in seconds. |
| 🎯 **Hybrid Clustering** | Keyword-first classification (30+ categories) → KMeans for uncategorized files |
| 🤖 **LLM Naming** | Groq Llama 3.3 70B generates human-readable cluster names, with TF-IDF fallback |
| 📊 **Live Dashboard** | React + react-force-graph-2d visualization with interactive clusters |
| 📁 **OS Folder Sync** | Creates real `SEFS_*` folders on your filesystem — no virtual abstractions |
| 🔄 **WebSocket Streaming** | Every pipeline step broadcasts live to the frontend |
| 📤 **Drag & Drop Upload** | Upload files directly through the web UI |
| 🛡️ **Resilient Pipeline** | Graceful fallbacks at every stage — never crashes |

---

## 🏗 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                           │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │ Landing Page │  │  Dashboard   │  │   2D Force Graph      │  │
│  │ (LandingPage │  │ (Dashboard   │  │   (Graph2D.jsx)       │  │
│  │    .jsx)     │  │    .jsx)     │  │  • Cluster clouds     │  │
│  └──────────────┘  └──────┬───────┘  │  • File nodes         │  │
│                           │          │  • Hover tooltips      │  │
│                    ┌──────┴───────┐  │  • Click to open      │  │
│                    │ useWebSocket │  └───────────────────────┘  │
│                    │    .js       │                              │
│                    └──────┬───────┘                              │
│                           │ WebSocket                           │
├───────────────────────────┼─────────────────────────────────────┤
│                           │                                     │
│                    ┌──────┴───────┐       BACKEND (FastAPI)     │
│                    │   main.py    │                              │
│                    │ Orchestrator │                              │
│                    └──┬──┬──┬──┬──┘                              │
│           ┌───────┬──┘  │  │  └──┬────────┐                    │
│           │       │     │  │     │        │                    │
│     ┌─────┴──┐ ┌──┴───┐│  │┌────┴───┐┌───┴─────┐              │
│     │watcher │ │extrac││  ││embedder││clusterer│              │
│     │  .py   │ │tor.py││  ││  .py   ││  .py    │              │
│     └────┬───┘ └──────┘│  │└────────┘└────┬────┘              │
│          │              │  │               │                    │
│     ┌────┴────┐   ┌─────┴──┐        ┌─────┴─────┐              │
│     │watched_ │   │state.py│        │organiser  │              │
│     │folder/  │   │        │        │  .py      │              │
│     └─────────┘   └────────┘        └─────┬─────┘              │
│                                           │                    │
│                                    ┌──────┴──────┐              │
│                                    │ SEFS_*      │              │
│                                    │ Folders     │              │
│                                    └─────────────┘              │
├─────────────────────────────────────────────────────────────────┤
│                     EXTERNAL SERVICES                           │
│  ┌──────────────────────┐  ┌──────────────────────────────┐     │
│  │ Sentence-Transformers│  │ Groq API (Llama 3.3 70B)    │     │
│  │ all-MiniLM-L6-v2     │  │ Cluster naming (with        │     │
│  │ (LOCAL - 384 dims)   │  │ TF-IDF fallback)            │     │
│  └──────────────────────┘  └──────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow Diagram

```
 ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────────┐     ┌──────────┐     ┌──────────┐
 │  File    │     │  Text    │     │   AI     │     │   Hybrid     │     │  Folder  │     │ WebSocket│
 │ Dropped  │────▶│Extracted │────▶│Embedding │────▶│  Clustering  │────▶│  Sync    │────▶│Broadcast │
 │          │     │          │     │          │     │              │     │          │     │          │
 │ watcher  │     │extractor │     │ embedder │     │ keyword-first│     │organiser │     │ main.py  │
 │   .py    │     │  .py     │     │   .py    │     │ + KMeans     │     │  .py     │     │          │
 └──────────┘     └──────────┘     └──────────┘     └──────────────┘     └──────────┘     └──────────┘
    3s debounce    PDF: 10 pages    384-dim vector    30+ categories      Creates SEFS_*    Real-time
                   TXT: auto-enc    Chunked avg       + silhouette       Move files        graph update
```

---

## 🔄 Pipeline Flow

### Step-by-Step Processing

```
1. FILE DETECTION
   └─ Watchdog observer monitors root/ (recursive)
   └─ Debounces rapid events (3s window)
   └─ Ignores: SEFS_* folders, hidden files, .staging/, unsupported types
   └─ Supported: .pdf, .txt

2. TEXT EXTRACTION (extractor.py)
   └─ PDF → PyMuPDF (first 10 pages, whitespace cleaned)
   └─ TXT → chardet auto-encoding detection (UTF-8, Latin-1, etc.)
   └─ Returns clean text string (empty string on failure)

3. SEMANTIC EMBEDDING (embedder.py)
   └─ Model: all-MiniLM-L6-v2 (22M params, runs locally)
   └─ Short text (≤500 chars) → embed directly
   └─ Long text → chunk at sentence boundaries (500 chars/chunk, max 20)
      └─ Batch embed all chunks
      └─ Weighted average (earlier chunks = higher weight)
      └─ L2 normalize to unit vector
   └─ Output: 384-dimensional numpy vector

4. HYBRID CLUSTERING (main.py → clusterer.py)
   ┌─ PHASE A: Keyword-First Classification
   │  └─ For each file: scan text + filename against CATEGORY_MAP
   │  └─ 30+ categories (Financial, Legal, AI Research, Biology, etc.)
   │  └─ Word-boundary regex matching with scoring
   │  └─ Filename matches weighted 3x (filename is strong signal)
   │  └─ Threshold: ≥1 keyword match AND score ≥2
   │  └─ Group files by detected category
   │
   ├─ PHASE B: KMeans for Uncategorized
   │  └─ Files with no keyword match → KMeans clustering
   │  └─ Optimal K via silhouette score (K=2 to K=8)
   │  └─ Name clusters via Groq LLM or TF-IDF fallback
   │
   └─ PHASE C: De-duplication & Merge
      └─ Merge clusters with identical names
      └─ Build final assignments map

5. 3D POSITIONING (clusterer.py)
   └─ n < 15 files → PCA projection to 3D
   └─ n ≥ 15 files → UMAP projection to 3D
   └─ Normalize coordinates to [-5, 5] range
   └─ Used for x/y positions in 2D graph visualization

6. FOLDER SYNCHRONIZATION (organiser.py)
   └─ Create SEFS_<ClusterName>/ folders
   └─ Move files into assigned folders
   └─ Handle naming conflicts (_1, _2 suffixes)
   └─ Clean up empty SEFS_* folders
   └─ Pre-mark moved paths so watcher ignores them (15s TTL)

7. BROADCAST (main.py)
   └─ Serialize graph state (files, clusters, positions)
   └─ WebSocket → all connected frontend clients
   └─ Activity log entry → real-time event stream
```

---

## 🛠 Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend Framework** | FastAPI + Uvicorn | Async REST API + WebSocket server |
| **File Watching** | Watchdog | OS-level file system event monitoring |
| **Text Extraction** | PyMuPDF (fitz) | PDF text extraction (up to 10 pages) |
| **Encoding Detection** | chardet | Auto-detect TXT file encodings |
| **AI Embeddings** | Sentence-Transformers (`all-MiniLM-L6-v2`) | Convert text → 384-dim vectors (LOCAL) |
| **Clustering** | scikit-learn (KMeans) | Group similar embeddings |
| **Cluster Evaluation** | scikit-learn (Silhouette Score) | Find optimal cluster count |
| **Dimensionality Reduction** | PCA / UMAP | Project 384-dim → 3D for visualization |
| **LLM Naming** | Groq API (Llama 3.3 70B Versatile) | Content-aware cluster names |
| **Fallback Naming** | TF-IDF (scikit-learn) | Keyword extraction when LLM unavailable |
| **Frontend** | React 18 + Vite 6 | Reactive dashboard UI |
| **Visualization** | react-force-graph-2d | Interactive 2D cluster graph |
| **Styling** | Tailwind CSS 3 | Utility-first styling |
| **Real-time Comms** | WebSocket (native) | Live activity log + state updates |
| **Routing** | react-router-dom v7 | SPA navigation |
| **Icons** | Lucide React + Material Symbols | UI iconography |

---

## 📁 Project Structure

```
sefs/
├── README.md                    ← You are here
├── ARCHITECTURE.md              ← Detailed system documentation
│
├── backend/
│   ├── main.py                  ← FastAPI server + pipeline orchestrator (671 lines)
│   │                               • REST endpoints (/graph, /upload, /open, /health)
│   │                               • WebSocket broadcast system
│   │                               • Hybrid _recluster_all() algorithm
│   │                               • Startup file scanner
│   │
│   ├── extractor.py             ← PDF/TXT text extraction (58 lines)
│   │                               • PyMuPDF for PDFs (10-page cap)
│   │                               • chardet auto-encoding for TXT
│   │
│   ├── embedder.py              ← Chunked AI embedding (98 lines)
│   │                               • all-MiniLM-L6-v2 (384-dim output)
│   │                               • Sentence-boundary chunking
│   │                               • Weighted average with L2 normalization
│   │
│   ├── clusterer.py             ← Clustering + naming engine (725 lines)
│   │                               • CATEGORY_MAP (30+ categories, 500+ keywords)
│   │                               • KMeans with silhouette optimization
│   │                               • Groq LLM naming → TF-IDF fallback
│   │                               • PCA/UMAP 3D projection
│   │
│   ├── watcher.py               ← File system monitor (110 lines)
│   │                               • Watchdog observer with 3s debounce
│   │                               • SEFS_* folder ignore filter
│   │
│   ├── organiser.py             ← OS folder synchronization (131 lines)
│   │                               • Create/sync SEFS_* folders
│   │                               • File moves with conflict resolution
│   │                               • Empty folder cleanup
│   │
│   ├── state.py                 ← Global in-memory state (49 lines)
│   │                               • files dict, clusters dict
│   │                               • Activity log (deque, max 50 entries)
│   │                               • Cluster color palette (8 colors)
│   │
│   ├── generate_test_data.py    ← Test data generator (70 lines)
│   │                               • Creates 11 sample files (physics + biology)
│   │
│   └── requirements.txt        ← Python dependencies (11 packages)
│
├── frontend/
│   ├── package.json             ← Frontend dependencies
│   ├── vite.config.js           ← Vite build configuration
│   ├── tailwind.config.js       ← Tailwind CSS config
│   ├── postcss.config.js        ← PostCSS config
│   ├── index.html               ← HTML entry point
│   │
│   ├── public/                  ← Static assets
│   │
│   └── src/
│       ├── main.jsx             ← React entry point + BrowserRouter
│       ├── App.jsx              ← Route definitions (/ → Landing, /dashboard → Dashboard)
│       ├── App.css              ← Global styles + dark theme
│       ├── index.css            ← Tailwind directives
│       ├── Landing.css          ← Landing page styles
│       │
│       ├── LandingPage.jsx      ← Landing page (292 lines)
│       │                           • Hero section, feature grid
│       │                           • Workflow visualization
│       │                           • CTA buttons
│       │
│       ├── Dashboard.jsx        ← Main dashboard (373 lines)
│       │                           • Stats cards (files, clusters, words)
│       │                           • Pipeline visualization banner
│       │                           • File upload (drag & drop + click)
│       │                           • Cluster cards with file lists
│       │                           • Activity log (real-time)
│       │                           • Graph overlay toggle
│       │
│       ├── components/
│       │   ├── Graph2D.jsx      ← 2D force graph (367 lines)
│       │   │                       • Cluster glow backgrounds
│       │   │                       • File node rendering
│       │   │                       • Hover tooltips with metadata
│       │   │                       • Click-to-open file
│       │   │
│       │   └── Graph3D.jsx      ← 3D graph (optional)
│       │
│       └── hooks/
│           └── useWebSocket.js  ← WebSocket hook (113 lines)
│                                   • Auto-reconnect with exponential backoff
│                                   • State management for graph + logs
│
└── root/                        ← Drop files here!
    ├── SEFS_Biology Research/   ← Auto-created by AuraFS
    ├── SEFS_Physics Research/   ← Auto-created by AuraFS
    └── ...
```

---

## 🔬 Module Deep Dive

### Backend Pipeline — `main.py`

The central orchestrator that wires all modules together:

| Component | Description |
|-----------|-------------|
| `pipeline_lock` | Threading lock preventing concurrent pipeline runs |
| `ignore_paths` | Dict of paths to ignore (TTL=15s) to prevent watcher re-triggers |
| `_RECLUSTER_DELAY` | 5s debounce before re-clustering (batches rapid file drops) |
| `_startup_done` | Flag to distinguish startup scan from live file events |

**Key Functions:**

- **`process_pipeline(event, path)`** — Entry point from watcher. Routes created/modified/deleted events.
- **`_ingest_one(path)`** — Extract → Embed → Store a single file.
- **`_do_recluster()`** — Debounced recluster trigger. Waits 5s after last file event.
- **`_recluster_all()`** — The brain: hybrid keyword-first + KMeans clustering.
- **`get_graph_state()`** — Serializes state to JSON for frontend (files + clusters + positions).
- **`_process_existing_files()`** — Startup scanner: ingests all existing files, clusters once.

**Threading Model:**
```
Main Thread (asyncio)      →  FastAPI + WebSocket handling
Background Thread 1        →  _process_existing_files() on startup
Background Thread 2        →  Watchdog Observer (file monitoring)
Timer Threads (per-file)   →  Debounce timers from watcher
Timer Thread               →  Recluster delay (5s batch window)
```

### Hybrid Clustering Algorithm

The core innovation — a two-phase approach that combines **domain knowledge** with **unsupervised learning**:

```
Input: N files with embeddings + extracted text

Phase 1 — Keyword Classification (Deterministic)
  For each file:
    1. Tokenize text into words
    2. Match against CATEGORY_MAP (30+ categories, 500+ keywords)
    3. Score = Σ(word-boundary matches) + 3× filename matches
    4. If score ≥ 2 AND match_count ≥ 1 → assign to category
    5. Group all files with same category into one cluster

Phase 2 — KMeans Fallback (Unsupervised)
  For uncategorized files (no keyword matches):
    1. Extract their embeddings (384-dim vectors)
    2. If only 1-2 files → assign to "General Documents"
    3. If 3+ files → KMeans with silhouette optimization
       - Try K = 2 to min(8, n-1)
       - Pick K with highest silhouette score
       - Name via Groq LLM or TF-IDF
    4. Assign cluster IDs

Phase 3 — Merge & Deduplicate
  - If KMeans produces a name matching an existing category → merge
  - Reassign cluster IDs for clean sequential numbering
```

**Why hybrid?** Pure KMeans lumps dissimilar files together when file count is low. Pure keyword matching misses novel topics. The hybrid approach gets the best of both — precise categorization for known domains, intelligent grouping for unknown ones.

### Embedding Strategy — `embedder.py`

```
Input Text → Length Check
  │
  ├─ Short (≤500 chars) → Direct embedding → 384-dim vector
  │
  └─ Long (>500 chars) → Chunk at sentence boundaries
                           │
                           ├─ Chunk 0: weight 1.00 (most important)
                           ├─ Chunk 1: weight 0.91
                           ├─ Chunk 5: weight 0.67
                           ├─ ...
                           └─ Chunk 19: weight 0.33 (least important)
                           │
                           └─ Weighted average → L2 normalize → 384-dim vector
```

**Why weighted?** Introductions and abstracts contain the strongest topic signals. The decay formula `1/(1 + 0.1i)` gives early chunks ~3× the influence of late chunks.

### CATEGORY_MAP — `clusterer.py`

30+ domain categories with 500+ keywords enabling precise classification:

| Category | Example Keywords |
|----------|-----------------|
| Financial Documents | revenue, profit, balance sheet, audit, payroll |
| Legal Documents | contract, compliance, litigation, patent, NDA |
| AI Research | neural network, transformer, deep learning, LLM |
| Biology Research | DNA, gene, CRISPR, mitosis, ecology |
| Physics Research | quantum, thermodynamics, relativity, photon |
| Medical Records | patient, diagnosis, prescription, surgery |
| Startup Documents | pitch, venture, funding, burn rate, MVP |
| Software Engineering | API, framework, devops, docker, microservices |
| *...and 22 more* | |

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+**
- **Node.js 18+** & npm
- **Groq API Key** (optional — system works without it using TF-IDF fallback)

### 1. Clone & Install Backend

```bash
cd sefs/backend
pip install -r requirements.txt
```

**Dependencies installed:**
```
fastapi           — Web framework with WebSocket support
uvicorn           — ASGI server
watchdog          — File system monitoring
pymupdf           — PDF text extraction
chardet           — Encoding detection
sentence-transformers — Local AI embeddings (downloads ~90MB model on first run)
scikit-learn      — KMeans, TF-IDF, Silhouette Score
umap-learn        — UMAP dimensionality reduction
numpy             — Vector operations
groq              — Groq Cloud API client
python-multipart  — File upload support
```

### 2. Install Frontend

```bash
cd sefs/frontend
npm install
```

### 3. Set Environment Variables (Optional)

```bash
# For LLM-powered cluster naming (optional)
set GROQ_API_KEY=gsk_your_key_here
```

> Without a Groq API key, AuraFS falls back to TF-IDF keyword extraction for naming clusters. The system works perfectly — names are just slightly less polished.

### 4. Start Backend

```bash
cd sefs/backend
python main.py
```

Server starts on **http://localhost:8000**

### 5. Start Frontend

```bash
cd sefs/frontend
npm run dev
```

Dev server starts on **http://localhost:5173**

### 6. Use It!

1. Open **http://localhost:5173** in your browser
2. Click **LAUNCH DASHBOARD**
3. Drop `.pdf` or `.txt` files into the `root/` directory (or drag into the web UI)
4. Watch the dashboard update in real-time as files are analyzed and organized!

### Generate Test Data

```bash
cd sefs/backend
python generate_test_data.py
```

Creates 11 sample files (6 physics + 5 biology) to demonstrate clustering.

---

## 📡 API Reference

### WebSocket `/ws`

Real-time bidirectional communication.

**On connect, server sends:**
```json
{
  "type": "graph_update",
  "nodes": [...],
  "files": [...],
  "clusters": [...],
  "clusters_map": { "0": {...}, "1": {...} },
  "total_files": 7
}
```
```json
{
  "type": "activity_log",
  "logs": [{ "timestamp": 1707..., "time_str": "21:15:03", "type": "cluster", "message": "...", "icon": "📁" }]
}
```

**Incremental updates:**
```json
{ "type": "activity_log_entry", "entry": { ... } }
```

### REST Endpoints

| Endpoint | Method | Description | Response |
|----------|--------|-------------|----------|
| `/ws` | WebSocket | Real-time state + log streaming | Bidirectional |
| `/graph` | GET | Current graph state | `{ nodes, files, clusters, clusters_map, total_files }` |
| `/health` | GET | Health check | `{ status, files, clusters }` |
| `/logs` | GET | Recent activity log | `{ logs: [...] }` |
| `/open?path=...` | GET | Open file in OS default app | `{ status: "opened" }` |
| `/upload` | POST | Upload files (multipart) | `{ status, uploaded, count }` |

### File Node Schema

```json
{
  "id": "D:\\path\\to\\file.pdf",
  "path": "D:\\path\\to\\file.pdf",
  "name": "file.pdf",
  "snippet": "First 200 chars of content...",
  "word_count": 1523,
  "cluster_id": 0,
  "cluster_name": "AI Research",
  "color": "#6366f1",
  "keywords": ["neural", "learning", "model", "training", "network"],
  "x": 1.23,
  "y": -3.45,
  "position": [1.23, -3.45, 5.67]
}
```

### Cluster Schema

```json
{
  "id": 0,
  "name": "AI Research",
  "color": "#6366f1",
  "file_count": 4
}
```

---

## ⚙ How It Works — Under the Hood

### Token Limit Management

Large files can contain 50,000+ characters. AuraFS handles this through three layers:

| Layer | Module | Strategy | Limit |
|-------|--------|----------|-------|
| **Extraction** | `extractor.py` | PDFs capped at 10 pages | ~5,000 words |
| **Embedding** | `embedder.py` | Chunked: 500-char chunks, batch embed, weighted avg | 20 chunks = 10,000 chars |
| **LLM Naming** | `clusterer.py` | `_smart_truncate()`: 60% start + 40% end, 300 chars/file | ~7,200 chars total |

### Watcher Anti-Loop Design

When AuraFS moves a file into `SEFS_Finance/`, the watcher would detect this as a new "create" event, triggering an infinite loop. Three mechanisms prevent this:

1. **`_should_ignore()`** — Filters out ALL events inside `SEFS_*` directories
2. **`ignore_paths`** — Pre-marks destination paths before moves (15s TTL)
3. **`_premark_moves()`** — Registers expected move destinations before they happen

### WebSocket Architecture

```
Backend (Python)                    Frontend (React)
┌─────────────┐                    ┌──────────────────┐
│ main.py     │   WebSocket        │ useWebSocket.js  │
│             │◄──────────────────▶│                  │
│ broadcast() │   JSON messages    │ • graphData      │
│             │                    │ • logs           │
│ Async event │                    │ • connected      │
│ loop        │                    │                  │
└─────────────┘                    │ Auto-reconnect   │
                                   │ (exp. backoff)   │
                                   │ 2s→4s→8s→16s→30s│
                                   └──────────────────┘
```

### Graph Visualization — `Graph2D.jsx`

The 2D force graph renders three layers using canvas:

1. **Cluster Clouds** — Radial gradient backgrounds centered on cluster centroid, sized by member count
2. **Links** — Semi-transparent lines connecting files to their cluster center
3. **File Nodes** — Colored circles with filename labels

**Interaction:**
- **Hover** → Tooltip with filename, cluster, word count, keywords, snippet
- **Click file** → Opens file via backend `/open` endpoint
- **Click cluster** → Zooms to fit that cluster
- **Scroll** → Zoom in/out
- **Drag** → Pan the canvas

---

## 🛡 Error Handling & Resilience

| Scenario | How AuraFS Handles It |
|----------|----------------------|
| PDF extraction fails | Returns empty string, logs warning, skips file |
| Encoding detection fails | Falls back to UTF-8 with error replacement |
| Groq API down | Falls back to TF-IDF keyword extraction for naming |
| Groq rate limited | Falls back to TF-IDF (no crash) |
| File moved by organiser triggers watcher | `_should_ignore()` + `ignore_paths` prevents re-trigger |
| Rapid file saves | 3s debounce in watcher prevents duplicate processing |
| Many files dropped at once | 5s recluster delay batches all into one clustering pass |
| Concurrent pipeline calls | `pipeline_lock` serializes all processing |
| WebSocket client disconnects | Removed from pool, no error |
| WebSocket send fails | Client marked dead, removed from pool |
| File naming conflicts | Appends `_1`, `_2`, etc. |
| Empty text extracted | Logs warning, skips file |
| numpy types in JSON | `default=str` serializer handles all edge cases |

---

## 🏆 Hackathon Details

### Problem Statement

**Intelligent File Organization Using AI** — Build a system that automatically understands and organizes files based on their semantic content, eliminating the need for manual folder management.

### Our Solution

AuraFS is a **real-time, AI-powered semantic file organizer** that combines:

- **Local AI** (all-MiniLM-L6-v2) for privacy-preserving document understanding
- **Hybrid clustering** (keyword-first + KMeans) for accurate categorization
- **LLM naming** (Groq Llama 3.3 70B) for human-readable folder names
- **Live visualization** (React + force-directed graphs) for intuitive monitoring
- **OS-level integration** (actual folder creation + file moves) for tangible results

### What Makes AuraFS Unique

1. **Hybrid Approach** — No other solution combines deterministic keyword classification with unsupervised ML clustering. This achieves both precision (for known domains) and flexibility (for novel topics).

2. **Privacy-First** — Embeddings run 100% locally. Only cluster naming (optionally) uses a cloud API, and even that has a fully offline TF-IDF fallback.

3. **Real, Not Virtual** — AuraFS creates actual OS folders. Close the app, and your files are still organized. This isn't a virtual overlay — it's a permanent improvement.

4. **Live Pipeline Visualization** — Every step of the AI pipeline is visible in real-time through WebSocket streaming and an interactive force-directed graph.

### Team

**It Works On My Machine**

### TeamLead

**Pardha Saradhi(Pardhu)**

### Tech Stack Summary

```
Backend:   Python 3.10+ | FastAPI | Sentence-Transformers | KMeans | Groq
Frontend:  React 18 | Vite 6 | Tailwind CSS | react-force-graph-2d
ML:        all-MiniLM-L6-v2 (local) | KMeans + Silhouette | PCA/UMAP
Comms:     WebSocket (real-time) | REST API
```

---

<p align="center">
  <strong>AuraFS</strong> — Let your files organize themselves. 🧠📁
</p>
