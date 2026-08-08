class ToDoList:
    def __init__(self):
        self.tasks = []

    def add_task(self, task):
        self.tasks.append(task)
        print(f"Task '{task}' added successfully.")

    def view_tasks(self):
        if not self.tasks:
            print("No tasks available.")
        else:
            for i, task in enumerate(self.tasks, start=1):
                print(f"{i}. {task}")

    def delete_task(self, task_number):
        try:
            task_number = int(task_number)
            if task_number <= 0:
                print("Invalid task number.")
            elif task_number > len(self.tasks):
                print("Task not found.")
            else:
                del self.tasks[task_number - 1]
                print("Task deleted successfully.")
        except ValueError:
            print("Invalid task number.")

def main():
    todo = ToDoList()
    todo.add_task("Buy milk")
    todo.add_task("Walk the dog")
    todo.view_tasks()
    todo.delete_task("1")
    todo.view_tasks()
    print("Application closed.")

if __name__ == "__main__":
    main()