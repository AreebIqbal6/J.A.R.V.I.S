from collections import deque

class JARVIS_DSA:
    def __init__(self):
        # 1. HASH MAP: Constant time O(1) lookup for command routing.
        # This replaces slow linear O(n) if-else chains.
        self.intent_map = {
            "open": "AUTOMATION_NODE",
            "close": "AUTOMATION_NODE",
            "search": "REALTIME_NODE",
            "google": "REALTIME_NODE",
            "weather": "REALTIME_NODE",
            "look": "VISION_NODE",
            "see": "VISION_NODE",
            "screenshot": "VISION_NODE",
            "generate": "CREATION_NODE",
            "tell": "CHAT_NODE",
            "who": "CHAT_NODE",
            "what": "CHAT_NODE"
        }

        # 2. STACK: LIFO (Last-In-First-Out) structure for Command History.
        # Demonstrates state management and data persistence.
        self.history_stack = []

        # 3. QUEUE: FIFO (First-In-First-Out) structure for Task Scheduling.
        # Manages asynchronous tasks to prevent system collisions.
        self.task_queue = deque()

    def map_intent(self, query):
        """Uses Hash Map for O(1) Time Complexity classification."""
        if not query:
            return "NULL_QUERY_NODE"
        
        # Extract first word to find the "Key" in our Hash Map
        words = query.lower().split()
        first_word = words[0] if words else ""
        
        return self.intent_map.get(first_word, "GENERAL_CHAT_NODE")

    def push_history(self, command):
        """Pushes a new command onto the Stack."""
        self.history_stack.append(command)
        # Standard maintenance: prevent stack overflow by limiting to last 10
        if len(self.history_stack) > 10:
            self.history_stack.pop(0) 

    def queue_task(self, task):
        """Adds a task to the FIFO Queue for orderly processing."""
        self.task_queue.append(task)
        print(f">> DSA: Task '{task}' successfully queued.")

    def get_last_command(self):
        """Example of Stack 'Pop' logic for demonstration."""
        return self.history_stack[-1] if self.history_stack else "No history found."