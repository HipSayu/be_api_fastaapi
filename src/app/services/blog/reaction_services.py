from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, delete
from sqlalchemy.orm import selectinload

from ...models.blog.blog_main_model import BlogReaction
from ...models.blog.comment_reaction_model import CommentReaction
from ...models.blog.reaction_type_model import ReactionType
from ...schemas.blog.reaction_schema import BlogReactionCreate, CommentReactionCreate
from ...core.exceptions import NotNotFoundError, ValidationError  # Chua viet ham nay
from datetime import datetime, UTC


class ReactionService:

    async def toggle_blog_reaction(
        self,
        db: AsyncSession,
        blog_id: int,
        user_id: int,
        reaction_create: BlogReactionCreate,
    ) -> Dict[str, Any]:
        """Toggle reaction on blog(add/remove/change)"""
        reaction_type = await self._get_reaction_type_by_name(
            db,
            reaction_create.reaction_type_name,
        )
        if not reaction_type:
            raise ValidationError("Invalid reaction type")
        # Check existing reaction
        existing_reaction = await self._get_user_blog_reaction(db, blog_id, user_id)

        if existing_reaction:
            if existing_reaction.reaction_type_id == reaction_type.id:
                # Same reaction - remove it
                await db.delete(existing_reaction)
                action = "removed"
            else:
                # Different reaction - update it
                existing_reaction.reaction_type_id = reaction_type.id
                existing_reaction.updated_at = datetime.now(UTC)
                action = "changed"
        else:
            # New reaction - create it
            new_reaction = BlogReaction(
                blog_id=blog_id, user_id=user_id, reaction_type_id=reaction_type.id
            )
            db.add(new_reaction)
            action = "added"

        await db.commit()

        # Get updated reaction counts
        reaction_summary = await self.get_blog_reaction_summary(db, blog_id, user_id)

        return {
            "action": action,
            "reaction_type": reaction_type.name,
            "summary": reaction_summary,
        }

    async def toggle_comment_reaction(
        self,
        db: AsyncSession,
        comment_id: int,
        user_id: int,
        reaction_create: CommentReactionCreate,
    ) -> Dict[str, Any]:
        """Toggle reaction on comment"""

        reaction_type = await self._get_reaction_type_by_name(
            db, reaction_create.reaction_type_name
        )
        if not reaction_type:
            raise ValidationError("Invalid reaction type")

        existing_reaction = await self._get_user_comment_reaction(
            db, comment_id, user_id
        )

        if existing_reaction:
            if existing_reaction.reaction_type_id == reaction_type.id:
                await db.delete(existing_reaction)
                action = "removed"
            else:
                existing_reaction.reaction_type_id = reaction_type.id
                existing_reaction.updated_at = datetime.now(UTC)
                action = "changed"
        else:
            new_reaction = CommentReaction(
                comment_id=comment_id,
                user_id=user_id,
                reaction_type_id=reaction_type.id,
            )
            db.add(new_reaction)
            action = "added"

        await db.commit()

        reaction_summary = await self.get_comment_reaction_summary(
            db, comment_id, user_id
        )

        return {
            "action": action,
            "reaction_type": reaction_type.name,
            "summary": reaction_summary,
        }

    async def get_blog_reaction_summary(
        self, db: AsyncSession, blog_id: int, user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get reaction summary for blog"""

        # Get reaction counts
        query = (
            select(
                ReactionType.name,
                ReactionType.emoji,
                ReactionType.display_name,
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
            .group_by(ReactionType.id)
            .order_by(ReactionType.sort_order)
        )

        result = await db.execute(query)
        reaction_data = result.all()

        reactions = [
            {
                "reaction_type": row.name,
                "emoji": row.emoji,
                "display_name": row.display_name,
                "count": row.count,
            }
            for row in reaction_data
            if row.count > 0
        ]

        total_count = sum(r["count"] for r in reactions)

        # Get user's reaction
        user_reaction = None
        if user_id:
            user_reaction_result = await self._get_user_blog_reaction(
                db, blog_id, user_id
            )
            if user_reaction_result:
                user_reaction = user_reaction_result.reaction_type.name

        return {
            "total_count": total_count,
            "reactions": reactions,
            "user_reaction": user_reaction,
        }

    async def get_comment_reaction_summary(
        self, db: AsyncSession, comment_id: int, user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get reaction summary for comment"""

        query = (
            select(
                ReactionType.name,
                ReactionType.emoji,
                ReactionType.display_name,
                func.count(CommentReaction.id).label("count"),
            )
            .select_from(
                ReactionType.outerjoin(
                    CommentReaction,
                    and_(
                        CommentReaction.reaction_type_id == ReactionType.id,
                        CommentReaction.comment_id == comment_id,
                    ),
                )
            )
            .where(ReactionType.is_active == True)
            .group_by(ReactionType.id)
            .order_by(ReactionType.sort_order)
        )

        result = await db.execute(query)
        reaction_data = result.all()

        reactions = [
            {
                "reaction_type": row.name,
                "emoji": row.emoji,
                "display_name": row.display_name,
                "count": row.count,
            }
            for row in reaction_data
            if row.count > 0
        ]

        total_count = sum(r["count"] for r in reactions)

        user_reaction = None
        if user_id:
            user_reaction_result = await self._get_user_comment_reaction(
                db, comment_id, user_id
            )
            if user_reaction_result:
                user_reaction = user_reaction_result.reaction_type.name

        return {
            "total_count": total_count,
            "reactions": reactions,
            "user_reaction": user_reaction,
        }

    async def get_available_reaction_types(
        self, db: AsyncSession
    ) -> List[ReactionType]:
        """Get all available reaction types"""
        query = (
            select(ReactionType)
            .where(ReactionType.is_active == True)
            .order_by(ReactionType.sort_order)
        )

        result = await db.execute(query)
        return result.scalars().all()

    # Helper methods
    async def _get_reaction_type_by_name(
        self, db: AsyncSession, name: str
    ) -> Optional[ReactionType]:
        query = select(ReactionType).where(
            and_(ReactionType.name == name, ReactionType.is_active == True)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def _get_user_blog_reaction(
        self, db: AsyncSession, blog_id: int, user_id: int
    ) -> Optional[BlogReaction]:
        query = (
            select(BlogReaction)
            .options(selectinload(BlogReaction.reaction_type))
            .where(
                and_(BlogReaction.blog_id == blog_id, BlogReaction.user_id == user_id)
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def _get_user_comment_reaction(
        self, db: AsyncSession, comment_id: int, user_id: int
    ) -> Optional[CommentReaction]:
        query = (
            select(CommentReaction)
            .options(selectinload(CommentReaction.reaction_type))
            .where(
                and_(
                    CommentReaction.comment_id == comment_id,
                    CommentReaction.user_id == user_id,
                )
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
