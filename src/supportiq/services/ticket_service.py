import logging
from typing import Literal

from sqlalchemy import func
from sqlalchemy.orm import Session

from supportiq.models.ticket import Ticket
from supportiq.schemas.ticket import TicketCreate


logger = logging.getLogger(__name__)


def create_ticket(
    ticket_data: TicketCreate,
    db: Session,
) -> Ticket:
    """Create and persist a customer support ticket."""

    ticket = Ticket(
        customer_name=ticket_data.customer_name,
        message=ticket_data.message,
    )

    try:
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
    except Exception:
        db.rollback()
        logger.exception("Failed to create ticket")
        raise

    return ticket



def list_tickets(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    status: Literal["open", "in_progress", "resolved"] | None = None,
) -> list[Ticket]:
    """Return tickets with pagination and an optional status filter."""

    query = db.query(Ticket)

    if status is not None:
        query = query.filter(Ticket.status == status)

    return (
        query
        .order_by(Ticket.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )



def search_tickets(
    db: Session,
    q: str,
    skip: int = 0,
    limit: int = 10,
) -> list[Ticket]:
    if not q.strip():
        return []
    search_term = f"%{q.strip()}%"
    return (
        db.query(Ticket)
        .filter(Ticket.customer_name.ilike(search_term) | Ticket.message.ilike(search_term))
        .order_by(Ticket.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def count_tickets(db: Session) -> dict[str, int]:
    """Return total ticket counts grouped by status."""

    total = db.query(func.count(Ticket.id)).scalar() or 0

    open_count = (
        db.query(func.count(Ticket.id))
        .filter(Ticket.status == "open")
        .scalar()
        or 0
    )

    in_progress_count = (
        db.query(func.count(Ticket.id))
        .filter(Ticket.status == "in_progress")
        .scalar()
        or 0
    )

    resolved_count = (
        db.query(func.count(Ticket.id))
        .filter(Ticket.status == "resolved")
        .scalar()
        or 0
    )

    return {
        "total": total,
        "open": open_count,
        "in_progress": in_progress_count,
        "resolved": resolved_count,
    }


def get_ticket_by_id(
    db: Session,
    ticket_id: int,
) -> Ticket | None:
    """Return a ticket by ID, or None if it doesn't exist."""
    return db.get(Ticket, ticket_id)


def update_ticket_status(
    db: Session,
    ticket_id: int,
    new_status: Literal["open", "in_progress", "resolved"],
) -> Ticket | None:
    """Update a ticket's status, returning None if it doesn't exist."""
    ticket = db.get(Ticket, ticket_id)

    if ticket is None:
        return None

    ticket.status = new_status

    try:
        db.commit()
        db.refresh(ticket)
    except Exception:
        db.rollback()
        logger.exception("Failed to update ticket status")
        raise

    return ticket


def delete_ticket_by_id(
    db: Session,
    ticket_id: int,
) -> bool:
    """Delete a ticket by ID; return False if it doesn't exist."""
    ticket = db.get(Ticket, ticket_id)

    if ticket is None:
        return False

    try:
        db.delete(ticket)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to delete ticket")
        raise

    return True
