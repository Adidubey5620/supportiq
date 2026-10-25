
import logging

from sqlalchemy.orm import Session
from typing import Literal
from sqlalchemy import func
from supportiq.models.ticket import Ticket
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
