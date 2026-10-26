
def test_create_knowledge_article(client):
    response = client.post(
        "/api/v1/knowledge/articles",
        json={
            "title": "Password Reset Help",
            "content": "Check your spam folder if the reset email does not arrive.",
            "category": "account",
        },
    )

    assert response.status_code == 201

    data = response.json()
    assert data["title"] == "Password Reset Help"
    assert data["content"] == (
        "Check your spam folder if the reset email does not arrive."
    )
    assert data["category"] == "account"
    assert "id" in data
    assert "created_at" in data


def test_list_knowledge_articles(client):
    client.post(
        "/api/v1/knowledge/articles",
        json={
            "title": "Password Reset Help",
            "content": "Check your spam folder for the reset email.",
            "category": "account",
        },
    )

    response = client.get("/api/v1/knowledge/articles")

    assert response.status_code == 200

    articles = response.json()
    assert isinstance(articles, list)
    assert len(articles) == 1
    assert articles[0]["title"] == "Password Reset Help"


def test_search_knowledge_articles(client):
    client.post(
        "/api/v1/knowledge/articles",
        json={
            "title": "Password Reset Help",
            "content": "Check your spam folder for the reset email.",
            "category": "account",
        },
    )

    client.post(
        "/api/v1/knowledge/articles",
        json={
            "title": "Payment Troubleshooting",
            "content": "Verify your payment method if a transaction fails.",
            "category": "billing",
        },
    )

    response = client.get("/api/v1/knowledge/search?q=Password")

    assert response.status_code == 200

    articles = response.json()
    assert len(articles) == 1
    assert articles[0]["title"] == "Password Reset Help"


def test_search_knowledge_articles_rejects_short_query(client):
    response = client.get("/api/v1/knowledge/search?q=a")

    assert response.status_code == 422



def test_search_knowledge_articles_excludes_inactive_articles(client, db):
    from supportiq.models.knowledge_article import KnowledgeArticle

    create_response = client.post(
        "/api/v1/knowledge/articles",
        json={
            "title": "Inactive Password Guide",
            "content": "Instructions for resetting a password.",
            "category": "account",
        },
    )

    assert create_response.status_code == 201
    article_id = create_response.json()["id"]

    article = db.get(KnowledgeArticle, article_id)
    assert article is not None

    article.is_active = False
    db.commit()

    response = client.get("/api/v1/knowledge/search?q=Password")

    assert response.status_code == 200
    assert all(
        item["id"] != article_id
        for item in response.json()
    )


def test_list_knowledge_articles_excludes_inactive_articles(client, db):
    from supportiq.models.knowledge_article import KnowledgeArticle

    create_response = client.post(
        "/api/v1/knowledge/articles",
        json={
            "title": "Inactive Billing Guide",
            "content": "Instructions for resolving a billing issue.",
            "category": "billing",
        },
    )

    assert create_response.status_code == 201
    article_id = create_response.json()["id"]

    article = db.get(KnowledgeArticle, article_id)
    assert article is not None

    article.is_active = False
    db.commit()

    response = client.get("/api/v1/knowledge/articles")

    assert response.status_code == 200
    assert all(
        item["id"] != article_id
        for item in response.json()
    )
