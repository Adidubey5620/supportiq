from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import logging

logger = logging.getLogger(__name__)

from supportiq.db.session import get_db
from supportiq.models.ticket import Ticket
from supportiq.schemas.ticket import TicketCreate, TicketResponse, TicketStatusUpdate

router = APIRouter()

@router.post(
    "/tickets",
    response_model= TicketResponse,
    status_code=201,
    tags=["Tickets"],
)
def create_ticket(
    ticket_data: TicketCreate,
    db: Session = Depends(get_db),
) -> TicketResponse:
    ticket = Ticket(
        customer_name=ticket_data.customer_name,
        message=ticket_data.message
    )

    try:
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
    except Exception:
        db.rollback()
        logger.exception("Failed to create ticket")
        raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to create ticket.",
        )
    return ticket

@router.get(
    "/tickets",
    response_model=list[TicketResponse],
    tags=["Tickets"],
)
def list_ticket(
    db:Session = Depends(get_db),
) -> list[TicketResponse]:
    tickets = (
        db.query(Ticket)
        .order_by(Ticket.created_at.desc())
        .all()
    )

    return tickets


@router.get(
    "/tickets/{ticket_id}",
    response_model=TicketResponse,
    tags=["Tickets"],
)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
) -> TicketResponse:
    ticket = db.get(Ticket, ticket_id)

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )
    
    return ticket

@router.patch(
    "/ticket/{ticket_id}",
    response_model=TicketResponse,
    tags=["Tickets"]
)
def update_ticket_status(
    ticket_id: int,
    status_data: TicketStatusUpdate,
    db: Session = Depends(get_db)
) -> TicketResponse:
    ticket = db.get(Ticket, ticket_id)

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    ticket.status = status_data.status

    try:
        db.commit()
        db.refresh(ticket)
    except Exception:
        db.rollback()
        logger.exception("Failed to update ticket status")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update ticket status."
        )

    return ticket


@router.delete(
    "/tickets/{ticket_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Tickets"]
)
def delete_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
) -> None:
    ticket = db.get(Ticket, ticket_id)

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found."
        )

    try:
        db.delete(ticket)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to delete ticket")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete ticket."
        )