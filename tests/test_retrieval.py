from supportiq.db.session import get_db
from supportiq.models.knowledge_article import KnowledgeArticle
from supportiq.services.retrieval import retrieve_knowledge


def test_retrieve_matching_knowledge_article(client):
    db = next(client.app.dependency_overrides[get_db]())

    article = KnowledgeArticle(
        title="Password Reset Email Not Received",
        content=(
            "Ask the customer to check their spam folder "
            "if the password reset email is missing."
        ),
        category="account",
        is_active=True,
    )

    db.add(article)
    db.commit()

    results = retrieve_knowledge(
        customer_message="I never received my password reset email",
        db=db,
    )

    assert len(results) == 1
    assert results[0].title == "Password Reset Email Not Received"

    db.close()


def test_retrieve_excludes_inactive_articles(client):
    db = next(client.app.dependency_overrides[get_db]())

    article = KnowledgeArticle(
        title="Password Reset Email Not Received",
        content="Check the spam folder for the reset email.",
        category="account",
        is_active=False,
    )

    db.add(article)
    db.commit()

    results = retrieve_knowledge(
        customer_message="I never received my password reset email",
        db=db,
    )

    assert results == []

    db.close()


def test_retrieve_knowledge_ranks_better_title_matches_first(client):
    db = next(client.app.dependency_overrides[get_db]())

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

    db.close()
