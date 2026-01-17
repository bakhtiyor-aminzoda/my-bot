import os
import logging
from datetime import datetime
from sqlalchemy import Column, BigInteger, String, DateTime, Integer, select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Configure Logging
logger = logging.getLogger(__name__)

# Database Configuration
# Render provides DATABASE_URL. If not found, use local SQLite.
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Ensure usage of asyncpg driver
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
        
    logger.info("🔌 Using remote PostgreSQL database.")
else:
    DATABASE_URL = "sqlite+aiosqlite:///bot_database.db"
    logger.info("📁 Using local SQLite database.")

# SQLAlchemy Setup
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

# --- Models ---

class User(Base):
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True)
    username = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    joined_at = Column(DateTime, default=datetime.utcnow)

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, index=True)
    role = Column(String) # 'user' or 'model'
    content = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

# --- Functions ---

async def init_db():
    """Initializes the database (creates tables)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Database tables created/verified.")

async def add_user(user_id: int, username: str, full_name: str):
    """Adds a new user if they don't exist."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).filter_by(id=user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            new_user = User(id=user_id, username=username, full_name=full_name)
            session.add(new_user)
            await session.commit()
            logger.info(f"🆕 New user added: {user_id}")

async def get_all_users():
    """Returns a list of all user IDs."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User.id))
        return result.scalars().all()

async def count_users():
    """Returns the total number of users."""
    async with AsyncSessionLocal() as session:
        # Optimized count query
        result = await session.execute(select(User.id))
        return len(result.scalars().all())

async def add_message(user_id: int, role: str, content: str):
    """Saves a message to history."""
    async with AsyncSessionLocal() as session:
        msg = Message(user_id=user_id, role=role, content=content)
        session.add(msg)
        await session.commit()

async def get_chat_history(user_id: int, limit: int = 20):
    """Retrieves recent chat history for context."""
    async with AsyncSessionLocal() as session:
        # Get last N messages
        stmt = (
            select(Message.role, Message.content)
            .where(Message.user_id == user_id)
            .order_by(Message.id.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        rows = result.fetchall()
        
        # Reverse to chronological order (Oldest first)
        rows.reverse()
        
        return [{"role": row.role, "parts": [row.content]} for row in rows]

class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, index=True)
    client_name = Column(String)
    service_type = Column(String) # 'shop', 'booking', 'consultation'
    slot_time = Column(DateTime)
    status = Column(String, default="new") # new, approved, completed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)

async def add_booking(user_id: int, client_name: str, service_type: str, slot_time: datetime):
    """Creates a new booking."""
    async with AsyncSessionLocal() as session:
        booking = Booking(
            user_id=user_id,
            client_name=client_name,
            service_type=service_type,
            slot_time=slot_time
        )
        session.add(booking)
        await session.commit()
        return booking.id

async def get_all_bookings():
    """Returns all bookings for the admin dashboard."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Booking).order_by(Booking.slot_time.desc()))
        return result.scalars().all()
