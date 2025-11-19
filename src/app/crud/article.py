from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.article import Article
from ..models.category import Category
from ..models.user import User
from ..schemas.article import ArticleCreate, ArticleUpdate


class ArticleCRUD:
    """CRUD operations for Article model"""
    
    async def create(
        self, 
        db: AsyncSession, 
        *, 
        obj_in: ArticleCreate, 
        author_id: int
    ) -> Article:
        """Create new article"""
        article = Article(
            title=obj_in.title,
            content=obj_in.content,
            summary=obj_in.summary,
            category_id=obj_in.category_id,
            author_id=author_id,
            is_published=obj_in.is_published,
            is_active=obj_in.is_active
        )
        db.add(article)
        await db.commit()
        await db.refresh(article)
        return article
    
    async def get(self, db: AsyncSession, *, id: int) -> Optional[Article]:
        """Get article by ID"""
        stmt = select(Article).where(Article.id == id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_with_relations(self, db: AsyncSession, *, id: int) -> Optional[Article]:
        """Get article by ID with relationships loaded"""
        stmt = (
            select(Article)
            .options(
                selectinload(Article.category),
                selectinload(Article.author)
            )
            .where(Article.id == id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_multi(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        category_id: Optional[int] = None,
        author_id: Optional[int] = None,
        is_published: Optional[bool] = None,
        is_active: Optional[bool] = None
    ) -> tuple[list[Article], int]:
        """Get multiple articles with pagination and filters"""
        # Build base query
        stmt = select(Article)
        count_stmt = select(func.count(Article.id))
        
        # Add filters
        if category_id is not None:
            stmt = stmt.where(Article.category_id == category_id)
            count_stmt = count_stmt.where(Article.category_id == category_id)
        
        if author_id is not None:
            stmt = stmt.where(Article.author_id == author_id)
            count_stmt = count_stmt.where(Article.author_id == author_id)
            
        if is_published is not None:
            stmt = stmt.where(Article.is_published == is_published)
            count_stmt = count_stmt.where(Article.is_published == is_published)
            
        if is_active is not None:
            stmt = stmt.where(Article.is_active == is_active)
            count_stmt = count_stmt.where(Article.is_active == is_active)
        
        # Add pagination
        stmt = stmt.offset(skip).limit(limit).order_by(Article.created_at.desc())
        
        # Execute queries
        result = await db.execute(stmt)
        count_result = await db.execute(count_stmt)
        
        articles = result.scalars().all()
        total = count_result.scalar()
        
        return articles, total
    
    async def get_multi_with_relations(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        category_id: Optional[int] = None,
        author_id: Optional[int] = None,
        is_published: Optional[bool] = None,
        is_active: Optional[bool] = None
    ) -> tuple[list[Article], int]:
        """Get multiple articles with relationships loaded"""
        # Build base query
        stmt = (
            select(Article)
            .options(
                selectinload(Article.category),
                selectinload(Article.author)
            )
        )
        count_stmt = select(func.count(Article.id))
        
        # Add filters
        if category_id is not None:
            stmt = stmt.where(Article.category_id == category_id)
            count_stmt = count_stmt.where(Article.category_id == category_id)
        
        if author_id is not None:
            stmt = stmt.where(Article.author_id == author_id)
            count_stmt = count_stmt.where(Article.author_id == author_id)
            
        if is_published is not None:
            stmt = stmt.where(Article.is_published == is_published)
            count_stmt = count_stmt.where(Article.is_published == is_published)
            
        if is_active is not None:
            stmt = stmt.where(Article.is_active == is_active)
            count_stmt = count_stmt.where(Article.is_active == is_active)
        
        # Add pagination
        stmt = stmt.offset(skip).limit(limit).order_by(Article.created_at.desc())
        
        # Execute queries
        result = await db.execute(stmt)
        count_result = await db.execute(count_stmt)
        
        articles = result.scalars().all()
        total = count_result.scalar()
        
        return articles, total
    
    async def update(
        self, 
        db: AsyncSession, 
        *, 
        db_obj: Article, 
        obj_in: ArticleUpdate
    ) -> Article:
        """Update article"""
        update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db_obj.updated_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def delete(self, db: AsyncSession, *, id: int) -> bool:
        """Delete article"""
        stmt = select(Article).where(Article.id == id)
        result = await db.execute(stmt)
        article = result.scalar_one_or_none()
        
        if article:
            await db.delete(article)
            await db.commit()
            return True
        return False
    
    async def verify_category_exists(self, db: AsyncSession, *, category_id: int) -> bool:
        """Verify if category exists and is active"""
        stmt = select(Category).where(
            Category.id == category_id,
            Category.is_active == True
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none() is not None
    
    async def verify_author_exists(self, db: AsyncSession, *, author_id: int) -> bool:
        """Verify if author exists"""
        stmt = select(User).where(User.id == author_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none() is not None


# Create instance
article_crud = ArticleCRUD()