from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends

from .core.config import get_settings, Settings

@asynccontextmanager
async def lifespan(app: FastAPI, settings: Settings = Depends(get_settings)):
    print("startup")
    print("welcome")
    yield
    print("Shutdown")


app = FastAPI(
    lifespan=lifespan,
    title="FastAPI App",
    description="this is a training project for me to learn fastapi",
    version="v0.1.0",
)
