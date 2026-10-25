
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
