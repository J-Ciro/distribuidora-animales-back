from fastapi import FastAPI
from .routers import productos
from .database import engine, Base
import os

# Create tables (simple auto-create for development)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Inventory HU API")
app.include_router(productos.router)

@app.get('/')
def root():
    return {"status": "ok"}
