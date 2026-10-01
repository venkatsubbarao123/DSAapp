"""Idempotent seed data for local development and test verification.

Clearly identified as DEVELOPMENT SEED DATA.
"""

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.content import (
    ContentAccessLevel,
    ContentLevel,
    ContentStatus,
    Curriculum,
    Hint,
    Lesson,
    Problem,
    ProblemDifficulty,
    ProblemExample,
    ProblemPattern,
    Subtopic,
    Tag,
    TestCase,
    Topic,
    Track,
)


async def seed_development_content(session: AsyncSession) -> None:
    """Populates a minimal, verified educational dataset for testing."""
    # Check if already seeded
    existing_curr = await session.execute(
        select(Curriculum).where(Curriculum.slug == "core-dsa-seed")
    )
    if existing_curr.scalar_one_or_none():
        return  # Already seeded

    # 1. Create Curriculum
    curriculum = Curriculum(
        slug="core-dsa-seed",
        title="Core Data Structures & Algorithms (Dev Seed)",
        short_description="Foundational algorithmic concepts engineered for software engineers.",
        description="Comprehensive study of fundamental data structures, memory layouts, time/space complexity analysis, and algorithmic patterns.",
        level=ContentLevel.BEGINNER,
        status=ContentStatus.PUBLISHED,
        display_order=1,
        is_free=True,
    )
    session.add(curriculum)
    await session.flush()

    # 2. Create Track
    track = Track(
        curriculum_id=curriculum.id,
        slug="foundations-patterns-seed",
        title="Foundations & Algorithmic Patterns",
        description="Master sequential data structures and essential two-pointer & sliding-window problem patterns.",
        level=ContentLevel.BEGINNER,
        display_order=1,
        status=ContentStatus.PUBLISHED,
        access_level=ContentAccessLevel.FREE,
    )
    session.add(track)
    await session.flush()

    # 3. Create Topics
    topic_arrays = Topic(
        track_id=track.id,
        slug="arrays-seed",
        title="Arrays & Two Pointers (Seed)",
        description="Array memory allocation, cache locality, amortized array resizing, and two-pointer traversal.",
        display_order=1,
        difficulty=ContentLevel.BEGINNER,
        access_level=ContentAccessLevel.FREE,
        status=ContentStatus.PUBLISHED,
    )
    topic_sliding = Topic(
        track_id=track.id,
        slug="sliding-window-seed",
        title="Sliding Window Techniques (Seed)",
        description="Continuous range tracking, fixed-size vs dynamic-size window boundaries, and state frequency maps.",
        display_order=2,
        difficulty=ContentLevel.INTERMEDIATE,
        access_level=ContentAccessLevel.FREE,
        status=ContentStatus.PUBLISHED,
    )
    session.add_all([topic_arrays, topic_sliding])
    await session.flush()

    # 4. Create Subtopics
    subtopic_arrays = Subtopic(
        topic_id=topic_arrays.id,
        slug="array-manipulation-seed",
        title="Array Manipulation & Two Pointers",
        description="Working with indexed sequences and in-place transformations.",
        display_order=1,
        difficulty=ContentLevel.BEGINNER,
        access_level=ContentAccessLevel.FREE,
        status=ContentStatus.PUBLISHED,
    )
    subtopic_sliding = Subtopic(
        topic_id=topic_sliding.id,
        slug="variable-sliding-window-seed",
        title="Dynamic Sliding Window",
        description="Expanding right and contracting left pointers to satisfy constraints.",
        display_order=1,
        difficulty=ContentLevel.INTERMEDIATE,
        access_level=ContentAccessLevel.FREE,
        status=ContentStatus.PUBLISHED,
    )
    session.add_all([subtopic_arrays, subtopic_sliding])
    await session.flush()

    # 5. Create Lessons with Structured Blocks
    lesson_array_blocks = [
        {"type": "heading", "level": 1, "content": "Understanding Dynamic Arrays"},
        {
            "type": "paragraph",
            "content": "A dynamic array represents a contiguous block of memory that automatically resizes when capacity is exceeded. In Python this is a list, in Java an ArrayList, and in C++ a std::vector.",
        },
        {
            "type": "code",
            "language": "python",
            "content": "# Amortized append operation demonstration\nitems = []\nfor i in range(10):\n    items.append(i)\n    # When capacity doubles, amortized complexity remains O(1)\n",
        },
        {
            "type": "note",
            "content": "Appending an element takes O(1) amortized time, though occasional O(N) array reallocation occurs.",
        },
    ]

    lesson_array = Lesson(
        subtopic_id=subtopic_arrays.id,
        slug="dynamic-arrays-seed",
        title="Dynamic Arrays & Amortized Complexity",
        summary="Deep dive into array memory layouts, pointer arithmetic, and amortized complexity guarantees.",
        content_json=json.dumps(lesson_array_blocks),
        estimated_minutes=15,
        difficulty=ContentLevel.BEGINNER,
        display_order=1,
        access_level=ContentAccessLevel.FREE,
        status=ContentStatus.PUBLISHED,
        version=1,
    )

    lesson_sliding_blocks = [
        {"type": "heading", "level": 1, "content": "The Sliding Window Pattern"},
        {
            "type": "paragraph",
            "content": "The sliding window pattern converts nested loops into a linear scan by tracking an active range [left, right] that expands and contracts.",
        },
        {
            "type": "code",
            "language": "python",
            "content": "def sliding_window_template(arr, k):\n    left = 0\n    curr_sum = 0\n    best = 0\n    for right in range(len(arr)):\n        curr_sum += arr[right]\n        while curr_sum > k and left <= right:\n            curr_sum -= arr[left]\n            left += 1\n        best = max(best, right - left + 1)\n    return best\n",
        },
        {
            "type": "tip",
            "content": "Always identify the condition that triggers the window contraction loop.",
        },
    ]

    lesson_sliding = Lesson(
        subtopic_id=subtopic_sliding.id,
        slug="sliding-window-template-seed",
        title="The Sliding Window Mental Model",
        summary="Systematic approach to converting quadratic nested substring problems into linear time solutions.",
        content_json=json.dumps(lesson_sliding_blocks),
        estimated_minutes=20,
        difficulty=ContentLevel.INTERMEDIATE,
        display_order=1,
        access_level=ContentAccessLevel.PREMIUM,  # Premium Lesson for testing gates!
        status=ContentStatus.PUBLISHED,
        version=1,
    )
    session.add_all([lesson_array, lesson_sliding])
    await session.flush()

    # 6. Tags and Patterns
    tag_array = Tag(slug="array", name="Array")
    tag_hash = Tag(slug="hash-table", name="Hash Table")
    tag_string = Tag(slug="string", name="String")
    tag_greedy = Tag(slug="greedy", name="Greedy")
    session.add_all([tag_array, tag_hash, tag_string, tag_greedy])
    await session.flush()

    pattern_two_pointer = ProblemPattern(
        slug="two-pointers",
        name="Two Pointers",
        description="Linear scanning using two synchronized pointer indexes.",
    )
    pattern_sliding = ProblemPattern(
        slug="sliding-window",
        name="Sliding Window",
        description="Dynamic range subset tracking to find optimal subsegments.",
    )
    session.add_all([pattern_two_pointer, pattern_sliding])
    await session.flush()

    # 7. Problem 1: Two Sum (EASY, FREE)
    p1 = Problem(
        slug="two-sum-seed",
        title="Two Sum (Dev Seed)",
        statement="Given an array of integers `nums` and an integer `target`, return indices of the two numbers such that they add up to `target`.\n\nYou may assume that each input would have exactly one solution, and you may not use the same element twice.",
        explanation="Use a hash map to record the complement `target - num` observed during a single pass.",
        difficulty=ProblemDifficulty.EASY,
        access_level=ContentAccessLevel.FREE,
        status=ContentStatus.PUBLISHED,
        topic_id=topic_arrays.id,
        subtopic_id=subtopic_arrays.id,
        display_order=1,
        estimated_minutes=15,
        input_format="nums: List[int], target: int",
        output_format="List[int] (indices of the two numbers)",
        constraints="2 <= nums.length <= 10^4\n-10^9 <= nums[i] <= 10^9\n-10^9 <= target <= 10^9",
        expected_time_complexity="O(N)",
        expected_space_complexity="O(N)",
        supported_languages='["python", "java", "cpp", "javascript"]',
        version=1,
    )
    p1.tags.extend([tag_array, tag_hash])
    p1.patterns.append(pattern_two_pointer)
    session.add(p1)
    await session.flush()

    # Examples, Hints, and Test Cases for Problem 1
    p1_ex = ProblemExample(
        problem_id=p1.id,
        input="nums = [2,7,11,15], target = 9",
        output="[0,1]",
        explanation="Because nums[0] + nums[1] == 9, we return [0, 1].",
        display_order=1,
    )
    p1_hint1 = Hint(
        problem_id=p1.id,
        hint_number=1,
        title="Check Complements",
        content="For each number x, what number would you need to add to it to reach target?",
        is_premium=False,
    )
    p1_hint2 = Hint(
        problem_id=p1.id,
        hint_number=2,
        title="Lookup Speed",
        content="Can you look up whether that complement exists in O(1) time using a dictionary or hash map?",
        is_premium=False,
    )
    p1_tc_sample = TestCase(
        problem_id=p1.id,
        input="[2, 7, 11, 15]\n9",
        expected_output="[0, 1]",
        is_sample=True,
        display_order=1,
        is_hidden=False,
    )
    p1_tc_hidden = TestCase(
        problem_id=p1.id,
        input="[3, 2, 4]\n6",
        expected_output="[1, 2]",
        is_sample=False,
        display_order=2,
        is_hidden=True,  # Hidden test case!
    )
    session.add_all([p1_ex, p1_hint1, p1_hint2, p1_tc_sample, p1_tc_hidden])

    # 8. Problem 2: Best Time to Buy and Sell Stock (EASY, FREE)
    p2 = Problem(
        slug="best-time-to-buy-and-sell-stock-seed",
        title="Best Time to Buy and Sell Stock (Dev Seed)",
        statement="You are given an array `prices` where `prices[i]` is the price of a given stock on the `i`th day.\n\nYou want to maximize your profit by choosing a single day to buy one stock and choosing a different day in the future to sell that stock.\n\nReturn the maximum profit you can achieve from this transaction. If you cannot achieve any profit, return `0`.",
        explanation="Track the minimum price seen so far as you iterate through the array, updating the maximum profit possible.",
        difficulty=ProblemDifficulty.EASY,
        access_level=ContentAccessLevel.FREE,
        status=ContentStatus.PUBLISHED,
        topic_id=topic_arrays.id,
        subtopic_id=subtopic_arrays.id,
        display_order=2,
        estimated_minutes=20,
        input_format="prices: List[int]",
        output_format="int (maximum profit)",
        constraints="1 <= prices.length <= 10^5\n0 <= prices[i] <= 10^4",
        expected_time_complexity="O(N)",
        expected_space_complexity="O(1)",
        supported_languages='["python", "java", "cpp", "javascript"]',
        version=1,
    )
    p2.tags.extend([tag_array, tag_greedy])
    session.add(p2)
    await session.flush()

    p2_ex = ProblemExample(
        problem_id=p2.id,
        input="prices = [7,1,5,3,6,4]",
        output="5",
        explanation="Buy on day 2 (price = 1) and sell on day 5 (price = 6), profit = 6-1 = 5.",
        display_order=1,
    )
    p2_tc = TestCase(
        problem_id=p2.id,
        input="[7, 1, 5, 3, 6, 4]",
        expected_output="5",
        is_sample=True,
        display_order=1,
        is_hidden=False,
    )
    session.add_all([p2_ex, p2_tc])

    # 9. Problem 3: Longest Substring Without Repeating Characters (MEDIUM, PREMIUM)
    p3 = Problem(
        slug="longest-substring-without-repeating-characters-seed",
        title="Longest Substring Without Repeating Characters (Dev Seed)",
        statement="Given a string `s`, find the length of the longest substring without duplicate characters.",
        explanation="Use a sliding window with a character index map to record the last seen position of each character.",
        difficulty=ProblemDifficulty.MEDIUM,
        access_level=ContentAccessLevel.PREMIUM,  # Gated by Premium!
        status=ContentStatus.PUBLISHED,
        topic_id=topic_sliding.id,
        subtopic_id=subtopic_sliding.id,
        display_order=1,
        estimated_minutes=30,
        input_format="s: str",
        output_format="int (length of longest substring)",
        constraints="0 <= s.length <= 5 * 10^4\ns consists of English letters, digits, symbols and spaces.",
        expected_time_complexity="O(N)",
        expected_space_complexity="O(min(N, M))",
        supported_languages='["python", "java", "cpp", "javascript"]',
        version=1,
    )
    p3.tags.extend([tag_string, tag_hash])
    p3.patterns.append(pattern_sliding)
    session.add(p3)
    await session.flush()

    p3_ex = ProblemExample(
        problem_id=p3.id,
        input='s = "abcabcbb"',
        output="3",
        explanation='The answer is "abc", with the length of 3.',
        display_order=1,
    )
    p3_hint1 = Hint(
        problem_id=p3.id,
        hint_number=1,
        title="Window Invariant",
        content="What data structure lets you quickly check if the incoming character is already inside the current window?",
        is_premium=False,
    )
    p3_hint2 = Hint(
        problem_id=p3.id,
        hint_number=2,
        title="Pointer Jump (Premium Hint)",
        content="Instead of advancing left one by one, can you directly jump left to last_seen[char] + 1?",
        is_premium=True,
    )
    p3_tc_sample = TestCase(
        problem_id=p3.id,
        input='"abcabcbb"',
        expected_output="3",
        is_sample=True,
        display_order=1,
        is_hidden=False,
    )
    p3_tc_hidden = TestCase(
        problem_id=p3.id,
        input='"pwwkew"',
        expected_output="3",
        is_sample=False,
        display_order=2,
        is_hidden=True,
    )
    session.add_all([p3_ex, p3_hint1, p3_hint2, p3_tc_sample, p3_tc_hidden])

    await session.commit()
