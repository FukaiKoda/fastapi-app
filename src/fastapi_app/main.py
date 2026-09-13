from contextlib import asynccontextmanager

from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("startup")
    yield
    print("Shutdown")


app = FastAPI(
    lifespan=lifespan,
    title="My first FastAPI App",
    description="this is a training project for me to learn fastapi",
    version="v0.1.0",
)
