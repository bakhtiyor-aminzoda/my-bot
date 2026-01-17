import aiosqlite
import logging
from datetime import datetime

DB_NAME = "bot_database.db"
logger = logging.getLogger(__name__)

async def init_db():
    """Initializes the database with necessary tables."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                joined_at TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                role TEXT,
                content TEXT,
                timestamp TIMESTAMP
            )
        """)
        await db.commit()
    logger.info("✅ Database initialized.")

async def add_user(user_id: int, username: str, full_name: str):
    """Adds a new user if they don't exist."""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT id FROM users WHERE id = ?", (user_id,)) as cursor:
            if await cursor.fetchone():
                return # User exists
        
        await db.execute(
            "INSERT INTO users (id, username, full_name, joined_at) VALUES (?, ?, ?, ?)",
            (user_id, username, full_name, datetime.now())
        )
        await db.commit()
        logger.info(f"🆕 New user added: {user_id}")

async def get_all_users():
    """Returns a list of all user IDs."""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT id FROM users") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

async def add_message(user_id: int, role: str, content: str):
    """Saves a message to history."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO messages (user_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (user_id, role, content, datetime.now())
        )
        await db.commit()

async def get_chat_history(user_id: int, limit: int = 20):
    """Retrieves recent chat history for context."""
    async with aiosqlite.connect(DB_NAME) as db:
        # Get last N messages order by asc timestamp
        # Subquery to get last N, then order by ID ASC to restore chronological order
        async with db.execute(f"""
            SELECT role, content FROM (
                SELECT role, content, id FROM messages 
                WHERE user_id = ? 
                ORDER BY id DESC 
                LIMIT ?
            ) ORDER BY id ASC
        """, (user_id, limit)) as cursor:
            rows = await cursor.fetchall()
            # Convert to format expected by Gemini (parts, role)
            # Gemini expects 'user' or 'model' roles. Our DB stores them as such.
            return [{"role": row[0], "parts": [row[1]]} for row in rows]
