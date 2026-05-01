=================================
How to build a simple API service
=================================

This example demonstrates how to build a simple CRUD (Create, Read, Update, Delete)
API using nanodjango's built-in `Django Ninja <https://django-ninja.dev/>`_ support.

Lets implement a simple "Todo" app with a database model and endpoints for creating,
listing, retrieving, updating, and deleting items.


Example code
------------

.. code-block:: python

    from django.db import models
    from nanodjango import Django

    app = Django()

    # Standard Django model
    # Decorator registers it with the admin site
    @app.admin
    class Todo(models.Model):
        title = models.CharField(max_length=200)
        done = models.BooleanField(default=False)

        def __str__(self):
            return self.title

    # Generate API schemas from the models
    # One which has all fields for reading...
    class TodoSchema(app.ninja.ModelSchema):
        class Meta:
            model = Todo
            fields = "__all__"

    # ... and one which doesn't have the ID, for create and update payloads - we'll
    # be getting the ID from the URL
    class TodoIn(app.ninja.ModelSchema):
        class Meta:
            model = Todo
            exclude = ["id"]

    # CRUD views, registered under the app's API - they all get the URL prefix /api
    @app.api.post("/todos", response=TodoSchema)
    def create_todo(request, payload: TodoIn):
        return Todo.objects.create(**payload.dict())

    @app.api.get("/todos", response=list[TodoSchema])
    def list_todos(request):
        return Todo.objects.all()

    @app.api.get("/todos/{todo_id}", response=TodoSchema)
    def get_todo(request, todo_id: int):
        try:
            return Todo.objects.get(id=todo_id)
        except Todo.DoesNotExist:
            return {"error": "Todo not found"}, 404

    @app.api.put("/todos/{todo_id}", response=TodoSchema)
    def update_todo(request, todo_id: int, payload: TodoIn):
        try:
            todo = Todo.objects.get(id=todo_id)
        except Todo.DoesNotExist:
            return {"error": "Todo not found"}, 404
        for key, value in payload.dict().items():
            setattr(todo, key, value)
        todo.save()
        return todo

    @app.api.delete("/todos/{todo_id}")
    def delete_todo(request, todo_id: int):
        try:
            todo = Todo.objects.get(id=todo_id)
        except Todo.DoesNotExist:
            return {"error": "Todo not found"}, 404
        todo.delete()
        return {"message": "Deleted"}


Running the app
---------------

Run the API using :

.. code-block:: bash

    cd /examples
    uvx nanodjango run hello_api.py


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
- Body: JSON object with new ``done`` state

.. code-block:: bash

    curl -X PUT http://127.0.0.1:8000/api/todos/1 \
      -H "Content-Type: application/json" \
      -d '{"done": true}'

Response:

.. code-block:: json

    {"id": 1, "title": "Learn nanodjango", "done": true}


**5. Delete a Todo (DELETE)**

- URL: ``/api/todos/{id}``

.. code-block:: bash

    curl -X DELETE http://127.0.0.1:8000/api/todos/1

Response:

.. code-block:: json

    {"message": "Deleted"}
