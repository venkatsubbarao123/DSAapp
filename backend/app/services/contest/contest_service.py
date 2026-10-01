"""Contest Management, Scoring, and Anti-Cheat Service.

Implements:
- Server-authoritative contest lifecycle and timer calculation
- Participant registration with entitlement validation
- Submission routing to Phase 5 Judge and contest scoring
- Real-time and final contest scoreboard with deterministic ranking
- Application-level anti-cheat signal detection and audit logging
"""

import json
import logging
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.contest import (
    Contest,
    ContestCheatSignal,
    ContestParticipant,
    ContestProblem,
    ContestStatus,
    ContestSubmission,
)
from backend.app.models.progress import Submission, SubmissionStatus
from backend.app.models.user import User
from backend.app.schemas.contest import (
    ContestDetailResponse,
    ContestLeaderboardEntry,
    ContestLeaderboardResponse,
    ContestProblemResponse,
    ContestSubmitRequest,
    ContestSubmitResponse,
    ContestSummaryResponse,
    ProblemResultDetail,
    UserContestHistoryEntry,
)
from backend.app.schemas.progress import SubmissionCreate
from backend.app.services.progress_service import ProgressService
from backend.app.services.redis import redis_service

logger = logging.getLogger(__name__)


class ContestService:
    """Core domain service for Contests."""

    @classmethod
    async def list_contests(
        cls,
        db: AsyncSession,
        status_filter: str | None = None,
    ) -> list[ContestSummaryResponse]:
        """Lists contests with computed server-authoritative status and participant counts."""
        stmt = select(Contest).order_by(Contest.start_at.desc())
        res = await db.execute(stmt)
        contests = res.scalars().all()

        summaries = []
        for c in contests:
            dynamic_status = c.compute_dynamic_status().value
            if status_filter and dynamic_status != status_filter:
                continue

            # Count participants
            p_stmt = select(func.count(ContestParticipant.id)).where(
                ContestParticipant.contest_id == c.id
            )
            p_count = (await db.execute(p_stmt)).scalar() or 0

            summaries.append(
                ContestSummaryResponse(
                    id=c.id,
                    title=c.title,
                    slug=c.slug,
                    description=c.description,
                    status=dynamic_status,
                    start_at=c.start_at,
                    end_at=c.end_at,
                    duration_seconds=c.duration_seconds,
                    remaining_seconds=c.remaining_seconds,
                    visibility=c.visibility,
                    premium_required=c.premium_required,
                    participant_count=p_count,
                )
            )
        return summaries

    @classmethod
    async def get_contest_detail(
        cls,
        db: AsyncSession,
        slug_or_id: str,
        user_id: str | None = None,
    ) -> ContestDetailResponse | None:
        """Retrieves full contest details including problem status for authenticated user."""
        stmt = (
            select(Contest)
            .where((Contest.slug == slug_or_id) | (Contest.id == slug_or_id))
            .options(
                selectinload(Contest.problems).selectinload(ContestProblem.problem)
            )
        )
        res = await db.execute(stmt)
        contest = res.scalars().first()
        if not contest:
            return None

        dynamic_status = contest.compute_dynamic_status().value

        # Count participants
        p_stmt = select(func.count(ContestParticipant.id)).where(
            ContestParticipant.contest_id == contest.id
        )
        p_count = (await db.execute(p_stmt)).scalar() or 0

        is_registered = False
        my_score = 0
        my_penalty = 0
        my_rank = None
        participant: ContestParticipant | None = None

        if user_id:
            part_stmt = select(ContestParticipant).where(
                ContestParticipant.contest_id == contest.id,
                ContestParticipant.user_id == user_id,
            )
            participant = (await db.execute(part_stmt)).scalars().first()
            if participant:
                is_registered = True
                my_score = participant.final_score
                my_penalty = participant.final_penalty
                my_rank = participant.final_rank

        # Problems overview
        problem_responses: list[ContestProblemResponse] = []
        for cp in contest.problems:
            solved = False
            wrong_attempts = 0

            if participant:
                # Check user's submissions for this problem
                sub_stmt = (
                    select(ContestSubmission)
                    .where(
                        ContestSubmission.contest_id == contest.id,
                        ContestSubmission.participant_id == participant.id,
                        ContestSubmission.problem_id == cp.problem_id,
                    )
                    .order_by(ContestSubmission.submitted_at.asc())
                )
                c_subs = (await db.execute(sub_stmt)).scalars().all()

                for cs in c_subs:
                    if cs.verdict == "ACCEPTED":
                        solved = True
                        break
                    else:
                        wrong_attempts += 1

            problem_responses.append(
                ContestProblemResponse(
                    id=cp.id,
                    problem_id=cp.problem_id,
                    title=cp.problem.title if cp.problem else "Contest Problem",
                    slug=cp.problem.slug if cp.problem else "",
                    sequence=cp.sequence,
                    points=cp.points,
                    penalty_minutes=cp.penalty_minutes,
                    difficulty=cp.difficulty,
                    solved=solved,
                    wrong_attempts=wrong_attempts,
                )
            )

        return ContestDetailResponse(
            id=contest.id,
            title=contest.title,
            slug=contest.slug,
            description=contest.description,
            status=dynamic_status,
            start_at=contest.start_at,
            end_at=contest.end_at,
            duration_seconds=contest.duration_seconds,
            remaining_seconds=contest.remaining_seconds,
            visibility=contest.visibility,
            premium_required=contest.premium_required,
            is_registered=is_registered,
            participant_count=p_count,
            my_score=my_score,
            my_penalty=my_penalty,
            my_rank=my_rank,
            problems=problem_responses,
        )

    @classmethod
    async def join_contest(
        cls,
        db: AsyncSession,
        slug_or_id: str,
        user: User,
    ) -> tuple[bool, str]:
        """Registers a user for a contest."""
        stmt = select(Contest).where(
            (Contest.slug == slug_or_id) | (Contest.id == slug_or_id)
        )
        res = await db.execute(stmt)
        contest = res.scalars().first()
        if not contest:
            return False, "Contest not found."

        dynamic_status = contest.compute_dynamic_status()
        if dynamic_status == ContestStatus.ENDED:
            return False, "Cannot join a contest that has already ended."
        if (
            dynamic_status == ContestStatus.ARCHIVED
            or dynamic_status == ContestStatus.DRAFT
        ):
            return (
                False,
                f"Contest is not open for registration ({dynamic_status.value}).",
            )

        # Check premium requirement
        if contest.premium_required and not getattr(user, "is_premium", False):
            return False, "This contest requires an active Pro subscription."

        # Check already joined
        part_stmt = select(ContestParticipant).where(
            ContestParticipant.contest_id == contest.id,
            ContestParticipant.user_id == user.id,
        )
        existing = (await db.execute(part_stmt)).scalars().first()
        if existing:
            return True, "Already registered for this contest."

        participant = ContestParticipant(
            contest_id=contest.id,
            user_id=user.id,
        )
        db.add(participant)
        await db.commit()
        return True, "Successfully joined contest."

    @classmethod
    async def submit_solution(
        cls,
        db: AsyncSession,
        slug_or_id: str,
        user: User,
        payload: ContestSubmitRequest,
        progress_service: ProgressService,
    ) -> tuple[ContestSubmitResponse | None, str | None]:
        """Validates submission timing, runs anti-cheat checks, queues code via Judge, and links contest submission."""
        stmt = select(Contest).where(
            (Contest.slug == slug_or_id) | (Contest.id == slug_or_id)
        )
        contest = (await db.execute(stmt)).scalars().first()
        if not contest:
            return None, "Contest not found."

        # 1. Server-authoritative timing check: contest MUST be LIVE
        dynamic_status = contest.compute_dynamic_status()
        if dynamic_status != ContestStatus.LIVE:
            return (
                None,
                f"Submissions are only accepted while contest is LIVE. Current status: {dynamic_status.value}.",
            )

        # 2. Check participant registration
        part_stmt = select(ContestParticipant).where(
            ContestParticipant.contest_id == contest.id,
            ContestParticipant.user_id == user.id,
        )
        participant = (await db.execute(part_stmt)).scalars().first()
        if not participant:
            return None, "You must register for this contest before submitting code."

        # 3. Check problem is in contest
        prob_stmt = select(ContestProblem).where(
            ContestProblem.contest_id == contest.id,
            (ContestProblem.problem_id == payload.problem_id)
            | (ContestProblem.id == payload.problem_id),
        )
        contest_prob = (await db.execute(prob_stmt)).scalars().first()
        if not contest_prob:
            # Check problem slug or id
            actual_prob = await progress_service.content_repo.get_problem_by_slug_or_id(
                payload.problem_id
            )
            if actual_prob:
                prob_stmt2 = select(ContestProblem).where(
                    ContestProblem.contest_id == contest.id,
                    ContestProblem.problem_id == actual_prob.id,
                )
                contest_prob = (await db.execute(prob_stmt2)).scalars().first()

        if not contest_prob:
            return None, "Problem is not part of this contest."

        resolved_problem_id = contest_prob.problem_id

        # 4. Anti-Cheat: Rapid submission check (< 5 seconds since last submission)
        now_utc = datetime.now(timezone.utc)
        recent_sub_stmt = (
            select(ContestSubmission)
            .where(
                ContestSubmission.contest_id == contest.id,
                ContestSubmission.participant_id == participant.id,
            )
            .order_by(ContestSubmission.submitted_at.desc())
            .limit(1)
        )
        last_sub = (await db.execute(recent_sub_stmt)).scalars().first()

        if last_sub:
            last_dt = (
                last_sub.submitted_at
                if last_sub.submitted_at.tzinfo
                else last_sub.submitted_at.replace(tzinfo=timezone.utc)
            )
            gap_seconds = (now_utc - last_dt).total_seconds()
            if gap_seconds < 5.0:
                cheat_sig = ContestCheatSignal(
                    contest_id=contest.id,
                    user_id=user.id,
                    signal_type="RAPID_SUBMISSIONS",
                    details_json={
                        "gap_seconds": gap_seconds,
                        "problem_id": resolved_problem_id,
                    },
                )
                db.add(cheat_sig)
                await db.commit()
                return (
                    None,
                    "Rate limit: Please wait at least 5 seconds between contest submissions.",
                )

        # 5. Anti-Cheat: Repeated identical source code check
        recent_identical_stmt = (
            select(Submission)
            .join(ContestSubmission, ContestSubmission.submission_id == Submission.id)
            .where(
                ContestSubmission.contest_id == contest.id,
                Submission.user_id == user.id,
                Submission.problem_id == resolved_problem_id,
                Submission.source_code == payload.source_code,
            )
        )
        identical_sub = (await db.execute(recent_identical_stmt)).scalars().first()
        if identical_sub:
            cheat_sig = ContestCheatSignal(
                contest_id=contest.id,
                user_id=user.id,
                signal_type="REPEATED_IDENTICAL_CODE",
                details_json={"problem_id": resolved_problem_id},
            )
            db.add(cheat_sig)

        # 6. Create standard Submission through ProgressService (enqueues in JudgeQueue for Docker sandbox)
        submission_create = SubmissionCreate(
            problem_id=resolved_problem_id,
            language=payload.language,
            source_code=payload.source_code,
            idempotency_key=payload.idempotency_key,
        )
        submission_detail = await progress_service.create_submission(
            user.id, submission_create
        )

        # 7. Create ContestSubmission link
        c_sub = ContestSubmission(
            contest_id=contest.id,
            participant_id=participant.id,
            problem_id=resolved_problem_id,
            submission_id=submission_detail.id,
            verdict="QUEUED",
            score=0,
            penalty=0,
        )
        db.add(c_sub)
        participant.last_activity_at = now_utc
        await db.commit()

        # Invalidate cached leaderboard
        cache_key = f"contest:leaderboard:{contest.id}"
        await redis_service.delete(cache_key)

        return ContestSubmitResponse(
            submission_id=submission_detail.id,
            contest_submission_id=c_sub.id,
            verdict="QUEUED",
            score=0,
            penalty=0,
            message="Submission enqueued for online judging.",
        ), None

    @classmethod
    async def get_leaderboard(
        cls,
        db: AsyncSession,
        slug_or_id: str,
    ) -> ContestLeaderboardResponse | None:
        """Calculates live contest scoreboard with deterministic ranking and Redis caching."""
        stmt = (
            select(Contest)
            .where((Contest.slug == slug_or_id) | (Contest.id == slug_or_id))
            .options(
                selectinload(Contest.problems),
                selectinload(Contest.participants).selectinload(
                    ContestParticipant.user
                ),
            )
        )
        contest = (await db.execute(stmt)).scalars().first()
        if not contest:
            return None

        cache_key = f"contest:leaderboard:{contest.id}"
        cached = await redis_service.get(cache_key)
        if cached:
            try:
                data = json.loads(cached)
                return ContestLeaderboardResponse(**data)
            except Exception:
                pass

        # Load all contest submissions with Judge results
        sub_stmt = (
            select(ContestSubmission, Submission.status)
            .join(Submission, ContestSubmission.submission_id == Submission.id)
            .where(ContestSubmission.contest_id == contest.id)
            .order_by(ContestSubmission.submitted_at.asc())
        )
        sub_results = (await db.execute(sub_stmt)).all()

        # Group submissions by (participant_id, problem_id)
        # item: { participant_id: { problem_id: [ (submitted_at, status) ] } }
        part_subs: dict[str, dict[str, list]] = {}
        for cs, status in sub_results:
            pid = cs.participant_id
            prob_id = cs.problem_id
            if pid not in part_subs:
                part_subs[pid] = {}
            if prob_id not in part_subs[pid]:
                part_subs[pid][prob_id] = []
            part_subs[pid][prob_id].append((cs.submitted_at, status))

        # Problems dictionary by id
        prob_dict = {cp.problem_id: cp for cp in contest.problems}

        # Calculate scores per participant
        raw_leaderboard = []

        for p in contest.participants:
            total_score = 0
            total_penalty = 0
            solved_count = 0
            last_accepted_time = None
            problem_results_map: dict[str, ProblemResultDetail] = {}

            p_submissions = part_subs.get(p.id, {})

            for prob_id, cp in prob_dict.items():
                attempts = p_submissions.get(prob_id, [])
                is_solved = False
                wrong_attempts = 0
                acc_time_min = None

                for sub_time, status in attempts:
                    if status == SubmissionStatus.ACCEPTED:
                        is_solved = True
                        sub_dt = (
                            sub_time
                            if sub_time.tzinfo
                            else sub_time.replace(tzinfo=timezone.utc)
                        )
                        c_start = (
                            contest.start_at
                            if contest.start_at.tzinfo
                            else contest.start_at.replace(tzinfo=timezone.utc)
                        )
                        diff_sec = max(0, (sub_dt - c_start).total_seconds())
                        acc_time_min = int(diff_sec / 60)
                        last_accepted_time = max(last_accepted_time or sub_dt, sub_dt)
                        break
                    else:
                        wrong_attempts += 1

                pts = cp.points if is_solved else 0
                problem_penalty = (
                    (acc_time_min + wrong_attempts * cp.penalty_minutes)
                    if is_solved
                    else 0
                )

                if is_solved:
                    total_score += pts
                    total_penalty += problem_penalty
                    solved_count += 1

                problem_results_map[prob_id] = ProblemResultDetail(
                    solved=is_solved,
                    wrong_attempts=wrong_attempts,
                    time_minutes=acc_time_min,
                    points=pts,
                )

            # Privacy-safe username
            display_name = f"User_{p.user_id[:6]}"
            if p.user and hasattr(p.user, "email") and p.user.email:
                display_name = p.user.email.split("@")[0]

            raw_leaderboard.append(
                {
                    "participant_id": p.id,
                    "display_name": display_name,
                    "user_id": p.user_id,
                    "score": total_score,
                    "penalty": total_penalty,
                    "problems_solved": solved_count,
                    "last_accepted_time": last_accepted_time
                    or datetime.max.replace(tzinfo=timezone.utc),
                    "problem_results": problem_results_map,
                }
            )

        # Deterministic Ranking Sort:
        # 1. Score DESC (higher score wins)
        # 2. Penalty ASC (lower penalty wins)
        # 3. Last Accepted Time ASC (earlier solve wins)
        # 4. user_id ASC (deterministic tie-break)
        raw_leaderboard.sort(
            key=lambda x: (
                -x["score"],
                x["penalty"],
                x["last_accepted_time"],
                x["user_id"],
            )
        )

        entries = []
        for rank, entry in enumerate(raw_leaderboard, start=1):
            entries.append(
                ContestLeaderboardEntry(
                    rank=rank,
                    display_name=entry["display_name"],
                    score=entry["score"],
                    penalty=entry["penalty"],
                    problems_solved=entry["problems_solved"],
                    problem_results=entry["problem_results"],
                )
            )

        resp = ContestLeaderboardResponse(
            contest_id=contest.id,
            contest_title=contest.title,
            status=contest.compute_dynamic_status().value,
            total_participants=len(contest.participants),
            entries=entries,
        )

        # Cache in Redis with 15s TTL during live contests, 300s when ended
        ttl = 15 if contest.compute_dynamic_status() == ContestStatus.LIVE else 300
        try:
            await redis_service.set(cache_key, resp.model_dump_json(), ttl=ttl)
        except Exception:
            pass

        return resp

    @classmethod
    async def get_user_history(
        cls,
        db: AsyncSession,
        user_id: str,
    ) -> list[UserContestHistoryEntry]:
        """Returns contest participation history for the authenticated user."""
        stmt = (
            select(ContestParticipant)
            .join(Contest, ContestParticipant.contest_id == Contest.id)
            .where(ContestParticipant.user_id == user_id)
            .options(selectinload(ContestParticipant.contest))
            .order_by(Contest.start_at.desc())
        )
        res = await db.execute(stmt)
        participants = res.scalars().all()

        history = []
        for p in participants:
            c = p.contest
            p_stmt = select(func.count(ContestParticipant.id)).where(
                ContestParticipant.contest_id == c.id
            )
            p_count = (await db.execute(p_stmt)).scalar() or 0

            history.append(
                UserContestHistoryEntry(
                    contest_id=c.id,
                    contest_title=c.title,
                    contest_slug=c.slug,
                    start_at=c.start_at,
                    end_at=c.end_at,
                    joined_at=p.joined_at,
                    final_score=p.final_score,
                    final_penalty=p.final_penalty,
                    final_rank=p.final_rank,
                    total_participants=p_count,
                )
            )
        return history
