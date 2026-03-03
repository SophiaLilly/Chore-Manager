from fastapi import FastAPI, APIRouter, Request, Response, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Any, Dict, Optional
import logging
import os

app = FastAPI(title="Chore Manager API", version="0.1.0")

api_router = APIRouter()

# TODOs:
# - Add route handlers (GET/POST/PUT/DELETE) on api_router
# - Add dependencies, auth, middleware, and event handlers
# - Add tests and a requirements file (fastapi, pydantic, uvicorn)

