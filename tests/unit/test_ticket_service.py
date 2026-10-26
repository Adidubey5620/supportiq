from supportiq.models.ticket import Ticket
from supportiq.schemas.ticket import TicketCreate
from supportiq.services.ticket_service import create_ticket, list_tickets
from unittest.mock import patch
from datetime import datetime, timezone
from supportiq.services.ticket_service import (
    count_tickets,
    create_ticket,
    list_tickets,
    search_tickets,
    get_ticket_by_id,
    update_ticket_status,
    delete_ticket_by_id,

)

from datetime import datetime, timezone

import pytest

def test_create_ticket_saves_ticket(db):
    ticket_data = TicketCreate(
        customer_name="Rahul",
        message="I cannot log in to my account.",
    )

    ticket = create_ticket(
        ticket_data=ticket_data,
        db=db,
    )

    assert ticket.id is not None
    assert ticket.customer_name == "Rahul"
    assert ticket.message == "I cannot log in to my account."
    assert ticket.status == "open"

    saved_ticket = db.get(Ticket, ticket.id)

    assert saved_ticket is not None
    assert saved_ticket.customer_name == "Rahul"

def test_create_ticket_rolls_back_when_commit_fails(db):
    ticket_data = TicketCreate(
        customer_name="Rahul",
        message="Cannot log in",
    )

    with patch.object(
        db,
        "commit",
        side_effect=Exception("Database error"),
    ):
        with pytest.raises(Exception, match="Database error"):
            create_ticket(
                ticket_data=ticket_data,
                db=db,
            )

    assert db.is_active
    assert db.query(Ticket).count() == 0


def test_list_tickets_filters_by_status(db):
    open_ticket = Ticket(
        customer_name="Rahul",
        message="Cannot log in",
        status="open",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    resolved_ticket = Ticket(
        customer_name="Ananya",
        message="Password reset worked",
        status="resolved",
        created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )

    db.add_all([open_ticket, resolved_ticket])
    db.commit()

    results = list_tickets(db=db, status="open")

    assert len(results) == 1
    assert results[0].customer_name == "Rahul"
    assert results[0].status == "open"


def test_list_tickets_respects_pagination(db):
    tickets = [
        Ticket(
            customer_name=f"Customer {i}",
            message=f"Support request {i}",
            status="open",
            created_at=datetime(2026, 1, i + 1, tzinfo=timezone.utc),
        )
        for i in range(3)
    ]

    db.add_all(tickets)
    db.commit()

    results = list_tickets(
        db=db,
        skip=1,
        limit=1,
    )

    assert len(results) == 1
    assert results[0].customer_name == "Customer 1"



def test_count_tickets_groups_by_status(db):
    tickets = [
        Ticket(customer_name="Rahul", message="Login issue", status="open"),
        Ticket(customer_name="Ananya", message="Payment issue", status="open"),
        Ticket(customer_name="Amit", message="Email issue", status="in_progress"),
        Ticket(customer_name="Priya", message="Resolved issue", status="resolved"),
    ]

    db.add_all(tickets)
    db.commit()

    result = count_tickets(db)

    assert result == {
        "total": 4,
        "open": 2,
        "in_progress": 1,
        "resolved": 1,
    }


def test_search_tickets_matches_customer_name_or_message(db):
    tickets = [
        Ticket(
            customer_name="Rahul",
            message="Cannot access account",
            status="open",
        ),
        Ticket(
            customer_name="Ananya",
            message="Password reset email missing",
            status="open",
        ),
        Ticket(
            customer_name="Amit",
            message="Payment failed",
            status="open",
        ),
    ]

    db.add_all(tickets)
    db.commit()

    name_results = search_tickets(db=db, q="Rahul")
    message_results = search_tickets(db=db, q="password reset")

    assert len(name_results) == 1
    assert name_results[0].customer_name == "Rahul"

    assert len(message_results) == 1
    assert message_results[0].customer_name == "Ananya"



def test_search_tickets_respects_pagination(db):
    tickets = [
        Ticket(customer_name="Customer 0", message="Login issue"),
        Ticket(customer_name="Customer 1", message="Login issue"),
        Ticket(customer_name="Customer 2", message="Login issue"),
    ]

    db.add_all(tickets)
    db.commit()

    results = search_tickets(
        db=db,
        q="Login",
        skip=1,
        limit=1,
    )

    assert len(results) == 1
    assert results[0].customer_name == "Customer 1"



def test_get_ticket_by_id_returns_existing_ticket(db):
    ticket = Ticket(
        customer_name="Rahul",
        message="Cannot log in",
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    result = get_ticket_by_id(db=db, ticket_id=ticket.id)

    assert result is not None
    assert result.id == ticket.id
    assert result.customer_name == "Rahul"


def test_get_ticket_by_id_returns_none_for_missing_ticket(db):
    result = get_ticket_by_id(db=db, ticket_id=99999)

    assert result is None



def test_update_ticket_status_changes_status(db):
    ticket = Ticket(
        customer_name="Rahul",
        message="Cannot log in",
        status="open",
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    result = update_ticket_status(
        db=db,
        ticket_id=ticket.id,
        new_status="in_progress",
    )

    assert result is not None
    assert result.status == "in_progress"

    db.refresh(ticket)
    assert ticket.status == "in_progress"


def test_update_ticket_status_returns_none_for_missing_ticket(db):
    result = update_ticket_status(
        db=db,
        ticket_id=99999,
        new_status="resolved",
    )

    assert result is None


def test_delete_ticket_by_id_deletes_existing_ticket(db):
    ticket = Ticket(
        customer_name="Rahul",
        message="Cannot log in",
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    ticket_id = ticket.id

    result = delete_ticket_by_id(
        db=db,
        ticket_id=ticket_id,
    )

    assert result is True
    assert db.get(Ticket, ticket_id) is None


def test_delete_ticket_by_id_returns_false_for_missing_ticket(db):
    result = delete_ticket_by_id(
        db=db,
        ticket_id=99999,
    )

    assert result is False


def test_search_tickets_returns_empty_for_whitespace_query(db):
    ticket = Ticket(
        customer_name="Rahul",
        message="Cannot log in",
    )
    db.add(ticket)
    db.commit()

    results = search_tickets(
        db=db,
        q="   ",
    )

    assert results == []



def test_delete_ticket_by_id_rolls_back_when_commit_fails(db):
    ticket = Ticket(
        customer_name="Rahul",
        message="Cannot log in",
    )
    db.add(ticket)
    db.commit()
    ticket_id = ticket.id

    with patch.object(
        db,
        "commit",
        side_effect=Exception("Database error"),
    ):
        with pytest.raises(Exception, match="Database error"):
            delete_ticket_by_id(
                db=db,
                ticket_id=ticket_id,
            )

    assert db.is_active
    assert db.get(Ticket, ticket_id) is not None



def test_update_ticket_status_rolls_back_when_commit_fails(db):
    ticket = Ticket(
        customer_name="Rahul",
        message="Cannot log in",
        status="open",
    )
    db.add(ticket)
    db.commit()
    ticket_id = ticket.id

    with patch.object(
        db,
        "commit",
        side_effect=Exception("Database error"),
    ):
        with pytest.raises(Exception, match="Database error"):
            update_ticket_status(
                db=db,
                ticket_id=ticket_id,
                new_status="in_progress",
            )

    assert db.is_active
    db.refresh(ticket)
    assert ticket.status == "open"

