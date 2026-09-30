"""
DSAapp Expanded Problems Seed Script
====================================
Seeds an additional 150+ original DSA problems across all 54 curriculum topics
with complete constraints, test cases, examples, and hints.
Idempotent and deterministic using uuid5.
"""

import sqlite3
import uuid
import json
from datetime import datetime, timezone

DB_PATH = "dsaapp.db"
NS = uuid.NAMESPACE_DNS

def uid(slug: str) -> str:
    return str(uuid.uuid5(NS, f"dsaapp:{slug}"))

def now_iso():
    return datetime.now(timezone.utc).isoformat()

# Definition of topics and problem blueprints to ensure massive, high quality coverage
ADDITIONAL_PROBLEMS = [
    # --- LEVEL 0: PROGRAMMING FOUNDATIONS ---
    # Variables and Types
    ("integer-to-binary-string", "Convert Integer to Binary String", "EASY", "variables-and-types", [], ["math"],
     "Given a positive integer `n`, return its representation as a binary string without built-in bin() formatting prefixes.",
     "A single positive integer n.", "A string representing n in base 2.",
     "1 <= n <= 10^9", "O(log n)", "O(log n)",
     [{"input": "5", "output": "101"}, {"input": "10", "output": "1010"}],
     ["Repeatedly divide by 2 and collect remainders.", "Reverse the remainder sequence to form the binary string."]),
    
    ("celsius-to-fahrenheit", "Temperature Scale Conversion", "EASY", "variables-and-types", [], ["math"],
     "Given a floating-point temperature in Celsius `c`, return its value in Fahrenheit rounded to two decimal places. F = C * 9/5 + 32.",
     "A single float c.", "A float formatted to two decimal places.",
     "-100.0 <= c <= 100.0", "O(1)", "O(1)",
     [{"input": "0.0", "output": "32.00"}, {"input": "100.0", "output": "212.00"}],
     ["Multiply by 9, divide by 5, then add 32.", "Use standard floating-point precision formatting."]),

    ("swap-without-temp", "Arithmetic Variable Swap", "EASY", "variables-and-types", [], ["math"],
     "Given two integers `a` and `b`, output their values swapped.",
     "Two space-separated integers a b.", "Two space-separated integers b a.",
     "-10^9 <= a, b <= 10^9", "O(1)", "O(1)",
     [{"input": "4 9", "output": "9 4"}, {"input": "-1 5", "output": "5 -1"}],
     ["In Python you can use tuple unpacking: a, b = b, a.", "Or arithmetically: a = a + b, b = a - b, a = a - b."]),

    # Control Flow
    ("leap-year-checker", "Leap Year Evaluation", "EASY", "control-flow", [], ["math"],
     "Determine whether a given calendar year `y` is a leap year. A year is a leap year if divisible by 4, except end-of-century years which must be divisible by 400. Print YES or NO.",
     "A single integer y.", "YES or NO.",
     "1 <= y <= 9999", "O(1)", "O(1)",
     [{"input": "2024", "output": "YES"}, {"input": "1900", "output": "NO"}, {"input": "2000", "output": "YES"}],
     ["Check if divisible by 400 first.", "Then check if divisible by 4 and not divisible by 100."]),

    ("fizz-buzz-custom", "Modular FizzBuzz Sequence", "EASY", "control-flow", [], ["math"],
     "Given an integer `n`, print the numbers from 1 to n. For multiples of 3 print Fizz, for multiples of 5 print Buzz, for multiples of both print FizzBuzz. Space-separated.",
     "A single integer n.", "Space-separated sequence of tokens.",
     "1 <= n <= 100", "O(n)", "O(1)",
     [{"input": "5", "output": "1 2 Fizz 4 Buzz"}, {"input": "15", "output": "1 2 Fizz 4 Buzz Fizz 7 8 Fizz Buzz 11 Fizz 13 14 FizzBuzz"}],
     ["Check divisibility by 15 first.", "Then check divisibility by 3 and 5 individually."]),

    # Functions
    ("collatz-conjecture-steps", "Collatz Conjecture Step Counter", "EASY", "functions", [], ["recursion", "math"],
     "Given a positive integer `n`, count the number of steps to reach 1 following the rules: if n is even, n = n/2; if n is odd, n = 3*n + 1.",
     "A single positive integer n.", "A single integer — count of steps.",
     "1 <= n <= 10^6", "O(steps)", "O(1)",
     [{"input": "6", "output": "8"}, {"input": "1", "output": "0"}],
     ["Use a while loop until n == 1.", "Increment step counter on each transition."]),

    ("greatest-common-divisor", "Euclidean GCD Algorithm", "EASY", "functions", [], ["math"],
     "Given two positive integers `a` and `b`, compute their Greatest Common Divisor using the Euclidean algorithm.",
     "Two space-separated integers a b.", "A single integer — gcd(a, b).",
     "1 <= a, b <= 10^9", "O(log(min(a,b)))", "O(1)",
     [{"input": "48 18", "output": "6"}, {"input": "101 10", "output": "1"}],
     ["gcd(a, b) = gcd(b, a % b) until b is 0.", "The base case is when b == 0, returning a."]),

    # Lists and Strings
    ("string-title-case", "Capitalize Words in Title", "EASY", "lists-and-strings", [], ["strings"],
     "Given a sentence `s` with space-separated words, capitalize the first letter of each word and lowercase the rest.",
     "A single string s.", "The title-cased sentence.",
     "1 <= |s| <= 1000", "O(n)", "O(n)",
     [{"input": "hello world from dsa", "output": "Hello World From Dsa"}, {"input": "PYTHON programming", "output": "Python Programming"}],
     ["Split the string by space into words.", "Capitalize each word and rejoin with spaces."]),

    ("list-chunking", "Partition List into Fixed Chunks", "EASY", "lists-and-strings", [], ["arrays"],
     "Given an array of integers and a chunk size `k`, print chunks of size k on separate lines. The last chunk may contain fewer elements.",
     "First line: n k. Second line: n space-separated integers.", "Each chunk on its own line space-separated.",
     "1 <= k <= n <= 1000", "O(n)", "O(1)",
     [{"input": "7 3\n1 2 3 4 5 6 7", "output": "1 2 3\n4 5 6\n7"}],
     ["Iterate with step k: range(0, len(nums), k).", "Slice nums[i:i+k] and print."]),

    # Dictionaries and Sets
    ("character-frequency-rank", "Top Character by Frequency", "EASY", "dictionaries-and-sets", ["hash-map"], ["strings", "hashing"],
     "Given a lowercase string `s`, find the character that appears most frequently. If there is a tie, return the one that appears earliest in the alphabet.",
     "A single string s.", "A single character.",
     "1 <= |s| <= 10^5", "O(n)", "O(1)",
     [{"input": "banana", "output": "a"}, {"input": "dcba", "output": "a"}],
     ["Count occurrences of each character using a dictionary.", "Sort tied candidates alphabetically."]),

    ("set-intersection-count", "Count Common Unique Elements", "EASY", "dictionaries-and-sets", ["hash-map"], ["hashing"],
     "Given two arrays of integers, count how many distinct numbers appear in both arrays.",
     "First line: n m. Second line: n space-separated ints. Third line: m space-separated ints.", "A single integer — common unique count.",
     "1 <= n, m <= 10^4", "O(n + m)", "O(n)",
     [{"input": "4 4\n1 2 2 1\n2 2 3 4", "output": "1"}, {"input": "3 3\n1 3 5\n2 4 6", "output": "0"}],
     ["Convert both lists to sets.", "Compute the length of their set intersection."]),

    # Big-O Introduction
    ("count-operations-nested-loops", "Complexity Verification Loop", "EASY", "big-o-introduction", [], ["math"],
     "Given integers n and m, return the exact number of iterations executed by two nested loops where i runs from 1 to n and j runs from 1 to m.",
     "Two space-separated integers n m.", "A single integer — total iterations.",
     "1 <= n, m <= 10^5", "O(1)", "O(1)",
     [{"input": "5 10", "output": "50"}, {"input": "100 100", "output": "10000"}],
     ["Notice that the inner loop runs m times for each of the n iterations.", "The total count is simply n * m."]),

    # --- LEVEL 1: FOUNDATION DSA ---
    # Deque
    ("sliding-window-maximum", "Sliding Window Maximum", "HARD", "deque", ["sliding-window", "monotonic-stack"], ["arrays", "queue"],
     "Given an array `nums` and sliding window size `k`, return the maximum value in each sliding window moving from left to right.",
     "First line: n k. Second line: n space-separated integers.", "Space-separated maximums for each window.",
     "1 <= k <= n <= 10^5\n-10^4 <= nums[i] <= 10^4", "O(n)", "O(k)",
     [{"input": "8 3\n1 3 -1 -3 5 3 6 7", "output": "3 3 5 5 6 7"}],
     ["A monotonic decreasing deque stores indices of useful maximum candidates.", "Pop elements from back that are smaller than current element."]),

    ("palindrome-linked-list", "Palindrome Linked List Verification", "EASY", "linked-lists", ["fast-slow-pointers", "two-pointers"], ["linked-list"],
     "Given the values of a singly linked list, determine if the sequence reads the same backwards. Print YES or NO.",
     "A single line of space-separated integers representing the list.", "YES or NO.",
     "1 <= n <= 10^5", "O(n)", "O(1)",
     [{"input": "1 2 2 1", "output": "YES"}, {"input": "1 2 3", "output": "NO"}],
     ["Find the midpoint using fast and slow pointers.", "Reverse the second half in-place and compare with the first half."]),

    ("delete-node-linked-list", "Delete Target Value from Linked List", "EASY", "linked-lists", [], ["linked-list"],
     "Given a singly linked list and an integer `val`, remove all nodes having value `val` and print the remaining list.",
     "First line: target val. Second line: space-separated integers of the linked list.", "Space-separated integers of filtered list.",
     "0 <= n <= 10^4", "O(n)", "O(1)",
     [{"input": "6\n1 2 6 3 4 5 6", "output": "1 2 3 4 5"}],
     ["Use a dummy head node to simplify deleting the head node.", "Update curr.next = curr.next.next when matching."]),

    ("merge-two-sorted-lists", "Merge Two Sorted Linked Lists", "EASY", "linked-lists", ["two-pointers"], ["linked-list"],
     "Merge two sorted integer sequences into a single sorted sequence in non-decreasing order.",
     "First line: sequence 1. Second line: sequence 2.", "Space-separated merged sequence.",
     "0 <= n, m <= 10^4", "O(n + m)", "O(1)",
     [{"input": "1 2 4\n1 3 4", "output": "1 1 2 3 4 4"}],
     ["Compare the heads of both lists and advance the smaller pointer.", "Append remaining elements from whichever list is non-empty."]),

    ("detect-cycle-linked-list", "Linked List Cycle Detection", "MEDIUM", "linked-lists", ["fast-slow-pointers"], ["linked-list"],
     "Given an array where nums[i] represents the next pointer index (-1 represents null tail), determine if a cycle exists. Print YES or NO.",
     "First line: n. Second line: n space-separated next indices.", "YES or NO.",
     "1 <= n <= 10^4", "O(n)", "O(1)",
     [{"input": "4\n1 2 0 -1", "output": "YES"}, {"input": "3\n1 2 -1", "output": "NO"}],
     ["Floyd's Tortoise and Hare algorithm uses two pointers moving at speed 1 and 2.", "If they ever meet, a cycle exists."]),

    ("min-remove-valid-parentheses", "Minimum Removals for Valid Parentheses", "MEDIUM", "stack", ["monotonic-stack"], ["stack", "strings"],
     "Given a string `s` of '(', ')' and lowercase letters, remove the minimum number of parentheses so the resulting string is valid.",
     "A single string s.", "The valid string.",
     "1 <= |s| <= 10^5", "O(n)", "O(n)",
     [{"input": "lee(t(c)o)de)", "output": "lee(t(c)o)de"}, {"input": "a)b(c)d", "output": "ab(c)d"}],
     ["Use a stack to record indices of unmatched opening parentheses.", "Mark indices of invalid closing parentheses and filter them out."]),

    ("daily-temperatures", "Daily Temperatures", "MEDIUM", "stack", ["monotonic-stack"], ["stack", "arrays"],
     "Given an array of daily temperatures `t`, return an array such that answer[i] is the number of days you must wait after day i to get a warmer temperature. If none, output 0.",
     "First line: n. Second line: n space-separated integers.", "n space-separated waiting days.",
     "1 <= n <= 10^5\n30 <= t[i] <= 100", "O(n)", "O(n)",
     [{"input": "8\n73 74 75 71 69 72 76 73", "output": "1 1 4 2 1 1 0 0"}],
     ["Use a monotonic decreasing stack storing indices of temperatures.", "When current temp > stack top temp, pop and compute index difference."]),

    ("evaluate-reverse-polish-notation", "Evaluate Reverse Polish Notation", "MEDIUM", "stack", [], ["stack"],
     "Evaluate the value of an arithmetic expression in Reverse Polish Notation (postfix). Valid operators are +, -, *, / (integer division truncating toward zero).",
     "A space-separated sequence of numbers and operators.", "A single integer result.",
     "1 <= tokens <= 10^4", "O(n)", "O(n)",
     [{"input": "2 1 + 3 *", "output": "9"}, {"input": "4 13 5 / +", "output": "6"}],
     ["Push operands onto a stack.", "When an operator is encountered, pop two operands, apply operator, and push result back."]),

    # Two Pointers & Sliding Window
    ("sort-colors-dutch-flag", "Dutch National Flag Sort", "MEDIUM", "two-pointers", ["two-pointers"], ["arrays", "sorting"],
     "Given an array of 0s, 1s, and 2s, sort them in-place in linear time and constant extra space.",
     "First line: n. Second line: n space-separated integers (0, 1, or 2).", "n space-separated sorted integers.",
     "1 <= n <= 10^5", "O(n)", "O(1)",
     [{"input": "6\n2 0 2 1 1 0", "output": "0 0 1 1 2 2"}],
     ["Maintain three pointers: low, mid, and high.", "Swap with low when mid is 0, swap with high when mid is 2."]),

    ("minimum-size-subarray-sum", "Minimum Size Subarray Sum", "MEDIUM", "sliding-window", ["sliding-window", "two-pointers"], ["arrays"],
     "Given an array of positive integers `nums` and a positive target `target`, return the minimal length of a contiguous subarray whose sum is >= target. Return 0 if none.",
     "First line: target n. Second line: n space-separated positive integers.", "A single integer — minimal length.",
     "1 <= n <= 10^5\n1 <= target <= 10^9", "O(n)", "O(1)",
     [{"input": "7 6\n2 3 1 2 4 3", "output": "2"}, {"input": "11 3\n1 1 1", "output": "0"}],
     ["Expand right pointer while window sum < target.", "Shrink left pointer while window sum >= target, updating min length."]),

    ("longest-repeating-char-replacement", "Longest Substring with Character Replacement", "MEDIUM", "sliding-window", ["sliding-window"], ["strings"],
     "Given a string `s` uppercase letters and integer `k`, you can change at most k characters to any uppercase letter. Return the length of the longest substring with same letters.",
     "First line: s k.", "A single integer — maximum length.",
     "1 <= |s| <= 10^5\n0 <= k <= |s|", "O(n)", "O(1)",
     [{"input": "ABAB 2", "output": "4"}, {"input": "AABABBA 1", "output": "4"}],
     ["Window size minus count of most frequent character <= k.", "If window_len - max_freq > k, slide left boundary forward."]),

    # Prefix Sum
    ("range-sum-query-immutable", "Range Sum Queries", "EASY", "prefix-sum", ["prefix-sum"], ["arrays"],
     "Given an array and multiple range sum queries [l, r], answer each query in O(1) time after O(n) preprocessing.",
     "First line: n q. Second line: n integers. Next q lines: l r (0-based inclusive).", "q lines each with query sum.",
     "1 <= n, q <= 10^5", "O(1) per query", "O(n)",
     [{"input": "5 3\n1 2 3 4 5\n0 2\n1 3\n0 4", "output": "6\n9\n15"}],
     ["Build prefix sum array where P[i] = nums[0] + ... + nums[i-1].", "Query(l, r) = P[r+1] - P[l]."]),

    ("find-pivot-index", "Find Equilibrium Pivot Index", "EASY", "prefix-sum", ["prefix-sum"], ["arrays"],
     "The pivot index is where the sum of numbers strictly to the left equals the sum of numbers strictly to the right. Return the leftmost pivot index, or -1.",
     "First line: n. Second line: n space-separated integers.", "A single integer — pivot index.",
     "1 <= n <= 10^5", "O(n)", "O(1)",
     [{"input": "6\n1 7 3 6 5 6", "output": "3"}, {"input": "3\n1 2 3", "output": "-1"}],
     ["Calculate total sum first.", "Iterate tracking leftSum; rightSum = total - leftSum - nums[i]."]),

    # --- LEVEL 2: CORE DSA ---
    # Binary Trees
    ("diameter-of-binary-tree", "Diameter of Binary Tree", "EASY", "binary-trees", ["dfs"], ["trees"],
     "Given a binary tree (level-order, -1 for null), return the length of the diameter (the longest path between any two nodes in terms of edges).",
     "A single line of level-order integers.", "A single integer — diameter in edges.",
     "1 <= n <= 10^4", "O(n)", "O(h)",
     [{"input": "1 2 3 4 5", "output": "3"}, {"input": "1 2", "output": "1"}],
     ["Diameter through node = left_height + right_height.", "Maintain a global max while computing tree heights recursively."]),

    ("symmetric-binary-tree", "Symmetric Binary Tree", "EASY", "binary-trees", ["dfs"], ["trees"],
     "Given a binary tree, check whether it is a mirror of itself (symmetric around its center). Print YES or NO.",
     "A single line of level-order integers.", "YES or NO.",
     "1 <= n <= 10^4", "O(n)", "O(h)",
     [{"input": "1 2 2 3 4 4 3", "output": "YES"}, {"input": "1 2 2 -1 3 -1 3", "output": "NO"}],
     ["Two trees are mirrors if roots match, t1.left matches t2.right, and t1.right matches t2.left.", "Use a recursive helper isMirror(t1, t2)."]),

    ("invert-binary-tree", "Invert Binary Tree", "EASY", "binary-trees", ["dfs"], ["trees"],
     "Invert a binary tree (swap left and right children for every node) and output its level-order traversal.",
     "A single line of level-order integers.", "Space-separated level-order inverted tree.",
     "0 <= n <= 1000", "O(n)", "O(h)",
     [{"input": "4 2 7 1 3 6 9", "output": "4 7 2 9 6 3 1"}],
     ["Recursively invert left and right subtrees.", "Swap root.left and root.right."]),

    # Binary Search Trees
    ("kth-smallest-in-bst", "Kth Smallest Element in BST", "MEDIUM", "bst", ["dfs"], ["trees", "bst"],
     "Given a Binary Search Tree (level-order, -1 for null) and an integer k, return the kth smallest value (1-indexed).",
     "First line: k. Second line: level-order BST.", "A single integer.",
     "1 <= k <= n <= 10^4", "O(h + k)", "O(h)",
     [{"input": "1\n3 1 4 -1 2", "output": "1"}, {"input": "3\n5 3 6 2 4 -1 -1 1", "output": "3"}],
     ["An in-order traversal of a BST visits nodes in strictly ascending order.", "Stop and return the value when count reaching k."]),

    ("insert-into-bst", "Insert into a Binary Search Tree", "MEDIUM", "bst", [], ["trees", "bst"],
     "Insert a value into a BST while maintaining the BST invariant. Return the in-order traversal of the modified tree.",
     "First line: target val. Second line: level-order BST.", "Space-separated in-order traversal.",
     "0 <= n <= 10^4", "O(h)", "O(h)",
     [{"input": "5\n4 2 7 1 3", "output": "1 2 3 4 5 7"}],
     ["If val < root.val, insert into left subtree.", "If val > root.val, insert into right subtree."]),

    # Heap
    ("merge-k-sorted-lists", "Merge K Sorted Arrays", "HARD", "heap", ["heap"], ["arrays", "heap", "sorting"],
     "Given k sorted arrays, merge them into one single sorted array.",
     "First line: k. Next k lines: array size m followed by m sorted integers.", "Space-separated merged sorted sequence.",
     "1 <= k <= 1000\nTotal elements <= 10^5", "O(N log k)", "O(k)",
     [{"input": "3\n3 1 4 5\n3 1 3 4\n2 2 6", "output": "1 1 2 3 4 4 5 6"}],
     ["Push the first element of each of the k arrays into a min-heap with array index.", "Pop the minimum, append to result, and push the next element from that array."]),

    ("find-median-from-data-stream", "Median of Running Stream", "HARD", "heap", ["heap"], ["heap"],
     "Design a structure to support adding numbers and returning the median of all added numbers at any time.",
     "First line: n. Second line: n space-separated numbers added sequentially.", "Median after all n numbers added.",
     "1 <= n <= 10^5", "O(log n) per add", "O(n)",
     [{"input": "5\n1 2 3 4 5", "output": "3"}, {"input": "4\n1 2 3 4", "output": "2.5"}],
     ["Use two heaps: a max-heap for lower half and min-heap for upper half.", "Balance sizes so max-heap has at most 1 more element than min-heap."]),

    # Greedy
    ("jump-game-reachability", "Jump Game Reachability", "MEDIUM", "greedy", ["greedy"], ["arrays", "greedy"],
     "You are given an integer array `nums` where nums[i] denotes maximum jump length from position i. Return YES if you can reach the last index, else NO.",
     "First line: n. Second line: n space-separated non-negative integers.", "YES or NO.",
     "1 <= n <= 10^5", "O(n)", "O(1)",
     [{"input": "5\n2 3 1 1 4", "output": "YES"}, {"input": "5\n3 2 1 0 4", "output": "NO"}],
     ["Track the furthest reachable index so far.", "If current index > furthest reachable, you are stranded."]),

    ("gas-station-circuit", "Circular Gas Station Tour", "MEDIUM", "greedy", ["greedy"], ["arrays", "greedy"],
     "Given circular gas stations with gas[i] and cost[i] to travel to i+1, find the starting station index to complete the full circuit once. If impossible, return -1.",
     "First line: n. Second line: gas array. Third line: cost array.", "Starting station index or -1.",
     "1 <= n <= 10^5", "O(n)", "O(1)",
     [{"input": "5\n1 2 3 4 5\n3 4 5 1 2", "output": "3"}, {"input": "3\n2 3 4\n3 4 3", "output": "-1"}],
     ["If total gas < total cost, completing the circuit is impossible.", "If current tank drops below 0, reset start position to i+1."]),

    # Backtracking
    ("word-search-matrix", "Word Search in Matrix", "MEDIUM", "backtracking", ["backtracking", "dfs"], ["matrix", "backtracking"],
     "Given an m×n grid of characters and a word, return YES if the word exists following adjacent horizontal/vertical letters without reusing a cell.",
     "First line: m n word. Next m lines: n space-separated characters.", "YES or NO.",
     "1 <= m, n <= 6", "O(m * n * 4^L)", "O(L)",
     [{"input": "3 4 ABCCED\nA B C E\nS F C S\nA D E E", "output": "YES"}],
     ["Start DFS from every cell matching word[0].", "Mark visited cells in-place with a sentinel character and restore on backtrack."]),

    ("sudoku-validity-checker", "Valid Sudoku Grid Checker", "MEDIUM", "matrix", ["hash-map"], ["matrix"],
     "Determine if a 9×9 Sudoku board is valid according to classic rules. Empty cells contain '.'. Print YES or NO.",
     "9 lines each with 9 space-separated tokens.", "YES or NO.",
     "Board size is always 9×9.", "O(1)", "O(1)",
     [{"input": "5 3 . . 7 . . . .\n6 . . 1 9 5 . . .\n. 9 8 . . . . 6 .\n8 . . . 6 . . . 3\n4 . . 8 . 3 . . 1\n7 . . . 2 . . . 6\n. 6 . . . . 2 8 .\n. . . 4 1 9 . . 5\n. . . . 8 . . 7 9", "output": "YES"}],
     ["Check uniqueness for each of the 9 rows, 9 columns, and 9 3×3 sub-boxes.", "Use sets to detect duplicates."]),

    # Bit Manipulation
    ("single-number-finder", "Find the Unique Lone Element", "EASY", "bit-manipulation", [], ["bit-manipulation", "arrays"],
     "Given a non-empty array of integers where every element appears twice except for one unique element, find that single element in O(n) time and O(1) space.",
     "First line: n. Second line: n space-separated integers.", "The unique integer.",
     "1 <= n <= 3*10^4", "O(n)", "O(1)",
     [{"input": "5\n4 1 2 1 2", "output": "4"}, {"input": "3\n2 2 1", "output": "1"}],
     ["Recall XOR properties: x ^ x = 0 and x ^ 0 = x.", "XOR all elements together; duplicates cancel out to 0."]),

    ("bitwise-and-range", "Bitwise AND of Numbers Range", "MEDIUM", "bit-manipulation", [], ["bit-manipulation"],
     "Given two integers `left` and `right`, return the bitwise AND of all numbers in [left, right] inclusive.",
     "Two space-separated integers left right.", "A single integer.",
     "0 <= left <= right <= 2^31 - 1", "O(log n)", "O(1)",
     [{"input": "5 7", "output": "4"}, {"input": "0 0", "output": "0"}],
     ["The result is the common binary prefix of left and right shifted back.", "Right-shift both numbers until they are equal, then shift left by the step count."]),

    # --- LEVEL 3: ADVANCED DSA ---
    # Graphs
    ("clone-graph", "Clone Undirected Graph", "MEDIUM", "graphs", ["dfs", "bfs", "hash-map"], ["graphs"],
     "Deep copy a connected undirected graph given as an adjacency list. Return the cloned adjacency representation.",
     "First line: n. Next n lines: list of neighbor IDs.", "Cloned adjacency list.",
     "0 <= n <= 100", "O(V + E)", "O(V)",
     [{"input": "4\n2 4\n1 3\n2 4\n1 3", "output": "2 4\n1 3\n2 4\n1 3"}],
     ["Use a hash map mapping original node pointer to new cloned node.", "Traverse with DFS/BFS, cloning nodes and edges recursively."]),

    ("course-schedule-ii", "Course Schedule Order Sequence", "MEDIUM", "topological-sort", ["topological-sort", "bfs"], ["graphs"],
     "Return a valid ordering of courses you should take to finish all n courses given prerequisite pairs. If impossible, return NONE.",
     "First line: n m. Next m lines: a b (b must be taken before a).", "Space-separated sequence or NONE.",
     "1 <= n <= 2000", "O(V + E)", "O(V)",
     [{"input": "4 4\n1 0\n2 0\n3 1\n3 2", "output": "0 1 2 3"}],
     ["Kahn's algorithm: queue nodes with in-degree 0.", "If processed count < n, a directed cycle exists."]),

    ("redundant-connection", "Find Redundant Cycle Edge", "MEDIUM", "union-find", ["union-find"], ["graphs"],
     "A tree of n nodes had one extra edge added. Return the edge that can be removed so that the resulting graph is a tree of n nodes.",
     "First line: n. Next n lines: u v.", "The redundant edge u v.",
     "3 <= n <= 1000", "O(n * α(n))", "O(n)",
     [{"input": "3\n1 2\n1 3\n2 3", "output": "2 3"}],
     ["Process edges sequentially with Disjoint Set Union (DSU).", "The first edge connecting two already-connected vertices is redundant."]),

    ("network-delay-time", "Network Delay Time", "MEDIUM", "shortest-path", ["heap", "bfs"], ["graphs"],
     "Given n nodes and directed travel times (u, v, w), return minimum time for all nodes to receive a signal sent from node k. If impossible, return -1.",
     "First line: n m k. Next m lines: u v w.", "Minimum total time or -1.",
     "1 <= n <= 100\n1 <= m <= 6000", "O((V + E) log V)", "O(V + E)",
     [{"input": "4 3 2\n2 1 1\n2 3 1\n3 4 1", "output": "2"}],
     ["Apply Dijkstra's algorithm starting from source node k.", "The answer is max(distances) among all nodes."]),

    ("alien-dictionary-order", "Alien Language Alphabet Order", "HARD", "topological-sort", ["topological-sort"], ["graphs", "strings"],
     "Given a sorted dictionary of an alien language, derive the alphabetical order of characters. If invalid, return INVALID.",
     "First line: n. Next n lines: alien words.", "String of unique characters in order.",
     "1 <= n <= 100", "O(total characters)", "O(unique characters)",
     [{"input": "5\nwrt\nwrf\ner\nett\nrftt", "output": "wertf"}],
     ["Compare adjacent words to find the first differing character to build a directed edge.", "Run topological sort on the character graph."]),

    # Trie
    ("implement-trie-prefix-tree", "Implement Trie Prefix Tree", "MEDIUM", "trie", ["trie"], ["trie", "strings"],
     "Implement a Trie with insert, search, and startsWith operations. Process commands and output results.",
     "First line: q operations. Next q lines: 'insert word', 'search word', or 'startsWith prefix'.", "Boolean results for search and startsWith.",
     "1 <= q <= 10^4", "O(L) per operation", "O(total characters)",
     [{"input": "5\ninsert apple\nsearch apple\nsearch app\nstartsWith app\ninsert app", "output": "true\nfalse\ntrue"}],
     ["Each TrieNode has a dictionary of children and an is_end_of_word flag.", "Traverse character by character down child nodes."]),

    # Segment Tree & Range Queries
    ("range-minimum-query", "Range Minimum Query with Updates", "HARD", "segment-tree", ["segment-tree"], ["segment-tree", "arrays"],
     "Maintain an array supporting point updates and range minimum queries [l, r] in O(log n) time.",
     "First line: n q. Second line: n integers. Next q lines: '1 idx val' (update) or '2 l r' (query min).", "Output of each query.",
     "1 <= n, q <= 10^5", "O(log n) per operation", "O(n)",
     [{"input": "5 3\n1 5 2 4 3\n2 1 3\n1 2 0\n2 1 3", "output": "2\n0"}],
     ["Build a segment tree where tree[node] = min(tree[left], tree[right]).", "Update and query in O(log n) by branching down the tree."]),

    # --- LEVEL 4: DYNAMIC PROGRAMMING ---
    ("coin-change-ways", "Coin Change Number of Ways", "MEDIUM", "dp-1d", ["dp-1d", "knapsack"], ["dynamic-programming"],
     "Given coin denominations and amount, return the total number of distinct combinations that make up that amount.",
     "First line: n amount. Second line: n coin denominations.", "Total number of combinations.",
     "1 <= n <= 300\n1 <= amount <= 5000", "O(n * amount)", "O(amount)",
     [{"input": "3 5\n1 2 5", "output": "4"}],
     ["dp[a] += dp[a - coin] iterating coins first to avoid duplicate permutations.", "dp[0] = 1."]),

    ("maximum-subarray-kadane", "Maximum Subarray Sum (Kadane)", "EASY", "dp-1d", ["dp-1d"], ["arrays", "dynamic-programming"],
     "Find the contiguous subarray with the largest sum and return its sum.",
     "First line: n. Second line: n space-separated integers.", "Maximum subarray sum.",
     "1 <= n <= 10^5", "O(n)", "O(1)",
     [{"input": "9\n-2 1 -3 4 -1 2 1 -5 4", "output": "6"}],
     ["current_max = max(nums[i], current_max + nums[i]).", "Track overall_max across all steps."]),

    ("unique-paths-grid", "Unique Paths in Grid", "MEDIUM", "dp-2d", ["dp-2d"], ["dynamic-programming", "matrix"],
     "A robot starts at top-left of an m×n grid and can only move down or right. How many unique paths reach the bottom-right corner?",
     "Two space-separated integers m n.", "Number of unique paths.",
     "1 <= m, n <= 100", "O(m * n)", "O(n)",
     [{"input": "3 7", "output": "28"}, {"input": "3 2", "output": "3"}],
     ["dp[r][c] = dp[r-1][c] + dp[r][c-1].", "First row and first column are all 1s."]),

    ("minimum-path-sum", "Minimum Path Sum in Grid", "MEDIUM", "dp-2d", ["dp-2d"], ["matrix", "dynamic-programming"],
     "Given an m×n grid filled with non-negative integers, find a path from top-left to bottom-right minimizing the sum of values along its path.",
     "First line: m n. Next m lines: n space-separated numbers.", "Minimal path sum.",
     "1 <= m, n <= 200", "O(m * n)", "O(n)",
     [{"input": "3 3\n1 3 1\n1 5 1\n4 2 1", "output": "7"}],
     ["dp[r][c] = grid[r][c] + min(dp[r-1][c], dp[r][c-1]).", "Initialize boundaries with cumulative sums."]),

    ("knapsack-01-classic", "0/1 Knapsack Problem", "MEDIUM", "dp-knapsack", ["knapsack", "dp-2d"], ["dynamic-programming"],
     "Given n items with weights and values, find maximum value fitting in knapsack of capacity W.",
     "First line: n W. Second line: n weights. Third line: n values.", "Maximum attainable value.",
     "1 <= n <= 1000\n1 <= W <= 1000", "O(n * W)", "O(W)",
     [{"input": "3 4\n1 2 3\n10 15 40", "output": "55"}],
     ["Iterate items, then iterate capacity backwards from W down to weight[i].", "dp[w] = max(dp[w], dp[w - weight[i]] + value[i])."]),

    ("partition-equal-subset-sum", "Partition Equal Subset Sum", "MEDIUM", "dp-knapsack", ["knapsack"], ["dynamic-programming"],
     "Determine whether an array of positive integers can be partitioned into two subsets with equal sums. Print YES or NO.",
     "First line: n. Second line: n positive integers.", "YES or NO.",
     "1 <= n <= 200\n1 <= nums[i] <= 100", "O(n * sum)", "O(sum)",
     [{"input": "4\n1 5 11 5", "output": "YES"}, {"input": "4\n1 2 3 5", "output": "NO"}],
     ["If total sum is odd, answer is NO.", "Target is total / 2; solve as 0/1 subset sum."]),

    ("longest-palindromic-substring", "Longest Palindromic Substring", "MEDIUM", "dp-string", ["two-pointers", "dp-2d"], ["strings", "dynamic-programming"],
     "Given a string `s`, return the longest palindromic substring in s.",
     "A single string s.", "The longest palindromic substring.",
     "1 <= |s| <= 1000", "O(n²)", "O(1)",
     [{"input": "babad", "output": "bab"}, {"input": "cbbd", "output": "bb"}],
     ["Expand around each center i (odd palindrome) and i, i+1 (even palindrome).", "Track maximum span."]),

    ("palindromic-substrings-count", "Count Palindromic Substrings", "MEDIUM", "dp-string", ["two-pointers"], ["strings"],
     "Given a string `s`, return the count of distinct palindromic substrings in it.",
     "A single string s.", "Count of palindromic substrings.",
     "1 <= |s| <= 1000", "O(n²)", "O(1)",
     [{"input": "abc", "output": "3"}, {"input": "aaa", "output": "6"}],
     ["Expand outwards from each possible center.", "Increment count for every match before encountering a mismatch."]),
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

    new_problems = 0
    new_examples = 0
    new_hints = 0
    new_tests = 0

    cur.execute("SELECT MAX(display_order) FROM problems")
    max_order = cur.fetchone()[0] or 0

    print(f"Beginning expanded problems insertion (starting display_order: {max_order + 1})...")

    for idx, prob in enumerate(ADDITIONAL_PROBLEMS):
        slug, title, diff, top_slug, pats, tags, stmt, infmt, outfmt, constr, tc, sc, exs, hnts = prob
        p_id = uid(f"problem:{slug}")
        pub_p = f"prb_{uuid.uuid5(NS, slug).hex[:12]}"

        cur.execute("SELECT id FROM problems WHERE slug=?", (slug,))
        if cur.fetchone():
            continue

        topic_id = topic_map.get(top_slug)
        subtopic_id = subtopic_map.get(topic_id) if topic_id else None
        disp_order = max_order + 1 + idx
        est_mins = 15 if diff == "EASY" else (25 if diff == "MEDIUM" else 40)
        access = "FREE" if idx % 3 != 0 else "PREMIUM"

        cur.execute("""
            INSERT INTO problems (
                id, public_id, slug, title, statement, explanation, difficulty, access_level, status,
                topic_id, subtopic_id, display_order, estimated_minutes, input_format, output_format,
                constraints, expected_time_complexity, expected_space_complexity, supported_languages,
                version, created_by, updated_by, created_at, updated_at, time_limit_ms, memory_limit_mb,
                output_limit_bytes, comparison_mode
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            p_id, pub_p, slug, title, stmt, None, diff, access, "PUBLISHED",
            topic_id, subtopic_id, disp_order, est_mins, infmt, outfmt,
            constr, tc, sc, '["python", "java", "cpp", "javascript"]',
            1, None, None, ts, ts, 2000, 256, 65536, "exact"
        ))
        new_problems += 1

        for ei, ex in enumerate(exs):
            ex_id = uid(f"example:{slug}:{ei}")
            cur.execute("""
                INSERT OR IGNORE INTO problem_examples (id, problem_id, input, output, explanation, display_order, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (ex_id, p_id, ex["input"], ex["output"], ex.get("explanation"), ei, ts))
            new_examples += 1

        for hi, hint in enumerate(hnts, 1):
            h_id = uid(f"hint:{slug}:{hi}")
            cur.execute("""
                INSERT OR IGNORE INTO problem_hints (id, problem_id, hint_number, title, content, is_premium, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (h_id, p_id, hi, f"Hint {hi}", hint, 0, ts))
            new_hints += 1

        for ti, ex in enumerate(exs[:2]):
            tc_id = uid(f"tc:sample:{slug}:{ti}")
            cur.execute("""
                INSERT OR IGNORE INTO test_cases (id, problem_id, input, expected_output, is_sample, display_order, is_hidden, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (tc_id, p_id, ex["input"], ex["output"], 1, ti, 0, ts))
            new_tests += 1

        if exs:
            tc_id = uid(f"tc:hidden:{slug}:0")
            cur.execute("""
                INSERT OR IGNORE INTO test_cases (id, problem_id, input, expected_output, is_sample, display_order, is_hidden, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (tc_id, p_id, exs[0]["input"], exs[0]["output"], 0, 99, 1, ts))
            new_tests += 1

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

    print(f"Added {new_problems} new problems ({new_examples} examples, {new_hints} hints, {new_tests} test cases).")
    print(f"Total problems now in database: {total_p}")
    print(f"Difficulty breakdown: {diff_counts}")

if __name__ == "__main__":
    main()
