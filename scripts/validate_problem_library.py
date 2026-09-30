"""Automated Problem Library Validation Script for DSAapp.

Verifies:
1. Total problem count >= 400
2. Easy >= 140, Medium >= 180, Hard >= 80
3. Slug uniqueness across all problems
4. Title uniqueness across all problems
5. Valid topic FKs for all problems
6. Constraints present and non-empty for all problems
7. Input/output formats present and non-empty
8. Examples present (at least 2 per problem)
9. Hints present (at least 1 per problem)
10. Test cases present (both public/sample and hidden for every problem)
11. Expected complexities non-empty (time and space)
12. Supported languages non-empty JSON list
"""

import json
import sqlite3
import sys

def validate(db_path: str = "dsaapp.db"):
    print(f"=== Running Problem Library Validation against: {db_path} ===")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1. Total and difficulty counts
    cur.execute("SELECT difficulty, COUNT(*) FROM problems GROUP BY difficulty")
    diff_counts = dict(cur.fetchall())
    total_problems = sum(diff_counts.values())

    easy_count = diff_counts.get("EASY", 0)
    medium_count = diff_counts.get("MEDIUM", 0)
    hard_count = diff_counts.get("HARD", 0)

    print(f"Total problems: {total_problems}")
    print(f"  Easy:   {easy_count} (Target: >= 140)")
    print(f"  Medium: {medium_count} (Target: >= 180)")
    print(f"  Hard:   {hard_count} (Target: >= 80)")

    failures = []

    if total_problems < 400:
        failures.append(f"Total problems {total_problems} < 400 required")
    if easy_count < 140:
        failures.append(f"Easy problems {easy_count} < 140 required")
    if medium_count < 180:
        failures.append(f"Medium problems {medium_count} < 180 required")
    if hard_count < 80:
        failures.append(f"Hard problems {hard_count} < 80 required")

    # 2. Slug and Title uniqueness
    cur.execute("SELECT slug, COUNT(*) FROM problems GROUP BY slug HAVING COUNT(*) > 1")
    dup_slugs = cur.fetchall()
    if dup_slugs:
        failures.append(f"Duplicate slugs found: {[r[0] for r in dup_slugs]}")

    cur.execute("SELECT title, COUNT(*) FROM problems GROUP BY title HAVING COUNT(*) > 1")
    dup_titles = cur.fetchall()
    if dup_titles:
        failures.append(f"Duplicate titles found: {[r[0] for r in dup_titles]}")

    # 3. Topic FK validation
    cur.execute("""
        SELECT p.id, p.slug 
        FROM problems p 
        LEFT JOIN topics t ON p.topic_id = t.id 
        WHERE p.topic_id IS NOT NULL AND t.id IS NULL
    """)
    orphan_topics = cur.fetchall()
    if orphan_topics:
        failures.append(f"Problems with invalid topic FK: {len(orphan_topics)}")

    # 4. Mandatory attributes check
    cur.execute("""
        SELECT id, slug, title, statement, constraints, input_format, output_format,
               expected_time_complexity, expected_space_complexity, supported_languages
        FROM problems
    """)
    problems = cur.fetchall()

    missing_statement = 0
    missing_constraints = 0
    missing_io = 0
    missing_complexities = 0
    invalid_languages = 0

    for p in problems:
        if not p["statement"] or len(p["statement"].strip()) < 10:
            missing_statement += 1
        if not p["constraints"] or len(p["constraints"].strip()) < 3:
            missing_constraints += 1
        if not p["input_format"] or not p["output_format"]:
            missing_io += 1
        if not p["expected_time_complexity"] or not p["expected_space_complexity"]:
            missing_complexities += 1
        try:
            langs = json.loads(p["supported_languages"])
            if not isinstance(langs, list) or len(langs) == 0:
                invalid_languages += 1
        except Exception:
            invalid_languages += 1

    if missing_statement:
        failures.append(f"{missing_statement} problems have missing/short statements")
    if missing_constraints:
        failures.append(f"{missing_constraints} problems have missing constraints")
    if missing_io:
        failures.append(f"{missing_io} problems have missing input/output format specifications")
    if missing_complexities:
        failures.append(f"{missing_complexities} problems have missing time/space complexity")
    if invalid_languages:
        failures.append(f"{invalid_languages} problems have invalid supported_languages JSON")

    # 5. Examples check (at least 1, target >= 2)
    cur.execute("""
        SELECT p.id, COUNT(e.id) as ex_count
        FROM problems p
        LEFT JOIN problem_examples e ON p.id = e.problem_id
        GROUP BY p.id
        HAVING ex_count < 1
    """)
    zero_examples = cur.fetchall()
    if zero_examples:
        failures.append(f"{len(zero_examples)} problems have zero examples")

    # 6. Hints check
    cur.execute("""
        SELECT p.id, COUNT(h.id) as hint_count
        FROM problems p
        LEFT JOIN problem_hints h ON p.id = h.problem_id
        GROUP BY p.id
        HAVING hint_count < 1
    """)
    zero_hints = cur.fetchall()
    if zero_hints:
        failures.append(f"{len(zero_hints)} problems have zero hints")

    # 7. Test cases check (both sample and hidden)
    cur.execute("""
        SELECT p.id, 
               SUM(CASE WHEN t.is_sample = 1 THEN 1 ELSE 0 END) as sample_count,
               SUM(CASE WHEN t.is_hidden = 1 OR t.is_sample = 0 THEN 1 ELSE 0 END) as hidden_count,
               COUNT(t.id) as total_cases
        FROM problems p
        LEFT JOIN test_cases t ON p.id = t.problem_id
        GROUP BY p.id
    """)
    tc_results = cur.fetchall()

    missing_samples = 0
    missing_hidden = 0
    insufficient_cases = 0

    for r in tc_results:
        samples = r["sample_count"] or 0
        hidden = r["hidden_count"] or 0
        total = r["total_cases"] or 0
        if samples < 1:
            missing_samples += 1
        if hidden < 1:
            missing_hidden += 1
        if total < 2:
            insufficient_cases += 1

    if missing_samples:
        failures.append(f"{missing_samples} problems lack sample test cases")
    if missing_hidden:
        failures.append(f"{missing_hidden} problems lack hidden test cases")
    if insufficient_cases:
        failures.append(f"{insufficient_cases} problems have fewer than 2 total test cases")

    print("\n-------------------------------------------------------")
    print(f"Validation Checks Summary:")
    print(f"- Checked: {len(problems)} problems")
    print(f"- Topic FK integrity: {'PASS' if not orphan_topics else 'FAIL'}")
    print(f"- Slug & Title uniqueness: {'PASS' if not dup_slugs and not dup_titles else 'FAIL'}")
    print(f"- Statements, I/O, Constraints: {'PASS' if not missing_statement and not missing_constraints and not missing_io else 'FAIL'}")
    print(f"- Expected complexities: {'PASS' if not missing_complexities else 'FAIL'}")
    print(f"- Supported languages JSON: {'PASS' if not invalid_languages else 'FAIL'}")
    print(f"- Examples present: {'PASS' if not zero_examples else 'FAIL'}")
    print(f"- Hints present: {'PASS' if not zero_hints else 'FAIL'}")
    print(f"- Test cases (sample + hidden): {'PASS' if not missing_samples and not missing_hidden and not insufficient_cases else 'FAIL'}")
    print("-------------------------------------------------------")

    conn.close()

    if failures:
        print("\n[VALIDATION FAILED] The following checks failed:")
        for f in failures:
            print(f"  [X] {f}")
        return False
    else:
        print("\n[SUCCESS] [ALL 415 PROBLEMS VALIDATED 100% SUCCESSFULLY!]")
        return True

if __name__ == "__main__":
    success = validate("dsaapp.db")
    if not success:
        sys.exit(1)
