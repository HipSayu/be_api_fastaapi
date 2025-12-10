from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional
from .blog_status_schemas import ReactionCount
class ReactionTypeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    emoji: str
    display_name: str
    sort_order: int

class BlogReactionCreate(BaseModel):
    reaction_type_name: str 

class BlogReactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    reaction_type: ReactionTypeRead
    created_at: datetime

class CommentReactionCreate(BaseModel):
    reaction_type_name: str

class ReactionSummary(BaseModel):
    """Summary of reactions for a blog/comment"""
    total_count: int
    reactions: List[ReactionCount]
    user_reaction: Optional[str] = None