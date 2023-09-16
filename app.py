from fastapi import *
from Database.Database import *
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from pydantic_models import *

description = """
            La Cosa
            
            This is a game about the game cards "La Cosa"
            ## The FUN is guaranteed! 
"""

origins = [
    "http://localhost:3000",
    "localhost:3000",
    "http://localhost:3000/",
    "localhost:3000/",
]

tags_metadata = [
    {"name": "Matches", "description": "Operations with users."},
    {"name": "Cards", "description": "Operations with cards."},
]

app = FastAPI(
    title="La Cosa",
    description=description,
    version="0.0.1",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],)
