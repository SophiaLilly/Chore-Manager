# application/main.py

# Local External Imports
from api.routes import (
    tasks,
    admin,
    health,
)

# Partial Imports
from asyncio import run
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uvicorn import (
    Config,
    Server,
)


api = FastAPI(title="Chore Manager API", version="0.1.0")

api.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://chores.lillywhite.dev",
        "https://lillywhite.dev",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api.include_router(tasks.router)
api.include_router(admin.router)
api.include_router(health.router)


async def main():
    config = Config(
        app="app.main:api",
        host="0.0.0.0",
        log_level="info",
        port=8000,
    )
    server = Server(config)
    await server.serve()


if __name__ == "__main__":
    run(main())
