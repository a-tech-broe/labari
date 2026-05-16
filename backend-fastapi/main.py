from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.models import Base
from db.session import engine
from routers import auth, comments, images, posts

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Labari API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(images.router)


@app.get("/health")
def health():
    return {"status": "ok"}
