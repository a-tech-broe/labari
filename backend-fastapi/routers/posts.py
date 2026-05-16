import re
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, or_, update
from sqlalchemy.orm import Session
from ulid import ULID

from core.auth import get_current_user
from db.models import Post
from db.session import get_db

router = APIRouter(prefix="/posts", tags=["posts"])


class PostCreate(BaseModel):
    title: str
    content: str
    excerpt: Optional[str] = None
    cover_image: Optional[str] = ""
    categories: Optional[List[str]] = []
    published: Optional[bool] = False


class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    cover_image: Optional[str] = None
    categories: Optional[List[str]] = None
    published: Optional[bool] = None


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


def _fmt(post: Post) -> dict:
    return {
        "id": post.id,
        "title": post.title,
        "slug": post.slug,
        "content": post.content,
        "excerpt": post.excerpt,
        "cover_image": post.cover_image or "",
        "categories": post.categories or [],
        "author_id": post.author_id,
        "published": post.published,
        "published_at": post.published_at.isoformat() if post.published_at else None,
        "created_at": post.created_at.isoformat() if post.created_at else None,
        "updated_at": post.updated_at.isoformat() if post.updated_at else None,
        "like_count": post.like_count or 0,
    }


@router.get("")
def list_posts(
    category: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    q = db.query(Post).filter(Post.published.is_(True)).order_by(Post.published_at.desc())
    if category:
        q = q.filter(Post.categories.any(func.lower(category)))
    total = q.count()
    posts = q.offset(offset).limit(limit).all()
    return {"posts": [_fmt(p) for p in posts], "total": total, "limit": limit, "offset": offset}


@router.get("/search")
def search_posts(
    q: str = Query(..., min_length=2, max_length=100),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    term = f"%{q.lower()}%"
    query = (
        db.query(Post)
        .filter(Post.published.is_(True))
        .filter(
            or_(
                func.lower(Post.title).like(term),
                func.lower(Post.excerpt).like(term),
                func.lower(Post.content).like(term),
            )
        )
        .order_by(Post.published_at.desc())
    )
    total = query.count()
    posts = query.offset(offset).limit(limit).all()
    return {"posts": [_fmt(p) for p in posts], "query": q, "total": total}


@router.get("/{id}")
def get_post(id: str, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == id).first()
    if not post:
        raise HTTPException(404, "Post not found")
    return {"post": _fmt(post)}


@router.post("", status_code=201)
def create_post(body: PostCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    cats = [c.strip().lower() for c in (body.categories or []) if c.strip()]
    post = Post(
        id=str(ULID()),
        title=body.title.strip(),
        slug=_slugify(body.title),
        content=body.content.strip(),
        excerpt=body.excerpt or body.content[:200],
        cover_image=body.cover_image or "",
        categories=cats,
        author_id=user["sub"],
        published=body.published,
        published_at=now if body.published else None,
        created_at=now,
        updated_at=now,
        like_count=0,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return {"post": _fmt(post)}


@router.put("/{id}")
def update_post(id: str, body: PostUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    post = db.query(Post).filter(Post.id == id).first()
    if not post:
        raise HTTPException(404, "Post not found")

    now = datetime.now(timezone.utc)
    if body.title is not None:
        post.title = body.title.strip()
        post.slug = _slugify(body.title)
    if body.content is not None:
        post.content = body.content.strip()
    if body.excerpt is not None:
        post.excerpt = body.excerpt
    if body.cover_image is not None:
        post.cover_image = body.cover_image
    if body.categories is not None:
        post.categories = [c.strip().lower() for c in body.categories if c.strip()]
    if body.published is not None and body.published and not post.published:
        post.published = True
        post.published_at = now
    post.updated_at = now

    db.commit()
    return {"message": "Post updated"}


@router.post("/{id}/like")
def like_post(id: str, db: Session = Depends(get_db)):
    result = db.execute(
        update(Post)
        .where(Post.id == id)
        .values(like_count=Post.like_count + 1)
        .returning(Post.like_count)
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(404, "Post not found")
    db.commit()
    return {"like_count": row[0]}


@router.delete("/{id}", status_code=200)
def delete_post(id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    post = db.query(Post).filter(Post.id == id).first()
    if not post:
        raise HTTPException(404, "Post not found")
    db.delete(post)
    db.commit()
    return {"message": "Post deleted"}
