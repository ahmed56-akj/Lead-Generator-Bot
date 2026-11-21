import csv
import io
import aiosqlite
from datetime import datetime
from config import DB_PATH

async def init_db():
    """Initialize database tables."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                is_admin INTEGER DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                full_name TEXT,
                email TEXT,
                phone TEXT,
                service TEXT,
                budget TEXT,
                notes TEXT,
                status TEXT DEFAULT 'NEW',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def record_user(user_id: int, username: str, first_name: str, last_name: str, is_admin: bool = False):
    """Save or update user activity."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, username, first_name, last_name, is_admin, last_active)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                last_name = excluded.last_name,
                is_admin = CASE WHEN users.is_admin = 1 THEN 1 ELSE excluded.is_admin END,
                last_active = CURRENT_TIMESTAMP
        """, (user_id, username, first_name, last_name, 1 if is_admin else 0))
        await db.commit()

async def save_lead(
    user_id: int,
    username: str,
    full_name: str,
    email: str,
    phone: str,
    service: str,
    budget: str,
    notes: str
) -> int:
    """Save a new qualified lead into the database."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO leads (user_id, username, full_name, email, phone, service, budget, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, username, full_name, email, phone, service, budget, notes))
        await db.commit()
        return cursor.lastrowid

async def get_lead_by_id(lead_id: int):
    """Fetch single lead by ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def update_lead_status(lead_id: int, status: str) -> bool:
    """Update lead status (NEW, CONTACTED, QUALIFIED, WON, LOST)."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("UPDATE leads SET status = ? WHERE id = ?", (status, lead_id))
        await db.commit()
        return cursor.rowcount > 0

async def get_recent_leads(limit: int = 10, offset: int = 0):
    """Get list of recent leads with pagination."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM leads ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def get_lead_stats() -> dict:
    """Calculate lead and user metrics."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM leads") as cur:
            total_leads = (await cur.fetchone())[0]

        async with db.execute("SELECT COUNT(*) FROM leads WHERE status = 'NEW'") as cur:
            new_leads = (await cur.fetchone())[0]

        async with db.execute("SELECT COUNT(*) FROM leads WHERE status = 'CONTACTED'") as cur:
            contacted_leads = (await cur.fetchone())[0]

        async with db.execute("SELECT COUNT(*) FROM leads WHERE status IN ('QUALIFIED', 'WON')") as cur:
            qualified_leads = (await cur.fetchone())[0]

        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            total_users = (await cur.fetchone())[0]

        # Count leads created today
        today = datetime.utcnow().strftime("%Y-%m-%d")
        async with db.execute("SELECT COUNT(*) FROM leads WHERE DATE(created_at) = DATE(?)", (today,)) as cur:
            leads_today = (await cur.fetchone())[0]

    return {
        "total_leads": total_leads,
        "new_leads": new_leads,
        "contacted_leads": contacted_leads,
        "qualified_leads": qualified_leads,
        "leads_today": leads_today,
        "total_users": total_users
    }

async def get_all_user_ids() -> list[int]:
    """Retrieve all user IDs who ever contacted the bot for broadcasting."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            rows = await cursor.fetchall()
            return [r[0] for r in rows]

async def export_leads_to_csv() -> io.BytesIO:
    """Export all leads to a CSV in-memory stream for Telegram file upload."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM leads ORDER BY id ASC") as cursor:
            rows = await cursor.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Lead ID", "User ID", "Telegram Username", "Full Name",
        "Email", "Phone", "Service Required", "Budget Range",
        "Project Notes", "Status", "Created At"
    ])

    for row in rows:
        writer.writerow([
            row["id"],
            row["user_id"],
            row["username"] or "",
            row["full_name"],
            row["email"],
            row["phone"],
            row["service"],
            row["budget"],
            row["notes"],
            row["status"],
            row["created_at"]
        ])

    bytes_output = io.BytesIO(output.getvalue().encode("utf-8-sig"))
    bytes_output.name = f"leads_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    bytes_output.seek(0)
    return bytes_output
