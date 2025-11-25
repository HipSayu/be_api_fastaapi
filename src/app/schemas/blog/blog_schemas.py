from pydantic import BaseModel, ConfigDict, Field
from typing import Annotated, Optional
from ...core.schemas import FullAuditSchema, UUIDSchema
from datetime import datetime


class BlogBase(BaseModel):
    title: Annotated[
        str,
        Field(
            min_length=2,
            max_length=255,
            examples=["Đây là bài blogs"],
        ),
    ]

    content: Annotated[
        str,
        Field(
            min_length=1,
            max_length=50000,
            examples=["Đây là nội dung bài blogs"],
        ),
    ]


class Blog(FullAuditSchema, BlogBase, UUIDSchema):
    created_by_user_id: int


class BlogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: Annotated[
        str,
        Field(
            min_length=2,
            max_length=255,
            examples=["Đây là bài blogs"],
        ),
    ]
    content: Annotated[
        str,
        Field(
            min_length=1,
            max_length=50000,
            examples=["Đây là nội dung bài blogs"],
        ),
    ]
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]
    is_deleted: bool


class BlogCreate(BlogBase):
    model_config = ConfigDict(extra="forbid")


class BlogCreateInternal(BlogCreate):
    created_by_user_id: int


class BlogUpdate(BaseModel):
    title: Annotated[
        str,
        Field(
            min_length=2,
            max_length=255,
            examples=["Đây là bài blogs"],
        ),
    ]

    content: Annotated[
        str,
        Field(
            min_length=1,
            max_length=50000,
            examples=["Đây là nội dung bài blogs"],
        ),
    ]


class BlogUpdateInternal(BlogUpdate):
    updated_at: datetime


class BlogDelete(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_deleted: bool
    deleted_at: datetime

class BlogListResponse(BaseModel):
    data: list[BlogRead]
    total: int
    page: int
    size: int
    pages: int
