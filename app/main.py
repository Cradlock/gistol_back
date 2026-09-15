from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.errors import register_error_handlers
from app.init import lifespan
from app.routers.auth import router as AuthRouter
from app.routers.groups import router as GroupRouter
from app.routers.exam import router as ExamRouter
from app.routers.student import router as StudentRouter
from app.routers.task import router as TaskRouter
from app.routers.years import router as YearRouter

app = FastAPI(lifespan=lifespan)
register_error_handlers(app)

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
app.include_router(ExamRouter,prefix="/api")

@app.get("/hello")
async def hello():
    return "hello user"




