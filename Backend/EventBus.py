import threading

class EventBus:
    def __init__(self):
        self.subscribers = {}
        self.lock = threading.Lock()

    def subscribe(self, event_type, callback):
        with self.lock:
            if event_type not in self.subscribers:
                self.subscribers[event_type] = []
            if callback not in self.subscribers[event_type]:
                self.subscribers[event_type].append(callback)

    def publish(self, event_type, data):
        with self.lock:
            callbacks = self.subscribers.get(event_type, []).copy()
            
        for callback in callbacks:
            try:
                callback(data)
            except Exception as e:
                print(f"Error in EventBus callback for {event_type}: {e}")

event_bus = EventBus()
