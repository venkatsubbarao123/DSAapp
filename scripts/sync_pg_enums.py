import asyncio
from backend.app.db.session import async_session_factory
from backend.app.models.progress import SubmissionStatus, ProblemProgressStatus, MistakeType, ReviewOutcome
from backend.app.models.user import UserRole
from backend.app.models.content import ContentStatus, ContentLevel, ContentAccessLevel, ProblemDifficulty
from sqlalchemy import text

ALL_ENUMS = {
    'submissionstatus': [e.value for e in SubmissionStatus],
    'problemprogressstatus': [e.value for e in ProblemProgressStatus],
    'mistaketype': [e.value for e in MistakeType],
    'reviewoutcome': [e.value for e in ReviewOutcome],
    'userrole': [e.value for e in UserRole],
    'contentstatus': [e.value for e in ContentStatus],
    'contentlevel': [e.value for e in ContentLevel],
    'contentaccesslevel': [e.value for e in ContentAccessLevel],
    'problemdifficulty': [e.value for e in ProblemDifficulty],
}

async def main():
    async with async_session_factory() as s:
        for enum_name, expected_vals in ALL_ENUMS.items():
            r = await s.execute(text(f"SELECT enumlabel FROM pg_enum JOIN pg_type ON pg_enum.enumtypid = pg_type.oid WHERE typname = '{enum_name}';"))
            existing = {x[0] for x in r.all()}
            if not existing:
                print(f"Enum type {enum_name} not found in pg_type (varchar or not in pg)")
                continue
            missing = [v for v in expected_vals if v not in existing]
            print(f"{enum_name}: existing={len(existing)}, missing={missing}")
            for m in missing:
                print(f"Adding value '{m}' to enum {enum_name}...")
                await s.execute(text(f"ALTER TYPE {enum_name} ADD VALUE '{m}';"))
                await s.commit()

        print("All enums verified and synchronized successfully!")

if __name__ == '__main__':
    asyncio.run(main())
