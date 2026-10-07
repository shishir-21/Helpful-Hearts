from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.ai.openai_provider import OpenAIProvider
from app.integrations.ai.provider import AssistantInput, ProviderError
from app.models.assistant import Conversation, Message
from app.models.user import User

MAX_HISTORY_MESSAGES = 20


class AssistantService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.provider = OpenAIProvider()

    def create_conversation(self, user: User, title: str | None) -> Conversation:
        conversation = Conversation(patient_id=user.id, title=title)
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def get_conversation(self, user: User, conversation_id: UUID) -> Conversation | None:
        return self.db.scalar(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.patient_id == user.id,
            )
        )

    def list_conversations(self, user: User) -> list[Conversation]:
        return list(
            self.db.scalars(
                select(Conversation)
                .where(Conversation.patient_id == user.id)
                .order_by(Conversation.updated_at.desc())
            ).all()
        )

    def list_messages(self, conversation: Conversation) -> list[Message]:
        return list(
            self.db.scalars(
                select(Message)
                .where(Message.conversation_id == conversation.id)
                .order_by(Message.created_at.asc())
            ).all()
        )

    def send_message(self, conversation: Conversation, content: str) -> Message:
        history = self.list_messages(conversation)
        user_message = Message(conversation_id=conversation.id, role="user", content=content)
        self.db.add(user_message)
        self.db.flush()

        context: Sequence[AssistantInput] = [
            AssistantInput(message.role, message.content)
            for message in history[-MAX_HISTORY_MESSAGES:]
        ]
        context = [*context, AssistantInput("user", content)]

        try:
            answer = self.provider.generate(context)
        except ProviderError:
            self.db.rollback()
            raise

        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=answer,
        )
        self.db.add(assistant_message)
        self.db.commit()
        self.db.refresh(assistant_message)
        return assistant_message
