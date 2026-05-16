from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


def _now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False, default="admin")
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_now)

    posts = relationship("Post", back_populates="author")


class Post(Base):
    __tablename__ = "posts"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    slug = Column(String, nullable=False, index=True)
    content = Column(Text, nullable=False)
    excerpt = Column(Text)
    cover_image = Column(String, default="")
    categories = Column(ARRAY(String), default=list)
    author_id = Column(String, ForeignKey("users.id"), nullable=False)
    published = Column(Boolean, default=False)
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)
    like_count = Column(Integer, default=0)

    author = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(String, primary_key=True)
    post_id = Column(String, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    author_name = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_now)

    post = relationship("Post", back_populates="comments")
