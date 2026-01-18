Howto: Build a Simple API
=========================

This example demonstrates how to build a simple CRUD (Create, Read, Update, Delete)
API using nanodjango’s built-in `Django Ninja <https://django-ninja.dev/>`_ support.

We implement a minimal in-memory "Todo" database with endpoints for creating,
listing, retrieving, updating, and deleting items.

Example code
------------

.. code-block:: python

    # hello_api.py
    from nanodjango.app import Django

    # Initialise nanodjango
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


Running the app
---------------

Run the API using :

.. code-block:: bash

    cd /examples
    python -m nanodjango run hello_api.py


Endpoints
---------

All endpoints are available under ``/api/``:

**1. Create a Todo (POST)**

- URL: ``/api/todos``
- Body: JSON object with ``title`` and optional ``done``

.. code-block:: bash

    curl -X POST http://127.0.0.1:8000/api/todos \
      -H "Content-Type: application/json" \
      -d '{"title": "Learn nanodjango", "done": false}'

Response:

.. code-block:: json

    {"id": 1, "title": "Learn nanodjango", "done": false}


**2. List all Todos (GET)**

- URL: ``/api/todos``

.. code-block:: bash

    curl http://127.0.0.1:8000/api/todos

Response:

.. code-block:: json

    [{"id": 1, "title": "Learn nanodjango", "done": false}]


**3. Get a Todo by ID (GET)**

- URL: ``/api/todos/{id}``

.. code-block:: bash

    curl http://127.0.0.1:8000/api/todos/1

Response:

.. code-block:: json

    {"id": 1, "title": "Learn nanodjango", "done": false}


**4. Update a Todo (PUT)**

- URL: ``/api/todos/{id}``
- Body: JSON object with updated ``title`` and ``done``

.. code-block:: bash

    curl -X PUT http://127.0.0.1:8000/api/todos/1 \
      -H "Content-Type: application/json" \
      -d '{"title": "Learn N@n0Dj@n60 deeply", "done": true}'

Response:

.. code-block:: json

    {"id": 1, "title": "Learn N@n0Dj@n60 deeply", "done": true}


**5. Delete a Todo (DELETE)**

- URL: ``/api/todos/{id}``

.. code-block:: bash

    curl -X DELETE http://127.0.0.1:8000/api/todos/1

Response:

.. code-block:: json

    {"message": "Deleted"}


Notes
-----

- ``@app.api`` is an instance of ``NinjaAPI`` automatically mounted at ``/api/``.
- ``app.ninja.Schema`` is used to define input validation and output schema.
- This example stores data in an in-memory dictionary, which resets on restart.
- For persistence, you can later integrate with Django ORM models.
