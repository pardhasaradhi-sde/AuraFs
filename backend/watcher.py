import time
import threading
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

SUPPORTED = {'.pdf', '.txt'}
DEBOUNCE_SECONDS = 3.0  # Wait this long after last event before processing


class SEFSEventHandler(FileSystemEventHandler):
    """
    Watches for file changes, with debouncing to prevent duplicate events
    and filtering to ignore SEFS-managed subdirectories.
    """
    
    def __init__(self, pipeline_callback):
        super().__init__()
        self.callback = pipeline_callback
        self._pending = {}       # path -> (event_type, timer)
        self._lock = threading.Lock()
    
    def _should_ignore(self, path: str) -> bool:
        """Ignore directories, .staging, hidden files, or unsupported types.
        
        NOTE: We do NOT ignore SEFS_ managed folders here.
        Internal moves by the organiser are filtered via ignore_paths in main.py,
        so user-initiated deletes/moves inside SEFS_ folders are properly detected.
        """
        p = Path(path)
        
        # Ignore directories
        if p.is_dir():
            return True
            
        # Ignore .staging directory (intermediate uploads)
        for parent in p.parents:
            if parent.name == ".staging":
                return True
        
        # Ignore hidden files
        if p.name.startswith('.'):
            return True
        
        # Ignore unsupported extensions
        if p.suffix.lower() not in SUPPORTED:
            return True
        
        return False
    
    def _schedule(self, event_type: str, path: str):
        """Debounce: schedule processing after DEBOUNCE_SECONDS of no new events for this path."""
        with self._lock:
            # Cancel existing timer for this path
            if path in self._pending:
                _, old_timer = self._pending[path]
                old_timer.cancel()
            
            # Schedule new timer
            timer = threading.Timer(
                DEBOUNCE_SECONDS,
                self._fire,
                args=(event_type, path)
            )
            timer.daemon = True
            self._pending[path] = (event_type, timer)
            timer.start()
    
    def _fire(self, event_type: str, path: str):
        """Actually trigger the pipeline after debounce period."""
        with self._lock:
            self._pending.pop(path, None)
        
        try:
            self.callback(event_type, path)
        except Exception as e:
            print(f"[WATCHER] Pipeline error for {path}: {e}")
    
    def on_created(self, event):
        if not self._should_ignore(event.src_path):
            self._schedule('created', event.src_path)
    
    def on_modified(self, event):
        if not self._should_ignore(event.src_path):
            self._schedule('modified', event.src_path)
    
    def on_deleted(self, event):
        if not self._should_ignore(event.src_path):
            self._schedule('deleted', event.src_path)
    
    def on_moved(self, event):
        if not self._should_ignore(event.src_path):
            self._schedule('deleted', event.src_path)
        if not self._should_ignore(event.dest_path):
            self._schedule('created', event.dest_path)


def start_watcher(root_folder: str, pipeline_callback):
    """Start the file system observer in a background thread."""
    handler = SEFSEventHandler(pipeline_callback)
    observer = Observer()
    # recursive=True so we can detect if user adds files DIRECTLY to root
    # but the handler filters out SEFS_ subdirectory events
    observer.schedule(handler, root_folder, recursive=True)
    observer.start()
    print(f"[WATCHER] Watching: {root_folder}")
    return observer
