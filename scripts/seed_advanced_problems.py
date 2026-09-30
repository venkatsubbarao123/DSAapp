"""
DSAapp Advanced & Competitive Problems Seed Script
===================================================
Seeds advanced and competitive programming problems across Levels 3, 4, 5
including KMP, Number Theory, Advanced DP, Geometry, and Combinatorics.
"""

import sqlite3
import uuid
from datetime import datetime, timezone

DB_PATH = "dsaapp.db"
NS = uuid.NAMESPACE_DNS

def uid(slug: str) -> str:
    return str(uuid.uuid5(NS, f"dsaapp:{slug}"))

def now_iso():
    return datetime.now(timezone.utc).isoformat()

ADVANCED_PROBLEMS = [
    # KMP / String Algorithms
    ("kmp-pattern-search", "Knuth-Morris-Pratt Substring Search", "MEDIUM", "kmp", ["divide-conquer"], ["strings"],
     "Given a text string `text` and pattern string `pat`, find the 0-based index of the first occurrence of pat in text. Return -1 if not found. Solve in O(n + m) time.",
     "Two lines: text on first line, pat on second line.", "A single integer index, or -1.",
     "1 <= |pat| <= |text| <= 10^5", "O(n + m)", "O(m)",
     [{"input": "ABABDABACDABABCABAB\nABABCABAB", "output": "10"}, {"input": "hello\nworld", "output": "-1"}],
     ["Build the longest proper prefix that is also a suffix (LPS) array for pat.", "Use the LPS values to avoid comparing previously matched characters."]),

    ("z-algorithm-matching", "Linear Z-Algorithm String Matching", "HARD", "z-algorithm", [], ["strings"],
     "Compute the Z-array for string `s` where Z[i] is the length of the longest substring starting from s[i] which is also a prefix of s. Print Z values space-separated.",
     "A single string s.", "Space-separated Z-array values (Z[0] = 0).",
     "1 <= |s| <= 10^5", "O(n)", "O(n)",
     [{"input": "aabxaabxcaabxaabxay", "output": "0 1 0 0 4 1 0 0 0 8 1 0 0 5 1 0 0 1 0"}],
     ["Maintain an interval [l, r] which is the segment with the greatest r such that s[l..r] is a prefix.", "Use previously computed values inside the window."]),

    ("rabin-karp-rolling-hash", "Rabin-Karp Substring Matching", "MEDIUM", "rolling-hash", [], ["strings", "hashing"],
     "Find all starting indices of pattern `pat` in text `text` using polynomial rolling hashing. Output space-separated indices, or NONE.",
     "First line: text. Second line: pat.", "Space-separated 0-based indices or NONE.",
     "1 <= |pat| <= |text| <= 10^5", "O(n + m)", "O(1)",
     [{"input": "AABAACAADAABAABA\nAABA", "output": "0 9 12"}, {"input": "ABCDE\nXYZ", "output": "NONE"}],
     ["Compute polynomial hash for pattern and text windows.", "Update window hash in O(1) by subtracting leaving character and adding arriving character."]),

    # Advanced Graph Algorithms
    ("bellman-ford-negative-cycle", "Bellman-Ford Shortest Path and Negative Cycle", "HARD", "shortest-path", [], ["graphs", "shortest-path"],
     "Given a directed weighted graph with possible negative weights, find shortest path from node 0 to node n-1. If a negative weight cycle is reachable, output CYCLE.",
     "First line: n m. Next m lines: u v w.", "Shortest distance or CYCLE.",
     "2 <= n <= 1000\n1 <= m <= 5000\n-10^4 <= w <= 10^4", "O(V * E)", "O(V)",
     [{"input": "4 4\n0 1 1\n1 2 -2\n2 3 3\n0 3 5", "output": "2"}, {"input": "3 3\n0 1 1\n1 2 -2\n2 0 -1", "output": "CYCLE"}],
     ["Relax all edges V - 1 times.", "If any edge can still be relaxed on the V-th iteration, a negative cycle exists."]),

    ("floyd-warshall-all-pairs", "Floyd-Warshall All-Pairs Distances", "MEDIUM", "shortest-path", ["dp-2d"], ["graphs", "shortest-path", "matrix"],
     "Compute shortest distance between all pairs of nodes in an n-node graph. Print distance from node 0 to all nodes space-separated (-1 if unreachable).",
     "First line: n m. Next m lines: u v w (0-indexed).", "n space-separated distances from node 0.",
     "1 <= n <= 100\n0 <= m <= 2000", "O(n³)", "O(n²)",
     [{"input": "4 4\n0 1 5\n0 3 10\n1 2 3\n2 3 1", "output": "0 5 8 9"}],
     ["dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j]) for k from 0 to n-1.", "Initialize diagonal with 0 and missing edges with infinity."]),

    ("prims-minimum-spanning-tree", "Prim's Algorithm for Minimum Spanning Tree", "HARD", "minimum-spanning-tree", ["heap", "greedy"], ["graphs", "greedy"],
     "Given a connected undirected weighted graph, return the total weight of its Minimum Spanning Tree.",
     "First line: n m. Next m lines: u v w.", "A single integer — MST total weight.",
     "1 <= n <= 10^4\nn-1 <= m <= 5*10^4\n0 <= w <= 10^5", "O(m log n)", "O(n + m)",
     [{"input": "4 5\n0 1 10\n0 2 6\n0 3 5\n1 3 15\n2 3 4", "output": "19"}],
     ["Grow MST from an arbitrary starting vertex.", "Use a min-heap to pick the minimum weight edge connecting the cut."]),

    ("tarjans-bridges-detection", "Critical Connections in Network (Bridges)", "HARD", "scc", ["dfs"], ["graphs", "dfs"],
     "Find all critical connections (bridges) in an undirected network. Removing a bridge disconnects the graph. Output count of bridges.",
     "First line: n m. Next m lines: u v.", "A single integer — count of bridges.",
     "2 <= n <= 10^4\n1 <= m <= 2*10^4", "O(V + E)", "O(V + E)",
     [{"input": "4 4\n0 1\n1 2\n2 0\n1 3", "output": "1"}],
     ["Use Tarjan's bridge-finding algorithm with discovery times tin and lowest reachable times low.", "An edge (u, v) is a bridge if low[v] > tin[u]."]),

    # Advanced DP
    ("matrix-chain-multiplication", "Matrix Chain Multiplication Optimal Cost", "HARD", "dp-intervals", ["dp-2d"], ["dynamic-programming"],
     "Given an array p of matrix dimensions where matrix i has dimension p[i-1] × p[i], find minimal scalar multiplications needed to compute the chain product.",
     "First line: n (size of p). Second line: n integers.", "Minimal scalar multiplications.",
     "2 <= n <= 100", "O(n³)", "O(n²)",
     [{"input": "4\n10 20 30 40", "output": "18000"}, {"input": "5\n40 20 30 10 30", "output": "26000"}],
     ["dp[i][j] = min cost to multiply matrices Ai..Aj.", "dp[i][j] = min_{k} (dp[i][k] + dp[k+1][j] + p[i-1]*p[k]*p[j])."]),

    ("traveling-salesperson-bitmask", "Traveling Salesperson Bitmask DP", "HARD", "dp-bitmask", ["bitmask-dp"], ["dynamic-programming", "bit-manipulation"],
     "Given n cities and an n×n cost matrix, find the minimum cost to visit every city exactly once and return to starting city 0.",
     "First line: n. Next n lines: n space-separated non-negative costs.", "Minimum tour cost.",
     "2 <= n <= 14", "O(n² * 2^n)", "O(n * 2^n)",
     [{"input": "4\n0 10 15 20\n10 0 35 25\n15 35 0 30\n20 25 30 0", "output": "80"}],
     ["dp(mask, u) = min cost to visit remaining unvisited cities starting from city u.", "mask indicates which cities have been visited so far."]),

    ("tree-diameter-dp", "Tree Diameter via Dynamic Programming", "HARD", "dp-trees", ["tree-dp", "dfs"], ["trees", "dynamic-programming"],
     "Find the diameter of a weighted tree where edge weights are given. Diameter is the maximum weighted distance between any two nodes.",
     "First line: n. Next n-1 lines: u v w.", "A single integer — tree diameter.",
     "1 <= n <= 10^4\n0 <= w <= 10^4", "O(n)", "O(n)",
     [{"input": "4\n0 1 3\n1 2 4\n1 3 2", "output": "7"}],
     ["For each node, compute top two longest paths going into its subtrees.", "Sum of top two gives maximum path with this node as turning point."]),

    # Segment Tree & Fenwick
    ("fenwick-inversion-count", "Count Inversions via Fenwick Tree", "HARD", "fenwick-tree", ["fenwick-tree"], ["arrays", "fenwick-tree", "sorting"],
     "Given an array, count the number of pairs (i, j) such that i < j and nums[i] > nums[j].",
     "First line: n. Second line: n space-separated integers.", "A single integer — count of inversions.",
     "1 <= n <= 10^5", "O(n log n)", "O(n)",
     [{"input": "5\n2 4 1 3 5", "output": "3"}, {"input": "4\n4 3 2 1", "output": "6"}],
     ["Coordinate-compress values if needed.", "Process elements right to left, querying prefix sum of elements smaller in BIT, then add current element."]),

    # Interview Patterns
    ("meeting-rooms-ii", "Meeting Rooms Minimum Conference Rooms", "MEDIUM", "interview-arrays", ["greedy", "intervals"], ["intervals", "heap"],
     "Given an array of meeting time intervals [start, end], find the minimum number of conference rooms required.",
     "First line: n. Next n lines: start end.", "A single integer — rooms required.",
     "1 <= n <= 10^4", "O(n log n)", "O(n)",
     [{"input": "3\n0 30\n5 10\n15 20", "output": "2"}, {"input": "3\n7 10\n2 4\n5 6", "output": "1"}],
     ["Separate starts and ends, sort both.", "Iterate with two pointers; increment rooms when start < end, else decrement rooms."]),

    ("lru-cache-capacity", "Least Recently Used (LRU) Cache Simulation", "HARD", "interview-arrays", ["hash-map"], ["linked-list", "hashing"],
     "Simulate an LRU Cache with capacity cap. Support 'put key value' and 'get key'. Print result for each 'get' (-1 if not present).",
     "First line: capacity q. Next q lines: 'put k v' or 'get k'.", "Outputs for each get operation.",
     "1 <= cap <= 1000\n1 <= q <= 10^4", "O(1) per operation", "O(cap)",
     [{"input": "2 5\nput 1 10\nput 2 20\nget 1\nput 3 30\nget 2", "output": "10\n-1"}],
     ["Combine a hash map with a doubly linked list.", "Move accessed node to head; evict from tail when capacity exceeded."]),

    ("maximum-product-subarray", "Maximum Product Subarray", "MEDIUM", "interview-arrays", ["dp-1d"], ["arrays", "dynamic-programming"],
     "Given an integer array `nums`, find a subarray that has the largest product, and return the product.",
     "First line: n. Second line: n space-separated integers.", "Maximum product.",
     "1 <= n <= 2*10^4\n-10 <= nums[i] <= 10", "O(n)", "O(1)",
     [{"input": "4\n2 3 -2 4", "output": "6"}, {"input": "3\n-2 0 -1", "output": "0"}],
     ["Track both max_so_far and min_so_far at each step.", "A negative number swaps max and min."]),

    ("binary-tree-vertical-order", "Binary Tree Vertical Order Traversal", "MEDIUM", "interview-trees", ["bfs", "hash-map"], ["trees", "bfs"],
     "Given a binary tree (level-order, -1 for null), print nodes column by column from leftmost to rightmost. Separate columns by line.",
     "A single line of level-order integers.", "Each vertical column values on its own line space-separated.",
     "0 <= n <= 1000", "O(n)", "O(n)",
     [{"input": "3 9 20 -1 -1 15 7", "output": "9\n3 15\n20\n7"}],
     ["BFS traversal with (node, column) coordinate.", "Store nodes in a column-indexed hash map and output in column order."]),

    ("coin-change-fewest", "Target Amount Minimum Coin Count", "MEDIUM", "interview-dp", ["dp-1d"], ["dynamic-programming"],
     "Given n coin denominations and an amount, find minimum coins needed to make change. If impossible, return -1.",
     "First line: n amount. Second line: n coin values.", "Minimum coin count or -1.",
     "1 <= n <= 12\n1 <= amount <= 10^4", "O(n * amount)", "O(amount)",
     [{"input": "3 11\n1 2 5", "output": "3"}, {"input": "1 3\n2", "output": "-1"}],
     ["dp[i] = min(dp[i], dp[i - coin] + 1).", "Initialize dp with infinity, dp[0] = 0."]),
]

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()
    ts = now_iso()

    cur.execute("SELECT slug, id FROM topics")
    topic_map = dict(cur.fetchall())
    cur.execute("SELECT topic_id, id FROM subtopics")
    subtopic_map = {}
    for tid, sid in cur.fetchall():
        if tid not in subtopic_map:
            subtopic_map[tid] = sid

    cur.execute("SELECT slug, id FROM patterns")
    pat_map = dict(cur.fetchall())
    cur.execute("SELECT slug, id FROM tags")
    tag_map = dict(cur.fetchall())

    cur.execute("SELECT MAX(display_order) FROM problems")
    max_order = cur.fetchone()[0] or 0

    added = 0
    for idx, prob in enumerate(ADVANCED_PROBLEMS):
        slug, title, diff, top_slug, pats, tags, stmt, infmt, outfmt, constr, tc, sc, exs, hnts = prob
        p_id = uid(f"problem:{slug}")
        pub_p = f"prb_{uuid.uuid5(NS, slug).hex[:12]}"

        cur.execute("SELECT id FROM problems WHERE slug=?", (slug,))
        if cur.fetchone():
            continue

        topic_id = topic_map.get(top_slug)
        subtopic_id = subtopic_map.get(topic_id) if topic_id else None
        disp_order = max_order + 1 + idx
        est_mins = 20 if diff == "EASY" else (30 if diff == "MEDIUM" else 45)

        cur.execute("""
            INSERT INTO problems (
                id, public_id, slug, title, statement, explanation, difficulty, access_level, status,
                topic_id, subtopic_id, display_order, estimated_minutes, input_format, output_format,
                constraints, expected_time_complexity, expected_space_complexity, supported_languages,
                version, created_by, updated_by, created_at, updated_at, time_limit_ms, memory_limit_mb,
                output_limit_bytes, comparison_mode
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            p_id, pub_p, slug, title, stmt, None, diff, "FREE", "PUBLISHED",
            topic_id, subtopic_id, disp_order, est_mins, infmt, outfmt,
            constr, tc, sc, '["python", "java", "cpp", "javascript"]',
            1, None, None, ts, ts, 2000, 256, 65536, "exact"
        ))
        added += 1

        for ei, ex in enumerate(exs):
            ex_id = uid(f"example:{slug}:{ei}")
            cur.execute("""
                INSERT OR IGNORE INTO problem_examples (id, problem_id, input, output, explanation, display_order, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (ex_id, p_id, ex["input"], ex["output"], ex.get("explanation"), ei, ts))

        for hi, hint in enumerate(hnts, 1):
            h_id = uid(f"hint:{slug}:{hi}")
            cur.execute("""
                INSERT OR IGNORE INTO problem_hints (id, problem_id, hint_number, title, content, is_premium, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (h_id, p_id, hi, f"Hint {hi}", hint, 0, ts))

        for ti, ex in enumerate(exs[:2]):
            tc_id = uid(f"tc:sample:{slug}:{ti}")
            cur.execute("""
                INSERT OR IGNORE INTO test_cases (id, problem_id, input, expected_output, is_sample, display_order, is_hidden, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (tc_id, p_id, ex["input"], ex["output"], 1, ti, 0, ts))

        if exs:
            tc_id = uid(f"tc:hidden:{slug}:0")
            cur.execute("""
                INSERT OR IGNORE INTO test_cases (id, problem_id, input, expected_output, is_sample, display_order, is_hidden, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (tc_id, p_id, exs[0]["input"], exs[0]["output"], 0, 99, 1, ts))

        for pat_slug in pats:
            pat_id = pat_map.get(pat_slug)
            if pat_id:
                cur.execute("INSERT OR IGNORE INTO problem_patterns (problem_id, pattern_id) VALUES (?, ?)", (p_id, pat_id))

        for tag_slug in tags:
            t_id = tag_map.get(tag_slug)
            if t_id:
                cur.execute("INSERT OR IGNORE INTO problem_tags (problem_id, tag_id) VALUES (?, ?)", (p_id, t_id))

    conn.commit()
    cur.execute("SELECT COUNT(*) FROM problems")
    total_p = cur.fetchone()[0]
    cur.execute("SELECT difficulty, COUNT(*) FROM problems GROUP BY difficulty")
    diff_counts = dict(cur.fetchall())
    conn.close()

    print(f"Added {added} advanced problems. Total in DB: {total_p}. Breakdown: {diff_counts}")

if __name__ == "__main__":
    main()
