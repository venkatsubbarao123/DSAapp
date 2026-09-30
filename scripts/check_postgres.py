import asyncio
import asyncpg

async def check():
    conn = await asyncpg.connect('postgresql://dsaapp_user:DsaAppLocal2026Secure@localhost:5432/dsaapp')
    tables = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    print('Tables in Postgres dsaapp:', [t['table_name'] for t in tables])
    try:
        rev = await conn.fetchval('SELECT version_num FROM alembic_version')
        print('Alembic revision:', rev)
    except Exception as e:
        print('No alembic_version table yet:', e)
    await conn.close()

if __name__ == '__main__':
    asyncio.run(check())
