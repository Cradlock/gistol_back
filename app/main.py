from fastapi import FastAPI

from app.init import lifespan
from app.routers.auth import router as AuthRouter

app = FastAPI(lifespan=lifespan)

app.include_router(AuthRouter,prefix="/api")



@app.get("/hello")
async def hello():
    return "hello user"




