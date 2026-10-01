import asyncio
from sqlalchemy import text
from backend.app.db.session import engine

async def main():
    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT count(*) FROM information_schema.tables WHERE table_schema='public'")
        )
        print("Public tables:", result.scalar())

    await engine.dispose()

asyncio.run(main())