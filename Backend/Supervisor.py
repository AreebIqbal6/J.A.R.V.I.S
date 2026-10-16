"""
Backend/Supervisor.py
Phase 6: Watchdog and Process Supervisor for background worker threads.
Ensures crashed background tasks restart with exponential backoff rather
than dying silently. Logs all crash events and updates EventBus health state.
"""

import time
import threading
import traceback
import logging
from typing import Callable, Dict, Any, Optional

from Backend.EventBus import EventBus

class SupervisedTask:
    def __init__(self, name: str, target: Callable, min_backoff: float = 2.0, max_backoff: float = 60.0):
        self.name = name
        self.target = target
        self.min_backoff = min_backoff
        self.max_backoff = max_backoff
        self.current_backoff = min_backoff
        self.restart_count = 0
        self.is_running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.last_crash: Optional[str] = None
        self.last_crash_time: Optional[float] = None

    def start(self):
        if self.is_running:
            return
        self._stop_event.clear()
        self.is_running = True
        self._thread = threading.Thread(target=self._run_loop, name=f"Supervisor-{self.name}", daemon=True)
        self._thread.start()
        print(f">> [SUPERVISOR]: Supervised worker '{self.name}' launched.")

    def stop(self):
        self._stop_event.set()
        self.is_running = False

    def _run_loop(self):
        while not self._stop_event.is_set():
            try:
                # Mark subsystem healthy in EventBus
                EventBus.emit("health", {"subsystems": {self.name: "ok"}})
                # Run worker target
                self.target()
                # If target exits normally without looping, exit cleanly
                break
            except Exception as e:
                self.restart_count += 1
                self.last_crash = traceback.format_exc()
                self.last_crash_time = time.time()
                
                print(f"!! [SUPERVISOR CRASH]: Worker '{self.name}' crashed (Restart #{self.restart_count}): {e}")
                print(f"!! [SUPERVISOR BACKOFF]: Backing off for {self.current_backoff:.1f}s before restart...")
                
                # Emit degraded status to HUD
                EventBus.emit("health", {
                    "subsystems": {self.name: f"restarting (backoff {self.current_backoff:.1f}s)"}
                })

                # Sleep with backoff
                self._stop_event.wait(self.current_backoff)
                
                # Exponential backoff with ceiling
                self.current_backoff = min(self.max_backoff, self.current_backoff * 2.0)
            else:
                # Reset backoff upon clean completion or extended healthy runtime
                self.current_backoff = self.min_backoff

class WatchdogSupervisor:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(WatchdogSupervisor, cls).__new__(cls)
            cls._instance.tasks: Dict[str, SupervisedTask] = {}
            cls._instance._lock = threading.Lock()
        return cls._instance

    def register(self, name: str, target: Callable, min_backoff: float = 2.0, max_backoff: float = 60.0):
        with self._lock:
            task = SupervisedTask(name, target, min_backoff, max_backoff)
            self.tasks[name] = task
            return task

    def start(self, name: str):
        with self._lock:
            if name in self.tasks:
                self.tasks[name].start()

    def start_all(self):
        with self._lock:
            for task in self.tasks.values():
                task.start()

    def stop_all(self):
        with self._lock:
            for task in self.tasks.values():
                task.stop()

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            status = {}
            for name, task in self.tasks.items():
                status[name] = {
                    "running": task.is_running,
                    "restarts": task.restart_count,
                    "backoff": task.current_backoff,
                    "last_crash": task.last_crash,
                    "last_crash_time": task.last_crash_time
                }
            return status

# Global supervisor singleton
Supervisor = WatchdogSupervisor()
