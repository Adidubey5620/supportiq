
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from supportiq.models.base import Base
from supportiq.models.knowledge_article import KnowledgeArticle
from supportiq.services.retrieval import retrieve_knowledge


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        yield session

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_retrieve_article_by_keyword(db: Session):
    article = KnowledgeArticle(
        title="Password Reset Email Not Received",
        content="Check the registered email address and spam folder.",
        category="account",
        is_active=True,
    )
    db.add(article)
    db.commit()

    results = retrieve_knowledge(
        customer_message="My password reset email never arrived",
        db=db,
    )

    assert len(results) == 1
    assert results[0].title == "Password Reset Email Not Received"


def test_ignore_inactive_articles(db: Session):
    article = KnowledgeArticle(
        title="Password Reset Email Not Received",
        content="Check the registered email address and spam folder.",
        category="account",
        is_active=False,
    )
    db.add(article)
    db.commit()

    results = retrieve_knowledge(
        customer_message="My password reset email never arrived",
        db=db,
    )

    assert results == []


def test_return_empty_list_when_no_article_matches(db: Session):
    article = KnowledgeArticle(
        title="Update Billing Address",
        content="Customers can update their billing address in settings.",
        category="billing",
        is_active=True,
    )
    db.add(article)
    db.commit()

    results = retrieve_knowledge(
        customer_message="My password reset email never arrived",
        db=db,
    )

    assert results == []


def test_respect_result_limit(db: Session):
    for number in range(3):
        db.add(
            KnowledgeArticle(
                title=f"Password Help {number}",
                content="Password reset assistance and account access.",
                category="account",
                is_active=True,
            )
        )
    db.commit()

    results = retrieve_knowledge(
        customer_message="I need password reset help",
        db=db,
        limit=2,
    )

    assert len(results) <= 2


def test_retrieve_knowledge_ranks_better_title_matches_first(
    db: Session,
):
    weaker_article = KnowledgeArticle(
        title="General Account Help",
        content="General account help for email problems.",
        category="account",
        is_active=True,
    )

    stronger_article = KnowledgeArticle(
        title="Password Reset Email Troubleshooting",
        content="Check the spam folder if the reset email is missing.",
        category="account",
        is_active=True,
    )

    db.add_all([weaker_article, stronger_article])
    db.commit()

    results = retrieve_knowledge(
        customer_message="My password reset email never arrived",
        db=db,
    )

    assert len(results) == 2
    assert results[0].title == "Password Reset Email Troubleshooting"
    assert results[1].title == "General Account Help"