
import re

from sqlalchemy.orm import Session

from supportiq.models.knowledge_article import KnowledgeArticle


STOP_WORDS = {
    "that", "this", "with", "have", "from",
    "your", "what", "when", "where", "cannot",
    "could", "would", "please", "because",
    "they", "them", "then", "there", "here",
    "into", "about", "been", "being", "does",
    "just", "need", "help", "will", "want",
}


def retrieve_knowledge(
    customer_message: str,
    db: Session,
    limit: int = 5,
) -> list[KnowledgeArticle]:
    """Retrieve and rank active articles by keyword relevance."""

    if limit <= 0:
        return []

    words = re.findall(r"\b[a-zA-Z0-9]+\b", customer_message.lower())

    keywords = {
        word
        for word in words
        if len(word) >= 4 and word not in STOP_WORDS
    }

    if not keywords:
        return []

    articles = (
        db.query(KnowledgeArticle)
        .filter(KnowledgeArticle.is_active.is_(True))
        .all()
    )

    scored_articles: list[tuple[int, KnowledgeArticle]] = []

    for article in articles:
        title = article.title.lower()
        content = article.content.lower()

        score = 0

        for keyword in keywords:
            if re.search(rf"\b{re.escape(keyword)}\b", title):
                score += 3

            if re.search(rf"\b{re.escape(keyword)}\b", content):
                score += 1

        if score > 0:
            scored_articles.append((score, article))

    scored_articles.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return [
        article
        for score, article in scored_articles[:limit]
    ]




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
