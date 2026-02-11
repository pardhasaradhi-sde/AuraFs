import os
import shutil
from pathlib import Path


SEFS_PREFIX = "SEFS_"


def sync_folders(root: str, cluster_map: dict):
    """
    Sync OS folders with cluster assignments.
    cluster_map: { "FolderName": ["file_path1", "file_path2"] }
    
    Returns: dict of { old_path: new_path } for files that were moved
    """
    root_path = Path(root)
    moves = {}
    
    # 1. Create folders and move files
    for folder_name, file_paths in cluster_map.items():
        full_folder_name = f"{SEFS_PREFIX}{folder_name}"
        dest_folder = root_path / full_folder_name
        dest_folder.mkdir(exist_ok=True)
        
        for file_path in file_paths:
            src = Path(file_path)
            if not src.exists():
                continue
            
            # Already in the right folder?
            if src.parent == dest_folder:
                continue
            
            dest = dest_folder / src.name
            
            # Handle naming conflicts
            if dest.exists() and dest != src:
                stem = src.stem
                suffix = src.suffix
                counter = 1
                while dest.exists():
                    dest = dest_folder / f"{stem}_{counter}{suffix}"
                    counter += 1
            
            try:
                shutil.move(str(src), str(dest))
                moves[str(src)] = str(dest)
                print(f"[ORGANISER] Moved: {src.name} → {full_folder_name}/")
            except Exception as e:
                print(f"[ORGANISER] Failed to move {src.name}: {e}")
    
    # 2. Clean up ONLY truly empty SEFS_ folders (don't thrash on cluster changes)
    for item in root_path.iterdir():
        if item.is_dir() and item.name.startswith(SEFS_PREFIX):
            # Check if folder is empty
            try:
                contents = list(item.iterdir())
                if not contents:
                    item.rmdir()
                    print(f"[ORGANISER] Removed empty: {item.name}")
            except Exception:
                pass
    
    if moves:
        print(f"[ORGANISER] Moved {len(moves)} files ✓")
    
    return moves


def sync_nested_folders(root: str, nested_map: dict):
    """
    Create nested folder structure.
    nested_map: { "TopFolder": { "SubFolder": ["file_path1", ...] } }
    
    Returns: dict of { old_path: new_path }
    """
    root_path = Path(root)
    moves = {}
    
    for top_folder, sub_map in nested_map.items():
        top_full = f"{SEFS_PREFIX}{top_folder}"
        top_path = root_path / top_full
        top_path.mkdir(exist_ok=True)
        
        for sub_folder, file_paths in sub_map.items():
            sub_path = top_path / sub_folder
            sub_path.mkdir(exist_ok=True)
            
            for file_path in file_paths:
                src = Path(file_path)
                if not src.exists():
                    continue
                if src.parent == sub_path:
                    continue
                
                dest = sub_path / src.name
                if dest.exists() and dest != src:
                    stem = src.stem
                    suffix = src.suffix
                    counter = 1
                    while dest.exists():
                        dest = sub_path / f"{stem}_{counter}{suffix}"
                        counter += 1
                
                try:
                    shutil.move(str(src), str(dest))
                    moves[str(src)] = str(dest)
                    print(f"[ORGANISER]   {src.name} → {top_full}/{sub_folder}/")
                except Exception as e:
                    print(f"[ORGANISER] Failed to move {src.name}: {e}")
    
    return moves


def build_cluster_map(root: str, file_cluster_assignments: dict, cluster_names: dict) -> dict:
    """
    Build a map of folder names to file paths.
    file_cluster_assignments: { file_path: cluster_id }
    cluster_names: { cluster_id: "Cluster Name" }
    Returns: { "Cluster Name": [file_path1, file_path2] }
    """
    cluster_map = {}
    
    for file_path, cluster_id in file_cluster_assignments.items():
        folder_name = cluster_names.get(cluster_id, f"Cluster_{cluster_id}")
        if folder_name not in cluster_map:
            cluster_map[folder_name] = []
        cluster_map[folder_name].append(file_path)
    
    return cluster_map
