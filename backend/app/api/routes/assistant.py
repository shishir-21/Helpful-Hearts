from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.assistant import AssistantConversation, AssistantMessage
from app.models.user import User
from app.schemas.assistant import ConversationCreateRequest, ConversationResponse, MessageCreateRequest, MessageResponse
from app.services.assistant import AssistantProviderError, SYSTEM_PROMPT, get_assistant_provider

router = APIRouter(prefix="/assistant", tags=["Health Assistant"])


def _get_owned_conversation(db: Session, conversation_id: UUID, patient_id: UUID) -> AssistantConversation:
    conversation = db.scalar(
        select(AssistantConversation).where(
            AssistantConversation.id == conversation_id,
            AssistantConversation.patient_id == patient_id,
        )
    )
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conversation


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    payload: ConversationCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConversationResponse:
    conversation = AssistantConversation(patient_id=current_user.id, title=payload.title.strip() or "Health Assistant")
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return ConversationResponse.model_validate(conversation)


@router.get("/conversations", response_model=list[ConversationResponse])
def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ConversationResponse]:
    conversations = db.scalars(
        select(AssistantConversation)
        .where(AssistantConversation.patient_id == current_user.id)
        .order_by(AssistantConversation.updated_at.desc())
    ).all()
    return [ConversationResponse.model_validate(item) for item in conversations]


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
def list_messages(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MessageResponse]:
    _get_owned_conversation(db, conversation_id, current_user.id)
    messages = db.scalars(
        select(AssistantMessage)
        .where(AssistantMessage.conversation_id == conversation_id)
        .order_by(AssistantMessage.created_at.asc())
    ).all()
    return [MessageResponse.model_validate(item) for item in messages]


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    conversation_id: UUID,
    payload: MessageCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    conversation = _get_owned_conversation(db, conversation_id, current_user.id)
    user_message = AssistantMessage(conversation_id=conversation.id, role="user", content=payload.content.strip())
    db.add(user_message)
    db.flush()

    history = db.scalars(
        select(AssistantMessage)
        .where(AssistantMessage.conversation_id == conversation.id)
        .order_by(AssistantMessage.created_at.asc())
    ).all()
    provider_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    provider_messages.extend({"role": item.role, "content": item.content} for item in history)

    try:
        response_text = await get_assistant_provider().generate(provider_messages)
    except AssistantProviderError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    assistant_message = AssistantMessage(conversation_id=conversation.id, role="assistant", content=response_text)
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)
    return MessageResponse.model_validate(assistant_message)
