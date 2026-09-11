"""
Database Connection & Storage Adapter
Handles safe file operations, atomic writes, and data persistence
with 100% backward compatibility for existing JSON data.
"""

import os
import json
import tempfile
import threading
from typing import Any, Dict, List

_file_locks: Dict[str, threading.Lock] = {}
_global_lock = threading.Lock()


def _get_lock(filepath: str) -> threading.Lock:
    with _global_lock:
        if filepath not in _file_locks:
            _file_locks[filepath] = threading.Lock()
        return _file_locks[filepath]


def read_json_file(filepath: str, default: Any = None) -> Any:
    """Safely read a JSON file with thread safety."""
    if default is None:
        default = {}
    if not os.path.exists(filepath):
        return default

    lock = _get_lock(filepath)
    with lock:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return default
                return json.loads(content)
        except Exception:
            return default


def write_json_file(filepath: str, data: Any) -> bool:
    """Safely write data to a JSON file using atomic replacement."""
    lock = _get_lock(filepath)
    with lock:
        try:
            directory = os.path.dirname(os.path.abspath(filepath))
            os.makedirs(directory, exist_ok=True)

            # Write to temporary file in the same directory first for atomic replace
            with tempfile.NamedTemporaryFile("w", dir=directory, delete=False, encoding="utf-8") as tf:
                json.dump(data, tf, indent=4, ensure_ascii=False)
                temp_name = tf.name

            # Atomic replace (works reliably on modern Windows and Unix)
            if os.path.exists(filepath):
                try:
                    os.replace(temp_name, filepath)
                except OSError:
                    # Windows fallback if file is locked momentarily
                    import time
                    time.sleep(0.05)
                    os.replace(temp_name, filepath)
            else:
                os.rename(temp_name, filepath)
            return True
        except Exception as e:
            # Clean up temp file on failure
            try:
                if 'temp_name' in locals() and os.path.exists(temp_name):
                    os.remove(temp_name)
            except Exception:
                pass
            return False
