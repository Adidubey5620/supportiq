from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Literal
import logging

logger = logging.getLogger(__name__)

from supportiq.db.session import get_db
from supportiq.models.ticket import Ticket
from supportiq.services.retrieval import retrieve_knowledge
from supportiq.services.ticket_service import create_ticket, list_tickets
from supportiq.schemas.ticket import (
    TicketCreate,
    TicketResponse,
    TicketStatusUpdate,
    TicketCountResponse,
    AIReplyResponse,
)
from supportiq.models.knowledge_article import KnowledgeArticle
from supportiq.services.ticket_service import create_ticket
from supportiq.services.ai import generate_support_reply
from supportiq.services.ticket_service import (
    count_tickets,
    create_ticket,
    list_tickets,
    search_tickets,
    get_ticket_by_id,
    update_ticket_status,
    delete_ticket_by_id,

)

router = APIRouter()



@router.post(
    "/tickets",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Tickets"],
)
def create_ticket_endpoint(
    ticket_data: TicketCreate,
    db: Session = Depends(get_db),
) -> TicketResponse:
    try:
        return create_ticket(
            ticket_data=ticket_data,
            db=db,
        )
    except Exception:
        logger.exception("Ticket creation failed at API layer")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create ticket.",
        )



@router.get(
    "/tickets",
    response_model=list[TicketResponse],
    tags=["Tickets"],
)
def list_tickets_endpoint(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    status: Literal["open", "in_progress", "resolved"] | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[TicketResponse]:
    return list_tickets(
        db=db,
        skip=skip,
        limit=limit,
        status=status,
    )



@router.get(
    "/tickets/count",
    response_model=TicketCountResponse,
    tags=["Tickets"],
)
def count_tickets_endpoint(
    db: Session = Depends(get_db),
) -> TicketCountResponse:
    return count_tickets(db=db)


@router.get(
    "/tickets/search",
    response_model=list[TicketResponse],
    tags=["Tickets"],
)
def search_tickets_endpoint(
    q: str = Query(min_length=1, max_length=100),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[TicketResponse]:
    return search_tickets(
        db=db,
        q=q,
        skip=skip,
        limit=limit,
    )




@router.get(
    "/tickets/{ticket_id}",
    response_model=TicketResponse,
    tags=["Tickets"],
)

def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
) -> TicketResponse:
    ticket = get_ticket_by_id(
        db=db,
        ticket_id=ticket_id,
    )

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    return ticket



@router.patch(
    "/tickets/{ticket_id}",
    response_model=TicketResponse,
    tags=["Tickets"]
)

def update_ticket_status_endpoint(
    ticket_id: int,
    status_data: TicketStatusUpdate,
    db: Session = Depends(get_db),
) -> TicketResponse:
    try:
        ticket = update_ticket_status(
            db=db,
            ticket_id=ticket_id,
            new_status=status_data.status,
        )
    except Exception:
        logger.exception(
            "Ticket status update failed at API layer for ticket %s",
            ticket_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update ticket status.",
        )

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
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
    try:
        deleted = delete_ticket_by_id(
            db=db,
            ticket_id=ticket_id,
        )
    
    except Exception:
        logger.exception(
            "Ticket deletion failed at API layer for ticket %s",
            ticket_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete ticket.",
        )


    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found.",
        )



@router.post(
    "/tickets/{ticket_id}/generate-reply",
    tags=["AI"],
)

async def generate_ticket_reply(
    ticket_id: int,
    db: Session = Depends(get_db),
) -> AIReplyResponse:
    ticket = db.get(Ticket, ticket_id)

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found.",
        )

    try:
        articles = retrieve_knowledge(
            customer_message=ticket.message,
            db=db,
            limit=5,
        )

        if not articles:
            return AIReplyResponse(
                ticket_id=ticket.id,
                draft_reply="No relevant knowledge found. Please contact human support.",
                requires_human_review=True,
            )

        knowledge_context = "\n\n".join(
            f"Title: {article.title}\n"
            f"Category: {article.category}\n"
            f"Content: {article.content}"
            for article in articles
        )

        draft_reply = await generate_support_reply(
            customer_message=ticket.message,
            knowledge_context=knowledge_context,
        )

    except Exception:
        logger.exception(
            "Failed to generate AI reply for ticket %s",
            ticket_id,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to generate an AI reply. Please try again.",
        )

    return AIReplyResponse(
        ticket_id=ticket.id,
        draft_reply=draft_reply,
        requires_human_review=True,
    )

