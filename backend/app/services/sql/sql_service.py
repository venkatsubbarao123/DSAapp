"""SQL Practice and Curriculum Service.

Manages:
- SQL Problem catalog and schema delivery
- Sandboxed evaluation and execution via SQLSandbox
- Submission auditing and user progress recording
- Integration with XP and Gamification engines
"""

import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.sql_learning import SQLProblem, SQLSubmission
from backend.app.schemas.sql_learning import (
    RunSQLQueryResponse,
    SQLProblemDetail,
    SQLProblemSummary,
    SQLSubmissionSummary,
    SubmitSQLQueryResponse,
)
from backend.app.services.gamification.streak_service import StreakService
from backend.app.services.gamification.xp_service import XPService
from backend.app.services.sql.sql_sandbox import SQLSandbox

logger = logging.getLogger(__name__)


# Initial standard problems seed definition
DEFAULT_SQL_PROBLEMS = [
    {
        "title": "Top Performing Products",
        "slug": "top-performing-products",
        "difficulty": "EASY",
        "category": "AGGREGATIONS",
        "description": "Write an SQL query to find the product name and total revenue for each product sold. Order by total revenue descending.",
        "schema_ddl": """
            CREATE TABLE products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                price REAL NOT NULL
            );
            CREATE TABLE order_items (
                id INTEGER PRIMARY KEY,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products(id)
            );
        """,
        "seed_data_sql": """
            INSERT INTO products (id, name, price) VALUES
                (1, 'Laptop', 1000.0),
                (2, 'Mouse', 25.0),
                (3, 'Monitor', 200.0),
                (4, 'Keyboard', 75.0);
            INSERT INTO order_items (id, product_id, quantity) VALUES
                (1, 1, 2),
                (2, 2, 10),
                (3, 3, 5),
                (4, 1, 1),
                (5, 4, 4);
        """,
        "solution_sql": """
            SELECT p.name, SUM(p.price * oi.quantity) AS total_revenue
            FROM products p
            JOIN order_items oi ON p.id = oi.product_id
            GROUP BY p.id, p.name
            ORDER BY total_revenue DESC;
        """,
        "is_order_sensitive": True,
        "access_level": "FREE",
    },
    {
        "title": "Department Highest Salary",
        "slug": "department-highest-salary",
        "difficulty": "MEDIUM",
        "category": "JOINS",
        "description": "Write a query to find employees who have the highest salary in each department.",
        "schema_ddl": """
            CREATE TABLE departments (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            );
            CREATE TABLE employees (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                salary INTEGER NOT NULL,
                department_id INTEGER NOT NULL,
                FOREIGN KEY (department_id) REFERENCES departments(id)
            );
        """,
        "seed_data_sql": """
            INSERT INTO departments (id, name) VALUES (1, 'IT'), (2, 'Sales');
            INSERT INTO employees (id, name, salary, department_id) VALUES
                (1, 'Alice', 90000, 1),
                (2, 'Bob', 85000, 1),
                (3, 'Charlie', 90000, 1),
                (4, 'David', 70000, 2),
                (5, 'Eve', 80000, 2);
        """,
        "solution_sql": """
            SELECT d.name AS Department, e.name AS Employee, e.salary AS Salary
            FROM employees e
            JOIN departments d ON e.department_id = d.id
            WHERE (e.department_id, e.salary) IN (
                SELECT department_id, MAX(salary)
                FROM employees
                GROUP BY department_id
            );
        """,
        "is_order_sensitive": False,
        "access_level": "FREE",
    },
    {
        "title": "Running Monthly Active Users",
        "slug": "running-monthly-active-users",
        "difficulty": "HARD",
        "category": "WINDOW_FUNCTIONS",
        "description": "Calculate the cumulative count of total signups over time ordered by signup date.",
        "schema_ddl": """
            CREATE TABLE user_signups (
                user_id INTEGER PRIMARY KEY,
                signup_date TEXT NOT NULL
            );
        """,
        "seed_data_sql": """
            INSERT INTO user_signups (user_id, signup_date) VALUES
                (101, '2026-01-01'),
                (102, '2026-01-01'),
                (103, '2026-01-02'),
                (104, '2026-01-03'),
                (105, '2026-01-03'),
                (106, '2026-01-04');
        """,
        "solution_sql": """
            SELECT signup_date,
                   COUNT(user_id) AS daily_signups,
                   SUM(COUNT(user_id)) OVER (ORDER BY signup_date) AS running_total
            FROM user_signups
            GROUP BY signup_date
            ORDER BY signup_date;
        """,
        "is_order_sensitive": True,
        "access_level": "FREE",
    },
]


