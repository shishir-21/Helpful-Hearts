from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.core.rate_limit import assistant_rate_limiter
from app.models.assistant import Conversation
from app.models.user import User
from app.schemas.assistant import (
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
)
from app.services.assistant import AssistantService
from app.integrations.ai.provider import ProviderError

router = APIRouter(prefix="/assistant", tags=["Assistant"])
patient_only = require_roles("patient")


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    payload: ConversationCreate,
    current_user: User = Depends(patient_only),
    db: Session = Depends(get_db),
) -> Conversation:
    return AssistantService(db).create_conversation(current_user, payload.title)


@router.get("/conversations", response_model=list[ConversationResponse])
def list_conversations(
    current_user: User = Depends(patient_only),
    db: Session = Depends(get_db),
) -> list[Conversation]:
    return AssistantService(db).list_conversations(current_user)


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[MessageResponse],
)
def list_messages(
    conversation_id: UUID,
    current_user: User = Depends(patient_only),
    db: Session = Depends(get_db),
):
    service = AssistantService(db)
    conversation = service.get_conversation(current_user, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return service.list_messages(conversation)


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageResponse,
)
def send_message(
    conversation_id: UUID,
    payload: MessageCreate,
    current_user: User = Depends(patient_only),
    db: Session = Depends(get_db),
) -> MessageResponse:
    assistant_rate_limiter.check(current_user.id)
    service = AssistantService(db)
    conversation = service.get_conversation(current_user, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    try:
        return service.send_message(conversation, payload.content)
    except ProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
