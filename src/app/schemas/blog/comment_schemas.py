from pydantic import BaseModel, ConfigDict, Field
from typing import Annotated, List, Optional
from datetime import datetime
from .blog_status_schemas import ReactionCount


class CommentBase(BaseModel):
    content: Annotated[
        str,
        Field(
            min_length=1,
            max_length=5000,
        ),
    ]


class CommentCreate(CommentBase):
    model_config = ConfigDict(extra="forbid")
    parent_id: Optional[int] = None


class CommentUpdate(BaseModel):
    content: Annotated[
        str,
        Field(
            min_length=1,
            max_length=5000,
        ),
    ]


class CommentUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None


class CommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    content: str
    is_edited: bool
    edited_at: Optional[datetime]
    created_at: datetime
    parent_id: Optional[int]
    user: CommentUser


class CommentWithReplies(CommentRead):
    """Comment với nested replies"""

    replies: List["CommentWithReplies"] = []
    reaction_counts = List[ReactionCount] = []
    total_reactions: int = 0
    user_reaction: Optional[str] = None

class CommentTree(BaseModel):
    """Hierarchical comment structure"""
    comments: List[CommentWithReplies]
    total_count: int

