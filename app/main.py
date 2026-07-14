
from fastapi import FastAPI
from app.api.v1.photos import router



app = FastAPI(title="Photo Service", version="0.1.0")

app.include_router(router)
