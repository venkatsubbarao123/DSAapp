# Intelligent Recommendation & Adaptive Difficulty Engine

## 1. Executive Overview

The **DSAapp Recommendation & Adaptive Difficulty Engine** (`IntelligentProblemSelector` and `AdaptiveDifficultyService`) provides pedagogically guided problem selection. Rather than presenting random problems, the engine analyzes learner mastery, spaced repetition intervals, cognitive mistake logs, and recent submission trends to construct the optimal next challenge.

---

## 2. Recommendation Scoring Formula

Every eligible candidate problem $P$ receives a composite pedagogical relevance score:

$$\text{Score}(P) = \text{Baseline}(10) + \sum \text{Pedagogical Weights}$$

### Scoring Factors Table

| Pedagogical Factor | Weight | Condition & Educational Rationale |
| :--- | :---: | :--- |
| **Spaced Repetition Due** | **+40.0** | Problem is scheduled for revision review and is active in `RevisionItem`. Reinforces retention before cognitive decay. |
| **Cognitive Mistake Logged** | **+35.0** | Learner previously logged a cognitive gap, syntax error, or logic mistake in `Mistake` for this problem. |
| **Revision Mode Solved** | **+35.0** | Active practice mode is `REVISION` and the problem was previously solved. |
| **Recently Attempted / Unsolved** | **+30.0** | Problem was attempted in `UserProblemProgress` but remains unsolved. Encourages perseverance. |
| **Algorithmic Pattern Match** | **+25.0** | Problem matches the targeted pattern (e.g., Sliding Window, Two Pointers, Top-K Elements). |
| **Difficulty Calibration** | **+20.0** | Problem difficulty matches the learner's current adaptive difficulty tier. |
| **Weak Topic Cluster** | **+15.0** | Problem belongs to a curriculum topic where the learner logged multiple mistakes. |
| **Baseline Curriculum Growth** | **+10.0** | Default score ensuring every eligible published problem has positive weight. |

### Deterministic Candidate Sorting
To prevent non-deterministic sorting and pagination anomalies, problems are ranked using:
$$\text{sort\_key} = (-\text{score}, \text{problem\_id})$$

---

## 3. Strict Content Access & Security Boundary

Before scoring, candidate problems are passed through hard security filters:
1. **Status Filter**: Only `ContentStatus.PUBLISHED` problems are queried. All `DRAFT` and `ARCHIVED` problems are excluded.
2. **Entitlement Filter**: Free-tier learners only receive `ContentAccessLevel.FREE` problems. `PREMIUM` problems are strictly excluded unless the learner possesses an active Pro subscription verified by `UserRepository.has_active_premium()`.
3. **Solved Filter**: In normal practice drills (`QUICK`, `TOPIC`, `PATTERN`, `DIFFICULTY`, `WEAK_AREA`), already-solved problems are excluded. In `REVISION` mode, previously solved problems are permitted and prioritized.

---

## 4. Adaptive Difficulty Engine

`AdaptiveDifficultyService` continually monitors the student's recent submissions:

1. **Step-Up Condition**:
   - If the student's last 3 consecutive distinct submissions are `ACCEPTED`, the difficulty steps up:
     $$\text{EASY} \longrightarrow \text{MEDIUM} \longrightarrow \text{HARD} \longrightarrow \text{EXPERT}$$
2. **Step-Down Condition**:
   - If the student's last 3 consecutive submissions contain errors (`WRONG_ANSWER`, `TIME_LIMIT_EXCEEDED`, `RUNTIME_ERROR`), the difficulty steps down:
     $$\text{EXPERT} \longrightarrow \text{HARD} \longrightarrow \text{MEDIUM} \longrightarrow \text{EASY}$$
3. **Stability**:
   - Mixed performance maintains the current calibrated difficulty level.

---

## 5. Pedagogical Explanations API

To foster metacognitive awareness, learners can inspect why any problem was recommended via `GET /api/v1/practice/recommendations/explain/{problem_id}`:

```json
{
  "problem_id": "87b3af79-c974-4c27-a4d7-5878a4cd69a6",
  "title": "Merge Intervals",
  "explanation": "This problem was selected based on your current skill profile and learning history.",
  "pedagogical_factors": [
    "Targets an algorithmic topic where cognitive mistakes were recently noted.",
    "Calibrated to your preferred difficulty tier (MEDIUM)."
  ],
  "metrics": {
    "score": 45.0,
    "difficulty": "MEDIUM",
    "category": "WEAK_TOPIC"
  }
}
```
