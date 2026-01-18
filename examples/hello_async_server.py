"""
Running nanodjango as an async task alongside another async task
"""

import asyncio
import random

from nanodjango import Django

app = Django(
    # Avoid clashes with other examples
    SQLITE_DATABASE="hello_async.sqlite3",
    MIGRATIONS_DIR="hello_async_migrations",
)


@app.route("/")
async def view_async(request):
    sleep = random.randint(1, 5)
    await asyncio.sleep(sleep)
    return f"<p>Hello world, async view. You waited {sleep} seconds.</p>"


async def say_hello():
    while True:
        await asyncio.sleep(1)
        print("Hello!")


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    tasks = []
    tasks.append(loop.create_task(app.create_server("0.0.0.0", 8080)))
    tasks.append(loop.create_task(say_hello()))

    loop.run_forever()
