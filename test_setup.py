import asyncio
from database import (
    init_db,
    record_user,
    save_lead,
    get_lead_stats,
    export_leads_to_csv,
    update_lead_status,
    get_recent_leads
)

async def run_tests():
    print("[1/5] Initializing Database...")
    await init_db()

    print("[2/5] Testing User Registration...")
    await record_user(
        user_id=123456789,
        username="demo_client",
        first_name="John",
        last_name="Doe",
        is_admin=True
    )

    print("[3/5] Testing Lead Capture...")
    lead_id = await save_lead(
        user_id=123456789,
        username="demo_client",
        full_name="John Doe",
        email="john@example.com",
        phone="+1234567890",
        service="Web & App Development",
        budget="$1,500 - $5,000",
        notes="I need a custom e-commerce solution."
    )
    print(f" -> Lead saved with ID #{lead_id}")

    print("[4/5] Testing Status Update...")
    await update_lead_status(lead_id, "CONTACTED")
    leads = await get_recent_leads(limit=5)
    assert len(leads) >= 1
    assert leads[0]["status"] == "CONTACTED"
    print(f" -> Lead #{lead_id} status successfully updated to CONTACTED.")

    print("[5/5] Testing Stats & CSV Export...")
    stats = await get_lead_stats()
    print(f" -> Lead Stats: {stats}")

    csv_data = await export_leads_to_csv()
    csv_bytes = csv_data.getvalue()
    print(f" -> CSV Export generated ({len(csv_bytes)} bytes)")

    print("\n[SUCCESS] All database and logic tests passed!")

if __name__ == "__main__":
    asyncio.run(run_tests())
