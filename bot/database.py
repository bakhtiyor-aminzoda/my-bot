import os
import logging
from datetime import datetime, timedelta
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

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, index=True)
    name = Column(String)
    contact_info = Column(String)
    business_type = Column(String)
    budget = Column(String)
    task_description = Column(String)
    service_context = Column(String)
    status = Column(String, default="new")
    created_at = Column(DateTime, default=datetime.utcnow)

async def add_order(user_id: int, data: dict):
    """Saves a new order/lead to the database."""
    async with AsyncSessionLocal() as session:
        order = Order(
            user_id=user_id,
            name=data.get("name"),
            contact_info=data.get("contact_info"),
            business_type=data.get("business_type"),
            budget=data.get("budget"),
            task_description=data.get("task_description"),
            service_context=data.get("service_context", "General")
        )
        session.add(order)
        await session.commit()
        logger.info(f"📝 New order saved: {order.id}")
        return order.id

async def get_recent_orders(limit: int = 10, search_query: str = None):
    async with AsyncSessionLocal() as session:
        query = select(Order).order_by(Order.created_at.desc())
        
        if search_query:
            search_filter = f"%{search_query}%"
            query = query.where(
                (Order.name.ilike(search_filter)) | 
                (Order.contact_info.ilike(search_filter))
            )
        
        if limit:
            query = query.limit(limit)
            
        result = await session.execute(query)
        return result.scalars().all()

async def get_all_user_ids():
    """Returns a list of unique user_ids who have interacted/ordered."""
    async with AsyncSessionLocal() as session:
        # Assuming we want to broadcast to anyone who has an order or is in a users table
        # Since we only have Order table with user_id for now (and maybe stats logic), 
        # let's look at Order.user_id distinct. 
        # Ideally we should have a Users table. For now, we use unique IDs from Orders.
        result = await session.execute(select(Order.user_id).distinct())
        return result.scalars().all()

async def count_orders():
    """Returns total number of orders."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Order.id))
        return len(result.scalars().all())

async def get_order_by_id(order_id: int):
    """Returns a single order by ID."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Order).where(Order.id == order_id))
        return result.scalar_one_or_none()

async def update_order_status(order_id: int, new_status: str):
    """Updates the status of an order."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        
        if order:
            order.status = new_status
            await session.commit()
            return order
        return None

async def update_order_details(order_id: int, data: dict):
    """Updates editable fields of an order."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        
        if order:
            if "budget" in data: order.budget = data["budget"]
            if "contact_info" in data: order.contact_info = data["contact_info"]
            if "task_description" in data: order.task_description = data["task_description"]
            
            await session.commit()
            return order
        return None

async def get_daily_stats(days: int = 7):
    """Returns order counts grouped by day for the last N days."""
    from sqlalchemy import func
    async with AsyncSessionLocal() as session:
        # Note: This query is dialect specific. Assuming SQLite/Postgres compatibility for simple date casting.
        # For cross-db simplicity in this demo, we might fetch recent and aggregate in python if SQL is tricky without specific dialect imports.
        # But let's try a standard approach.
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = await session.execute(
            select(func.date(Order.created_at), func.count(Order.id))
            .where(Order.created_at >= cutoff)
            .group_by(func.date(Order.created_at))
            .order_by(func.date(Order.created_at))
        )
        return result.all()

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String)
    price = Column(Integer)
    icon = Column(String) # Emoji or Image URL
    category = Column(String) # 'bots', 'crm', 'other'
    desc = Column(String)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

async def add_product(data: dict):
    """Adds a new product."""
    async with AsyncSessionLocal() as session:
        product = Product(
            title=data.get("title"),
            price=data.get("price"),
            icon=data.get("icon"),
            category=data.get("category"),
            desc=data.get("desc"),
            is_active=1
        )
        session.add(product)
        await session.commit()
        return product.id

async def get_all_products(only_active: bool = True):
    """Returns all products."""
    async with AsyncSessionLocal() as session:
        query = select(Product)
        if only_active:
            query = query.where(Product.is_active == 1)
        
        # Sort by ID or Category
        query = query.order_by(Product.id.asc())
        
        result = await session.execute(query)
        return result.scalars().all()

async def update_product(product_id: int, data: dict):
    """Updates a product."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()
        
        if product:
            for key, value in data.items():
                if hasattr(product, key):
                    setattr(product, key, value)
            await session.commit()
            return product
        return None

async def delete_product(product_id: int):
    """Soft deletes a product."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()
        
        if product:
            product.is_active = 0
            await session.commit()
            return True
        return False

async def seed_products():
    """Seeds default products if table is empty."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Product).limit(1))
        if result.scalar_one_or_none():
            return # Already has data
            
    # Default Products
    items = [
        {"title": 'Telegram Магазин', "price": 2500, "icon": '🛍', "category": 'bots', "desc": 'Каталог, корзина, оплата внутри Telegram.'},
        {"title": 'CRM Система', "price": 4000, "icon": '📊', "category": 'crm', "desc": 'Управление заявками и аналитика для бизнеса.'},
        {"title": 'Чат-бот Визитка', "price": 1000, "icon": '📇', "category": 'bots', "desc": 'Ответы на вопросы, контакты, портфолио.'},
        {"title": 'Запись клиентов', "price": 3000, "icon": '📅', "category": 'bots', "desc": 'Бронирование слотов, календарь, напоминания.'},
        {"title": 'AI Ассистент', "price": 5000, "icon": '🤖', "category": 'crm', "desc": 'Умный бот на базе GPT для техподдержки.'},
        {"title": 'Консультация', "price": 500, "icon": '👨‍💻', "category": 'other', "desc": 'Разбор вашей бизнес-задачи за 1 час.'}
    ]
    
    for item in items:
        await add_product(item)
    logger.info("🌱 Database seeded with default products.")
