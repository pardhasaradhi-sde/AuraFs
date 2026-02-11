# Global in-memory state for SEFS
# In production you'd use a database, but for hackathon this is perfect

import time
from collections import deque

files = {}
# Format: { file_path: { "name", "text", "embedding", "cluster_id", "position_3d", "snippet" } }

clusters = {}
# Format: { cluster_id: { "name", "color", "file_count" } }

# Activity log — stores recent events for real-time display
# Each entry: { "timestamp", "type", "message", "icon" }
activity_log = deque(maxlen=50)

# Predefined colors for clusters (beautiful palette)
CLUSTER_COLORS = [
    "#00f5a0",  # mint green
    "#7b61ff",  # purple
    "#ff6b6b",  # coral red
    "#ffd93d",  # yellow
    "#4ecdc4",  # teal
    "#ff9f43",  # orange
    "#a29bfe",  # lavender
    "#fd79a8",  # pink
]

def get_color(cluster_id: int) -> str:
    return CLUSTER_COLORS[cluster_id % len(CLUSTER_COLORS)]


def add_log(log_type: str, message: str, icon: str = "ℹ️"):
    """Add an entry to the activity log."""
    entry = {
        "timestamp": time.time(),
        "time_str": time.strftime("%H:%M:%S"),
        "type": log_type,
        "message": message,
        "icon": icon,
    }
    activity_log.append(entry)
    return entry


def get_recent_logs(count: int = 20) -> list:
    """Get the most recent log entries."""
    return list(activity_log)[-count:]
