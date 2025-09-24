# hello_crud.py
from nanodjango.app import Django

# Initialise NanoDjango
app = Django()

# Fake in-memory database
todos = {}


# ---- Schema for Todo ----
class Todo(app.ninja.Schema):
    id: int | None = None   # Auto-assigned
    title: str
    done: bool = False


# ---- CREATE ----
@app.api.post("/todos")
def create_todo(request, payload: Todo):
    todo_id = len(todos) + 1
    todo = Todo(id=todo_id, title=payload.title, done=payload.done)
    todos[todo_id] = todo.dict()
    return todos[todo_id]


# ---- READ ALL ----
@app.api.get("/todos")
def list_todos(request):
    return list(todos.values())


# ---- READ ONE ----
@app.api.get("/todos/{todo_id}")
def get_todo(request, todo_id: int):
    todo = todos.get(todo_id)
    if not todo:
        return {"error": "Todo not found"}, 404
    return todo


# ---- UPDATE ----
@app.api.put("/todos/{todo_id}")
def update_todo(request, todo_id: int, payload: Todo):
    if todo_id not in todos:
        return {"error": "Todo not found"}, 404
    updated = todos[todo_id]
    updated["title"] = payload.title
    updated["done"] = payload.done
    todos[todo_id] = updated
    return updated


# ---- DELETE ----
@app.api.delete("/todos/{todo_id}")
def delete_todo(request, todo_id: int):
    if todo_id not in todos:
        return {"error": "Todo not found"}, 404
    del todos[todo_id]
    return {"message": "Deleted"}
