from sys import prefix

from fastapi import FastAPI

from app.init import lifespan
from app.routers.auth import router as AuthRouter
from app.routers.groups import router as GroupRouter 
from app.routers.task import router as TaskRouter 
from app.routers.years import router as YearRouter
from app.routers.student import router as StudentRouter
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
    
)

app.include_router(AuthRouter,prefix="/api")
app.include_router(GroupRouter,prefix="/api")
app.include_router(TaskRouter,prefix="/api")
app.include_router(YearRouter,prefix="/api")
app.include_router(StudentRouter,prefix="/api")

@app.get("/hello")
async def hello():
    return "hello user"