class SQLService:
    """Business service orchestrating SQL practice and execution."""

    @classmethod
    async def ensure_seed_problems(cls, db: AsyncSession) -> None:
        """Seeds standard SQL curriculum problems if table is empty."""
        stmt = select(func.count(SQLProblem.id))
        count = (await db.execute(stmt)).scalar() or 0
        if count == 0:
            for p_data in DEFAULT_SQL_PROBLEMS:
                problem = SQLProblem(**p_data)
                db.add(problem)
            await db.commit()
            logger.info("Seeded initial SQL problems.")

    @classmethod
    async def list_problems(
        cls,
        db: AsyncSession,
        user_id: str | None = None,
        category: str | None = None,
        difficulty: str | None = None,
    ) -> list[SQLProblemSummary]:
        """Lists published SQL problems with solved status indicator."""
        await cls.ensure_seed_problems(db)

        stmt = select(SQLProblem).where(SQLProblem.is_published.is_(True))
        if category:
            stmt = stmt.where(SQLProblem.category == category)
        if difficulty:
            stmt = stmt.where(SQLProblem.difficulty == difficulty)

        stmt = stmt.order_by(SQLProblem.difficulty, SQLProblem.title)
        res = await db.execute(stmt)
        problems: list[SQLProblem] = list(res.scalars().all())

        solved_problem_ids = set()
        if user_id:
            solved_stmt = (
                select(SQLSubmission.sql_problem_id)
                .where(
                    SQLSubmission.user_id == user_id,
                    SQLSubmission.verdict == "ACCEPTED",
                )
                .distinct()
            )
            s_res = await db.execute(solved_stmt)
            solved_problem_ids = {r[0] for r in s_res.all()}

        return [
            SQLProblemSummary(
                id=p.id,
                title=p.title,
                slug=p.slug,
                difficulty=p.difficulty,
                category=p.category,
                is_order_sensitive=p.is_order_sensitive,
                access_level=p.access_level,
                solved=(p.id in solved_problem_ids),
            )
            for p in problems
        ]

    @classmethod
    async def get_problem_by_slug_or_id(
        cls,
        db: AsyncSession,
        slug_or_id: str,
        user_id: str | None = None,
    ) -> SQLProblemDetail | None:
        """Retrieves SQL problem specification."""
        await cls.ensure_seed_problems(db)

        stmt = select(SQLProblem).where(
            (SQLProblem.slug == slug_or_id) | (SQLProblem.id == slug_or_id)
        )
        res = await db.execute(stmt)
        problem = res.scalars().first()
        if not problem:
            return None

        is_solved = False
        if user_id:
            s_stmt = select(func.count(SQLSubmission.id)).where(
                SQLSubmission.user_id == user_id,
                SQLSubmission.sql_problem_id == problem.id,
                SQLSubmission.verdict == "ACCEPTED",
            )
            is_solved = bool((await db.execute(s_stmt)).scalar() or 0)

        return SQLProblemDetail(
            id=problem.id,
            title=problem.title,
            slug=problem.slug,
            description=problem.description,
            difficulty=problem.difficulty,
            category=problem.category,
            schema_ddl=problem.schema_ddl,
            sample_data_sql=problem.seed_data_sql,
            is_order_sensitive=problem.is_order_sensitive,
            allowed_features=problem.allowed_features,
            access_level=problem.access_level,
            solved=is_solved,
        )

    @classmethod
    async def dry_run_query(
        cls,
        db: AsyncSession,
        slug_or_id: str,
        query: str,
    ) -> RunSQLQueryResponse:
        """Executes student query in dry-run mode against problem test schema."""
        problem = await cls.get_problem_by_slug_or_id(db, slug_or_id)
        if not problem:
            return RunSQLQueryResponse(
                verdict="SYSTEM_ERROR",
                execution_time_ms=0,
                error_message="Problem not found.",
            )

        res = await SQLSandbox.dry_run_query(
            schema_ddl=problem.schema_ddl,
            seed_data_sql=problem.sample_data_sql,
            user_query=query,
        )

        return RunSQLQueryResponse(
            verdict=res.verdict,
            execution_time_ms=res.execution_time_ms,
            columns=res.user_columns,
            rows=res.user_rows,
            error_message=res.error_message,
        )

    @classmethod
    async def submit_query(
        cls,
        db: AsyncSession,
        user_id: str,
        slug_or_id: str,
        query: str,
    ) -> SubmitSQLQueryResponse:
        """Evaluates student query against solution, records submission and rewards XP."""
        stmt = select(SQLProblem).where(
            (SQLProblem.slug == slug_or_id) | (SQLProblem.id == slug_or_id)
        )
        res = await db.execute(stmt)
        problem = res.scalars().first()
        if not problem:
            return SubmitSQLQueryResponse(
                submission_id="",
                verdict="SYSTEM_ERROR",
                execution_time_ms=0,
                error_message="Problem not found.",
            )

        sandbox_result = await SQLSandbox.evaluate_query(
            schema_ddl=problem.schema_ddl,
            seed_data_sql=problem.seed_data_sql,
            solution_sql=problem.solution_sql,
            user_query=query,
            is_order_sensitive=problem.is_order_sensitive,
            timeout_seconds=problem.time_limit_seconds,
        )

        # Record submission
        submission = SQLSubmission(
            user_id=user_id,
            sql_problem_id=problem.id,
            query=query,
            verdict=sandbox_result.verdict,
            execution_time_ms=sandbox_result.execution_time_ms,
            error_message=sandbox_result.error_message,
        )
        db.add(submission)
        await db.commit()

        # If ACCEPTED: award XP and record streak
        if sandbox_result.verdict == "ACCEPTED":
            try:
                await XPService.record_xp_event(
                    db=db,
                    user_id=user_id,
                    event_type="SQL_PROBLEM_SOLVE",
                    source_id=f"sql:{problem.id}",
                    amount=50,
                    metadata={"sql_problem_id": problem.id, "title": problem.title},
                )
                await StreakService.record_activity(db=db, user_id=user_id)
                await db.commit()
            except Exception as e:
                logger.warning(f"Could not award XP for SQL solve: {e}")

        return SubmitSQLQueryResponse(
            submission_id=submission.id,
            verdict=sandbox_result.verdict,
            execution_time_ms=sandbox_result.execution_time_ms,
            columns=sandbox_result.user_columns,
            rows=sandbox_result.user_rows,
            expected_columns=sandbox_result.expected_columns,
            expected_rows_sample=sandbox_result.expected_rows_sample,
            error_message=sandbox_result.error_message,
        )

    @classmethod
    async def list_user_submissions(
        cls,
        db: AsyncSession,
        user_id: str,
        slug_or_id: str,
    ) -> list[SQLSubmissionSummary]:
        """Lists user's submission history for a specific SQL problem."""
        stmt = select(SQLProblem.id).where(
            (SQLProblem.slug == slug_or_id) | (SQLProblem.id == slug_or_id)
        )
        prob_id = (await db.execute(stmt)).scalar()
        if not prob_id:
            return []

        sub_stmt = (
            select(SQLSubmission)
            .where(
                SQLSubmission.user_id == user_id,
                SQLSubmission.sql_problem_id == prob_id,
            )
            .order_by(SQLSubmission.created_at.desc())
            .limit(20)
        )

        res = await db.execute(sub_stmt)
        submissions: list[SQLSubmission] = list(res.scalars().all())

        return [
            SQLSubmissionSummary(
                id=s.id,
                query=s.query,
                verdict=s.verdict,
                execution_time_ms=s.execution_time_ms,
                error_message=s.error_message,
                created_at=s.created_at,
            )
            for s in submissions
        ]
