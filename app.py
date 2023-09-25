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
    allow_headers=["*"],
)


@app.get("/match/list", tags=["Matches"], status_code=200)
async def match_listing(list_params: MatchListParams = Depends()):
    res_list = get_match_list(list_params.name, list_params.filter)
    if res_list == ["no_valid_filter"]:
        raise HTTPException(
            status_code=404, detail=f"Filter {list_params.filter} is not a valid filter"
        )
    return {"Matches": res_list}
