# /// script
# dependencies = ["nanodjango"]
# ///
"""
Running nanodjango as an async task alongside another async task

Usage:

    uv run hello_async_server.py
    uvx nanodjango manage hello_async_server.py
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


async def main():
    await asyncio.gather(
        app.create_server("0.0.0.0:8080"),
        say_hello(),
    )


if __name__ == "__main__":
    asyncio.run(main())
