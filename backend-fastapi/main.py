from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from db.session import check_db
from routers import auth, comments, images, posts

app = FastAPI(
    title="Labari API",
    version="2.0.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(images.router)


@app.get("/health")
def health():
    db_ok = check_db()
    if not db_ok:
        from fastapi import Response
        return Response(
            content='{"status":"degraded","db":false}',
            status_code=503,
            media_type="application/json",
        )
    return {"status": "ok", "db": True}
