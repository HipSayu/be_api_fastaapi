from ..base_services import BaseService
from ...models.blog.blog_main_model import (
    BlogMain,
    BlogCategory,
    BlogReaction,
    BlogView,
    BlogComment,
)
from ...schemas.blog.blog_main_schemas import (
    BlogMainCreate,
    BlogMainUpdate,
    BlogStatus,
)

from ...models.blog.blog_reaction_model import ReactionType

from ...core.exceptions import NotFoundError, ValidationError, PermissionError
from sqlalchemy.ext.asyncio import AsyncSession
from slugify import slugify
from datetime import datetime, UTC, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select, func, update, and_, or_, desc, asc
from sqlalchemy.orm import selectinload, joinedload


class BlogService(BaseService[BlogMain, BlogMainCreate, BlogMainUpdate]):
    def __init__(self):
        super().__init__()

    async def create_blog(
        self, db: AsyncSession, blog_in: BlogMainCreate, author_id: int
    ) -> BlogMain:
        """Create new Blog với auto-slug generation"""

        if not blog_in.slug:
            base_slug = slugify(blog_in.slug)
            slug = await self._generate_unique_slug(db, base_slug)
        else:
            slug = slugify(blog_in.slug)
            existing = await self._get_by_slug(db, slug)
            if existing:
                raise ValidationError("Slug already exists")

        if blog_in.category_id:
            category = await db.get(BlogCategory, blog_in.category_id)
            if not category or category.is_deleted:
                raise ValidationError("Invalid category")

        blog_data = blog_in.model_dump(exclude={"scheduled_publish_at"})
        blog_data.update(
            {
                "slug": slug,
                "author_id": author_id,
            }
        )

        if blog_in.status == BlogStatus.SCHEDULED and blog_in.scheduled_publish_at:
            if blog_in.scheduled_publish_at <= datetime.now(UTC):
                raise ValidationError("Scheduled publish time must be in the future")

        if blog_in.status == BlogStatus.PUBLISHED:
            blog_data["published_at"] = datetime.now(UTC)

        blog = BlogMain(**blog_data)
        db.add(blog)
        await db.commit()
        await db.refresh(blog)
        return blog

    async def update_blog(
        self,
        db: AsyncSession,
        blog_id: int,
        blog_update: BlogMainUpdate,
        user_id: int,
    ) -> BlogMain:
        """Update blog với permission check"""

        blog = await self.get(db, blog_id, load_relationships=True)
        if not blog:
            raise NotFoundError("Blog not found")
        if blog.create_by_user_id != user_id:
            raise PermissionError("You can only edit your own blogs")

        update_data = blog_update.model_dump(exclude_unset=True)

        if "status" in update_data:
            if update_data["status"] == BlogStatus.PUBLISHED and not blog.published_at:
                update_data["published_at"] = datetime.now(UTC)
            elif update_data["status"] != BlogStatus.PUBLISHED:
                update_data["published_at"] = None

        for field, value in update_data.items():
            setattr(blog, field, value)

        blog.updated_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(blog)
        return blog

    async def get_published_blogs(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        # category_id: Optional[int] = None,
        search: Optional[str] = None,
        tags: Optional[List[str]] = None,
        sort_by: str = "created_at",  # created_at, published_at, view_count, title
        sort_order: str = "desc",
    ) -> Tuple[List[BlogMain], int]:
        """Get published blogs với filtering và sorting"""

        query = (
            select(BlogMain)
            .options(
                selectinload(BlogMain.create_by_user_id),
                selectinload(BlogMain.category),
            )
            .where(
                and_(
                    BlogMain.status == BlogStatus.PUBLISHED,
                    BlogMain.is_deleted == False,
                )
            )
        )

        if search:
            search_filter = or_(
                BlogMain.title.ilike(f"%{search}%"),
                BlogMain.content.ilike(f"%{search}%"),
                BlogMain.meta_description.ilike(f"%{search}%"),
            )
            query = query.where(search_filter)

        if tags:
            query = query.where(BlogMain.tags.overlap(tags))
        sort_column = getattr(BlogMain, sort_by, BlogMain.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        blogs_query = query.offset(skip).limit(limit)
        result = await db.execute(blogs_query)
        blogs = result.scalars().all()

        return blogs, total

    async def get_blog_with_stats(
        self, db: AsyncSession, blog_id: int, user_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Get Blog với reaction counts và user's reaction"""
        blog = await self.get(db, blog_id, load_relationships=True)
        if not blog:
            return None

        reaction_counts_query = (
            select(
                ReactionType.name,
                ReactionType.emoji,
                func.count(BlogReaction.id).label("count"),
            )
            .select_from(
                ReactionType.outerjoin(
                    BlogReaction,
                    and_(
                        BlogReaction.reaction_type_id == ReactionType.id,
                        BlogReaction.blog_id == blog_id,
                    ),
                )
            )
            .where(ReactionType.is_active == True)
            .group_by(ReactionType.id, ReactionType.name, ReactionType.emoji)
            .order_by(ReactionType.sort_order)
        )
        result = await db.execute(reaction_counts_query)
        reaction_data = result.all()

        reaction_counts = [
            {
                "reaction_type": row.name,
                "emoji": row.emoji,
                "count": row.count,
            }
            for row in reaction_data
        ]

        total_reactions = sum(r["count"] for r in reaction_counts)

        user_reaction = None

        if user_id:
            user_reaction_query = (
                select(ReactionType.name)
                .select_from(BlogReaction.join(ReactionType))
                .where(
                    and_(
                        BlogReaction.blog_id == blog_id, BlogReaction.user_id == user_id
                    )
                )
            )
            result = await db.execute(user_reaction_query)
            user_reaction = result.scalar_one_or_none()

        comment_count_query = select(func.count(BlogComment.id)).where(
            and_(BlogComment.blog_id == blog_id, BlogComment.is_deleted == False)
        )

        result = await db.execute(comment_count_query)

        comment_count = result.scalar()

        return {
            "blog": blog,
            "reaction_counts": reaction_counts,
            "total_reactions": total_reactions,
            "user_reaction": user_reaction,
            "comment_count": comment_count,
        }

    async def increment_view_count(
        self,
        db: AsyncSession,
        blog_id: int,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        """Track blog view và increment coutner"""

        should_count = await self._should_count_view(
            db, blog_id, user_id, ip_address, session_id
        )

        if should_count:
            blog_view = BlogView(
                blog_id=blog_id,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
            )
            db.add(blog_view)

            await db.execute(
                update(BlogMain)
                .where(BlogMain.id == blog_id)
                .values(view_count=BlogMain.view_count + 1)
            )

            await db.commit()

    async def _generate_unique_slug(self, db: AsyncSession, base_slug: str) -> str:
        """Generate unique slug"""
        slug = base_slug
        counter = 1

        while await self._get_by_slug(db, slug):
            slug = f"{base_slug}-{counter}"
            counter += 1

        return slug

    async def _should_count_view(
        self,
        db: AsyncSession,
        blog_id: int,
        user_id: Optional[int],
        ip_address: Optional[str],
        session_id: Optional[str],
    ) -> bool:
        """Determine if view should be counted (anti-spam)"""

        time_threshold = datetime.now(UTC) - timedelta(hours=1)

        filters = [BlogView.blog_id == blog_id, BlogView.viewed_at > time_threshold]

        if user_id:
            filter.append(BlogView.user_id == user_id)
        elif ip_address and session_id:
            filters.append(
                and_(
                    BlogView.ip_address == ip_address, BlogView.session_id == session_id
                )
            )
        else:
            return False

        query = select(func.count(BlogView.id)).where(and_(*filters))
        result = await db.execute(query)
        existing_views = result.scalar()

        return existing_views == 0


blog_service = BlogService()
