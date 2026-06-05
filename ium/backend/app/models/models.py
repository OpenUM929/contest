import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, Float, Integer, DateTime, ForeignKey, Date, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class WelfareWorker(Base):
    __tablename__ = "welfare_workers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50))
    region: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    users: Mapped[list["User"]] = relationship(back_populates="welfare_worker")


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_type: Mapped[str] = mapped_column(String(10))      # elder | youth
    nickname: Mapped[str | None] = mapped_column(String(50))
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False)
    welfare_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("welfare_workers.id"))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    welfare_worker: Mapped["WelfareWorker | None"] = relationship(back_populates="users")
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="user")
    alerts: Mapped[list["SafetyAlert"]] = relationship(back_populates="user")


class WeeklyTopic(Base):
    __tablename__ = "weekly_topics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    media_url: Mapped[str | None] = mapped_column(Text)
    media_type: Mapped[str | None] = mapped_column(String(20))   # image | audio | video | text
    source: Mapped[str | None] = mapped_column(String(100))
    source_url: Mapped[str | None] = mapped_column(Text)
    ai_question: Mapped[str | None] = mapped_column(Text)
    active_week: Mapped[datetime] = mapped_column(Date)
    region: Mapped[str] = mapped_column(String(100), default="default")
    welfare_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("welfare_workers.id"))
    question_type: Mapped[str] = mapped_column(String(20), default="narrative")  # choice | narrative | mixed
    is_customized: Mapped[bool] = mapped_column(Boolean, default=False)
    parent_topic_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("weekly_topics.id"))
    text_content: Mapped[str | None] = mapped_column(Text)
    preview_thumbnail: Mapped[str | None] = mapped_column(Text)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    choices: Mapped[str | None] = mapped_column(Text)  # JSON 문자열 ["선택1", "선택2", ...]
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    conversations: Mapped[list["Conversation"]] = relationship(back_populates="topic")
    essays: Mapped[list["Essay"]] = relationship(back_populates="topic")


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    topic_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("weekly_topics.id"))
    role: Mapped[str] = mapped_column(String(10))           # user | assistant
    content: Mapped[str] = mapped_column(Text)
    emotion_label: Mapped[str | None] = mapped_column(String(20))
    emotion_score: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="conversations")
    topic: Mapped["WeeklyTopic | None"] = relationship(back_populates="conversations")


class Essay(Base):
    __tablename__ = "essays"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("weekly_topics.id"))
    title: Mapped[str | None] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    contributor_cnt: Mapped[int] = mapped_column(Integer, default=0)
    prompt_version: Mapped[str] = mapped_column(String(10), default="v0")
    published_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    topic: Mapped["WeeklyTopic | None"] = relationship(back_populates="essays")


class SafetyAlert(Base):
    __tablename__ = "safety_alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    alert_type: Mapped[str] = mapped_column(String(50))     # no_contact | crisis | emotion_drop
    severity: Mapped[str | None] = mapped_column(String(10))  # red | yellow
    note: Mapped[str | None] = mapped_column(Text)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="alerts")


class InterventionLog(Base):
    __tablename__ = "intervention_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    welfare_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("welfare_workers.id"))
    action_type: Mapped[str] = mapped_column(String(50))  # phone | visit | counseling | detail | alert_resolve
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class EssayContributor(Base):
    __tablename__ = "essay_contributors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    essay_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("essays.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    message_count: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TopicProposal(Base):
    __tablename__ = "topic_proposals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    welfare_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("welfare_workers.id"))
    mode: Mapped[str] = mapped_column(String(20))  # detailed | simple
    welfare_input: Mapped[str | None] = mapped_column(Text)
    ai_suggestions: Mapped[dict | None] = mapped_column(JSON)  # JSONB
    welfare_selection: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("weekly_topics.id"))
    question_type: Mapped[str | None] = mapped_column(String(20))  # choice | narrative | mixed
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | approved | rejected
    question_set_json: Mapped[dict | None] = mapped_column(JSON)  # 복지사 편집한 QuestionSet
    is_draft: Mapped[bool] = mapped_column(Boolean, default=False)
    published_topic_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("weekly_topics.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SurveyTemplate(Base):
    __tablename__ = "survey_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    welfare_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("welfare_workers.id"))
    name: Mapped[str] = mapped_column(String(100))
    question_set_json: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SurveyResponse(Base):
    __tablename__ = "survey_responses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("weekly_topics.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    question_id: Mapped[str] = mapped_column(String(10))         # q1, q2
    question_type: Mapped[str] = mapped_column(String(10))       # choice | narrative
    selected_option_id: Mapped[str | None] = mapped_column(String(20))
    selected_option_label: Mapped[str | None] = mapped_column(String(100))
    narrative_text: Mapped[str | None] = mapped_column(Text)
    responded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
