# Local Imports
from .app_backend import get_today_file, parse_day, toggle_task, load_users, get_secret_key, get_algorithm, hash_pin

# Partial Imports
from datetime import datetime, UTC, timedelta
from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt
from uvicorn import Config, Server

# Full Imports
import asyncio

ACCESS_TOKEN_EXPIRE_MINUTES = 60

app = FastAPI(title="Chore Manager API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development; restrict in production
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "Chore Manager Backend is running"}


@app.get("/today")
def get_today():
    return parse_day(get_today_file())


@app.post("/toggle")
def toggle(data: dict = Body(...)):
    person = data["person"]
    index = data["index"]
    toggle_task(person, index)
    return {"status": "ok"}


@app.post("/login")
def login(data: dict):
    name = data["name"]
    pin = data["pin"]
    users = load_users()

    if name not in users:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not hash_pin(pin) == users[name]["pin_hash"]:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": name, "exp": expire}

    token = jwt.encode(to_encode, get_secret_key(), algorithm=get_algorithm())

    return {"access_token": token}


async def main():
    config = Config("app:app", port=8000, log_level="info")
    server = Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
