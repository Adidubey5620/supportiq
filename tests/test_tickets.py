from unittest.mock import AsyncMock, patch
from supportiq.models.knowledge_article import KnowledgeArticle

def test_create_ticket(client):
    response = client.post(
        "/api/v1/tickets",
        json={
            "customer_name": "Test Customer",
            "message": "I cannot log in to my account.",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["customer_name"] == "Test Customer"
    assert data["message"] == "I cannot log in to my account."
    assert data["status"] == "open"
    assert "id" in data
    assert "created_at" in data


def test_list_tickets_with_pagination(client):
    client.post(
        "/api/v1/tickets",
        json={
            "customer_name": "Customer One",
            "message": "First ticket.",
        },
    )
    client.post(
        "/api/v1/tickets",
        json={
            "customer_name": "Customer Two",
            "message": "Second ticket.",
        },
    )

    response = client.get("/api/v1/tickets?skip=0&limit=2")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 2


def test_filter_tickets_by_status(client):
    client.post(
        "/api/v1/tickets",
        json={
            "customer_name": "Open Customer",
            "message": "An open ticket.",
        },
    )

    response = client.get("/api/v1/tickets?status=open")

    assert response.status_code == 200
    tickets = response.json()
    assert isinstance(tickets, list)
    assert len(tickets) == 1
    assert all(ticket["status"] == "open" for ticket in tickets)


def test_update_ticket_status(client):
    create_response = client.post(
        "/api/v1/tickets",
        json={
            "customer_name": "Status Test Customer",
            "message": "Testing ticket status updates.",
        },
    )

    assert create_response.status_code == 201
    ticket_id = create_response.json()["id"]

    update_response = client.patch(
        f"/api/v1/tickets/{ticket_id}",
        json={"status": "in_progress"},
    )

    assert update_response.status_code == 200
    assert update_response.json()["status"] == "in_progress"


def test_delete_ticket(client):
    create_response = client.post(
        "/api/v1/tickets",
        json={
            "customer_name": "Delete Test Customer",
            "message": "This ticket will be deleted.",
        },
    )

    assert create_response.status_code == 201
    ticket_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/api/v1/tickets/{ticket_id}"
    )

    assert delete_response.status_code == 204

    get_response = client.get(
        f"/api/v1/tickets/{ticket_id}"
    )

    assert get_response.status_code == 404



def test_search_tickets(client):
    client.post(
        "/api/v1/tickets",
        json={
            "customer_name": "Rahul Sharma",
            "message": "I cannot log in to my account.",
        },
    )
    client.post(
        "/api/v1/tickets",
        json={
            "customer_name": "Priya Patel",
            "message": "My payment failed.",
        },
    )

    response = client.get("/api/v1/tickets/search?q=Rahul")

    assert response.status_code == 200
    tickets = response.json()
    assert len(tickets) == 1
    assert tickets[0]["customer_name"] == "Rahul Sharma"



def test_count_tickets(client):
    client.post(
        "/api/v1/tickets",
        json={
            "customer_name": "Open Customer",
            "message": "This ticket remains open.",
        },
    )

    create_response = client.post(
        "/api/v1/tickets",
        json={
            "customer_name": "In Progress Customer",
            "message": "This ticket is being handled.",
        },
    )
    ticket_id = create_response.json()["id"]

    update_response = client.patch(
        f"/api/v1/tickets/{ticket_id}",
        json={"status": "in_progress"},
    )
    assert update_response.status_code == 200

    response = client.get("/api/v1/tickets/count")

    assert response.status_code == 200
    assert response.json() == {
        "total": 2,
        "open": 1,
        "in_progress": 1,
        "resolved": 0,
    }


def test_get_nonexistent_ticket(client):
    response = client.get("/api/v1/tickets/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Ticket not found"


def test_update_ticket_with_invalid_status(client):
    create_response = client.post(
        "/api/v1/tickets",
        json={
            "customer_name": "Validation Test Customer",
            "message": "Testing invalid ticket status.",
        },
    )

    assert create_response.status_code == 201
    ticket_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/tickets/{ticket_id}",
        json={"status": "invalid_status"},
    )

    assert response.status_code == 422


def test_generate_reply_for_nonexistent_ticket(client):
    response = client.post(
        "/api/v1/tickets/99999/generate-reply"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Ticket not found."


from unittest.mock import AsyncMock, patch


def test_generate_reply_for_existing_ticket(client):
    create_response = client.post(
        "/api/v1/tickets",
        json={
            "customer_name": "AI Test Customer",
            "message": "I never received my password reset email.",
        },
    )

    assert create_response.status_code == 201
    ticket_id = create_response.json()["id"]


    article = KnowledgeArticle(
        title="Password Reset Email Not Received",
        content="Ask the customer to check their spam folder.",
        category="account",
        is_active=True,
    )

    with (
        patch(
            "supportiq.api.v1.endpoints.tickets.retrieve_knowledge",
            return_value=[article],
        ),
        patch(
            "supportiq.api.v1.endpoints.tickets.generate_support_reply",
            new_callable=AsyncMock,
        ) as mock_generate,
    ):
        mock_generate.return_value = (
            "Please check your spam folder. "
            "If the email is still missing, contact support."
        )

        response = client.post(
            f"/api/v1/tickets/{ticket_id}/generate-reply"
        )

    assert response.status_code == 200
    data = response.json()
    assert data["ticket_id"] == ticket_id
    assert "check your spam folder" in data["draft_reply"]
    assert data["requires_human_review"] is True
    mock_generate.assert_awaited_once()



def test_generate_reply_handles_ai_provider_failure(client):
    create_response = client.post(
        "/api/v1/tickets",
        json={
            "customer_name": "AI Failure Test",
            "message": "I cannot reset my password.",
        },
    )

    assert create_response.status_code == 201
    ticket_id = create_response.json()["id"]

    from supportiq.models.knowledge_article import KnowledgeArticle

    article = KnowledgeArticle(
    title="Password Reset Guide",
    content="Help customers reset their account password.",
    category="account",
    is_active=True,
    )

    with (
        patch(
            "supportiq.api.v1.endpoints.tickets.retrieve_knowledge",
            return_value=[article],
        ),
        patch(
            "supportiq.api.v1.endpoints.tickets.generate_support_reply",
            new_callable=AsyncMock,
        ) as mock_generate,
    ):
        mock_generate.side_effect = RuntimeError(
            "Simulated AI provider failure"
        )

        response = client.post(
            f"/api/v1/tickets/{ticket_id}/generate-reply"
        )

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "Unable to generate an AI reply. Please try again."
    )
    mock_generate.assert_awaited_once()


def test_generate_reply_passes_retrieved_knowledge_to_ai(client, db):
    from supportiq.models.knowledge_article import KnowledgeArticle

    create_response = client.post(
        "/api/v1/tickets",
        json={
            "customer_name": "Knowledge Context Test",
            "message": "I never received my password reset email.",
        },
    )

    assert create_response.status_code == 201
    ticket_id = create_response.json()["id"]

    article = KnowledgeArticle(
        title="Password Reset Email",
        content="Ask the customer to check their spam folder.",
        category="account",
        is_active=True,
    )
    db.add(article)
    db.commit()

    with patch(
        "supportiq.api.v1.endpoints.tickets.generate_support_reply",
        new_callable=AsyncMock,
    ) as mock_generate:
        mock_generate.return_value = "Please check your spam folder."

        response = client.post(
            f"/api/v1/tickets/{ticket_id}/generate-reply"
        )

    assert response.status_code == 200

    mock_generate.assert_awaited_once()
    call_kwargs = mock_generate.await_args.kwargs

    assert call_kwargs["customer_message"] == (
        "I never received my password reset email."
    )
    assert "Password Reset Email" in call_kwargs["knowledge_context"]
    assert "check their spam folder" in call_kwargs["knowledge_context"]



def test_generate_reply_without_relevant_knowledge_skips_ai(client):
    from unittest.mock import AsyncMock, patch

    create_response = client.post(
        "/api/v1/tickets",
        json={
            "customer_name": "Unknown Issue Test",
            "message": "My quantum teleportation device is malfunctioning.",
        },
    )

    assert create_response.status_code == 201
    ticket_id = create_response.json()["id"]

    with patch(
        "supportiq.api.v1.endpoints.tickets.retrieve_knowledge",
        return_value=[],
    ), patch(
        "supportiq.api.v1.endpoints.tickets.generate_support_reply",
        new_callable=AsyncMock,
    ) as mock_generate:
        response = client.post(
            f"/api/v1/tickets/{ticket_id}/generate-reply"
        )

    assert response.status_code == 200
    assert response.json()["requires_human_review"] is True
    assert "human support" in response.json()["draft_reply"].lower()
    mock_generate.assert_not_awaited()

