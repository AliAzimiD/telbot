from fastapi import FastAPI, Depends
from sqlalchemy import select
from .db import get_db
from .models import Item

app = FastAPI()

@app.get("/items")
async def list_items(db=Depends(get_db)):
    result = await db.execute(select(Item))
    return result.scalars().all()
