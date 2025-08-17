# app/models.py
from __future__ import annotations

import enum
import uuid
from datetime import datetime, date

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Date,
    Text,
    Integer,
    DECIMAL,
    JSON,
    ForeignKey,
    Enum as SQLEnum,
    TypeDecorator,
    CHAR,
    Boolean,
)
from sqlalchemy.dialects.mysql import CHAR as MYSQL_CHAR
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import relationship, sessionmaker, declarative_base
from sqlalchemy.sql import func

from app.core.config import settings

Base = declarative_base()

# -------- GUID (UUID文字列を36桁で保存) --------
class GUID(TypeDecorator):
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(MYSQL_CHAR(36)) if dialect.name == "mysql" else dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        return None if value is None else str(value)

    def process_result_value(self, value, dialect):
        return None if value is None else uuid.UUID(str(value))

# -------- Enums --------
class LocationType(str, enum.Enum):
    simulation_golf = "simulation_golf"
    real_golf_course = "real_golf_course"

class ReservationStatus(str, enum.Enum):
    booked = "booked"
    completed = "completed"
    cancelled = "cancelled"

class PaymentStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"

# -------- Users --------
class User(Base):
    __tablename__ = "users"

    user_id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    usertype = Column(String(50), nullable=False, default="user")
    username = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    gender = Column(String(10), nullable=True)
    line_user_id = Column(String(255), unique=True, nullable=True)

    profile_picture_url = Column(Text, nullable=True)
    bio = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    birthday = Column(Date, nullable=True)
    golf_score_ave = Column(Integer, nullable=True)
    golf_exp = Column(Integer, nullable=True)

    zip_code = Column(String(10), nullable=True)
    state = Column(String(50), nullable=True)
    address1 = Column(String(255), nullable=True)
    address2 = Column(String(255), nullable=True)

    sport_exp = Column(String(100), nullable=True)
    industry = Column(String(100), nullable=True)
    job_title = Column(String(100), nullable=True)
    position = Column(String(100), nullable=True)

# (Coach, Location, Video, CoachingSession, CoachingReservation, SectionGroup, SwingSection)
# ↓ ここはあなたの既存コードのままでOK。省略します。

# ---------- Async Engine / Session ----------
DATABASE_URL = settings.assemble_db_url()

engine = create_async_engine(
    DATABASE_URL,
    echo=(settings.env.lower() == "development"),
    pool_size=5,
    max_overflow=10,
    pool_recycle=1800,
    pool_pre_ping=True,
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
