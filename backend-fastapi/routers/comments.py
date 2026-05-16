from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ulid import ULID

from core.auth import get_current_user
from db.models import Comment, Post
from db.session import get_db

router = APIRouter(prefix="/posts", tags=["comments"])


class CommentCreate(BaseModel):
    author_name: str
    content: str


def _fmt(c: Comment) -> dict:
    return {
        "id": c.id,
        "author_name": c.author_name,
        "content": c.content,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


@router.get("/{id}/comments")
def list_comments(id: str, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == id).first()
    if not post:
        raise HTTPException(404, "Post not found")
    comments = (
        db.query(Comment)
        .filter(Comment.post_id == id)
        .order_by(Comment.created_at.asc())
        .all()
    )
    return {"comments": [_fmt(c) for c in comments]}


@router.post("/{id}/comments", status_code=201)
def create_comment(id: str, body: CommentCreate, db: Session = Depends(get_db)):
    if not body.author_name.strip() or not body.content.strip():
        raise HTTPException(400, "author_name and content are required")
    if len(body.content) > 2000:
        raise HTTPException(400, "Comment too long (max 2000 characters)")

    post = db.query(Post).filter(Post.id == id).first()
    if not post:
        raise HTTPException(404, "Post not found")

    comment = Comment(
        id=str(ULID()),
        post_id=id,
        author_name=body.author_name.strip(),
        content=body.content.strip(),
        created_at=datetime.now(timezone.utc),
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return _fmt(comment)


@router.delete("/{id}/comments/{comment_id}")
def delete_comment(
    id: str,
    comment_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    comment = db.query(Comment).filter(Comment.id == comment_id, Comment.post_id == id).first()
    if not comment:
        raise HTTPException(404, "Comment not found")
    db.delete(comment)
    db.commit()
    return {"message": "Comment deleted"}
