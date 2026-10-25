
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi import Query
from sqlalchemy.orm import Session

from supportiq.db.session import get_db
from supportiq.models.knowledge_article import KnowledgeArticle
from supportiq.schemas.knowledge import (
    KnowledgeArticleCreate,
    KnowledgeArticleResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/knowledge/articles",
    response_model=KnowledgeArticleResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Knowledge Base"],
)
def create_knowledge_article(
    article_data: KnowledgeArticleCreate,
    db: Session = Depends(get_db),
) -> KnowledgeArticleResponse:
    article = KnowledgeArticle(
        title=article_data.title,
        content=article_data.content,
        category=article_data.category,
    )

    try:
        db.add(article)
        db.commit()
        db.refresh(article)
    except Exception:
        db.rollback()
        logger.exception("Failed to create knowledge article")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create knowledge article.",
        )

    return article


@router.get(
    "/knowledge/articles",
    response_model=list[KnowledgeArticleResponse],
    tags=["Knowledge Base"],
)
def list_knowledge_articles(
    db: Session = Depends(get_db),
) -> list[KnowledgeArticleResponse]:
    return (
        db.query(KnowledgeArticle)
        .filter(KnowledgeArticle.is_active.is_(True))
        .order_by(KnowledgeArticle.created_at.desc())
        .all()
    )


@router.get(
    "/knowledge/search",
    response_model=list[KnowledgeArticleResponse],
    tags=["Knowledge Base"],
)
@router.get(
    "/knowledge/search",
    response_model=list[KnowledgeArticleResponse],
    tags=["Knowledge Base"],
)
def search_knowledge_articles(
    q: str = Query(min_length=2, max_length=200),
    db: Session = Depends(get_db),
) -> list[KnowledgeArticleResponse]:
    search_term = f"%{q.strip()}%"

    return (
        db.query(KnowledgeArticle)
        .filter(
            KnowledgeArticle.is_active.is_(True),
            (
                KnowledgeArticle.title.ilike(search_term)
                | KnowledgeArticle.content.ilike(search_term)
            ),
        )
        .order_by(KnowledgeArticle.created_at.desc())
        .limit(10)
        .all()
    )