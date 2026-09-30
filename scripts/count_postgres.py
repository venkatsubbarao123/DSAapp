import asyncio
import asyncpg

async def count_all():
    conn = await asyncpg.connect('postgresql://dsaapp_user:DsaAppLocal2026Secure@localhost:5432/dsaapp')
    tables = [
        'curricula', 'tracks', 'topics', 'subtopics', 'lessons',
        'problems', 'test_cases', 'problem_hints', 'problem_examples',
        'patterns', 'tags', 'sql_problems', 'achievements', 'contests', 'users'
    ]
    for t in tables:
        count = await conn.fetchval(f"SELECT COUNT(*) FROM {t}")
        print(f"{t}: {count}")
    await conn.close()

if __name__ == '__main__':
    asyncio.run(count_all())
