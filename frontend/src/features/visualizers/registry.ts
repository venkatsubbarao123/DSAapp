import { VisualizerFrame, VisualizerMetadata, VisualizerType } from "./types.ts";
import { generateArrayInsertFrames, generateLinearSearchFrames } from "./algorithms/arrayAlgorithms.ts";
import { generateBinarySearchFrames } from "./algorithms/binarySearchAlgorithms.ts";
import { generateBubbleSortFrames } from "./algorithms/sortingAlgorithms.ts";
import { generateTwoPointersFrames } from "./algorithms/twoPointersAlgorithms.ts";
import { generateSlidingWindowFrames } from "./algorithms/slidingWindowAlgorithms.ts";
import { generateQueueFrames, generateStackFrames } from "./algorithms/stackQueueAlgorithms.ts";
import { generateLinkedListFrames } from "./algorithms/linkedListAlgorithms.ts";
import { generateBinaryTreeTraversalFrames, generateBstSearchFrames } from "./algorithms/treeAlgorithms.ts";
import {
  generateGraphBfsFrames,
  generateGraphDfsFrames,
  generateMinHeapFrames,
  generateRecursionFrames,
} from "./algorithms/heapAndGraphAlgorithms.ts";

export const VISUALIZER_CATALOG: VisualizerMetadata[] = [
  {
    id: "array",
    title: "Array Operations",
    category: "Fundamentals",
    timeComplexity: "O(1) access, O(n) insert/delete",
    spaceComplexity: "O(n)",
    description: "Contiguous memory layout, element shifts on insertion, and linear search.",
    availableOperations: ["Linear Search", "Insert at Index"],
  },
  {
    id: "linked-list",
    title: "Singly Linked List",
    category: "Fundamentals",
    timeComplexity: "O(1) head insert, O(n) access",
    spaceComplexity: "O(n)",
    description: "Node-based non-contiguous data structure connected via next pointers.",
    availableOperations: ["Traverse List", "Insert at Head"],
  },
  {
    id: "stack",
    title: "Stack (LIFO)",
    category: "Fundamentals",
    timeComplexity: "O(1) Push, Pop, Peek",
    spaceComplexity: "O(n)",
    description: "Last-In, First-Out sequence essential for parsing, backtracking, and expression evaluation.",
    availableOperations: ["Push & Pop Sequence"],
  },
  {
    id: "queue",
    title: "Queue (FIFO)",
    category: "Fundamentals",
    timeComplexity: "O(1) Enqueue, Dequeue",
    spaceComplexity: "O(n)",
    description: "First-In, First-Out buffer fundamental for BFS and task scheduling.",
    availableOperations: ["Enqueue & Dequeue"],
  },
  {
    id: "binary-search",
    title: "Binary Search",
    category: "Algorithms",
    timeComplexity: "O(log n)",
    spaceComplexity: "O(1)",
    description: "Logarithmic search on monotonic sorted arrays via search space halving.",
    availableOperations: ["Search Target Value"],
  },
  {
    id: "sorting",
    title: "Sorting (Bubble Sort)",
    category: "Algorithms",
    timeComplexity: "O(n^2) worst/avg, O(n) best",
    spaceComplexity: "O(1)",
    description: "Pairwise comparisons and adjacent element swaps.",
    availableOperations: ["Sort Array"],
  },
  {
    id: "binary-tree",
    title: "Binary Tree Traversal",
    category: "Trees & Graphs",
    timeComplexity: "O(n)",
    spaceComplexity: "O(h)",
    description: "Recursive Inorder (Left -> Root -> Right) node visitation.",
    availableOperations: ["Inorder Traversal"],
  },
  {
    id: "bst",
    title: "Binary Search Tree",
    category: "Trees & Graphs",
    timeComplexity: "O(h) where h <= n",
    spaceComplexity: "O(h)",
    description: "Sorted tree invariant: all left descendents < root < all right descendents.",
    availableOperations: ["Search Target Value"],
  },
  {
    id: "heap",
    title: "Min-Heap",
    category: "Trees & Graphs",
    timeComplexity: "O(log n) Insert, O(1) Min",
    spaceComplexity: "O(n)",
    description: "Complete binary tree satisfying the heap invariant: parent <= children.",
    availableOperations: ["Insert & Bubble-Up"],
  },
  {
    id: "graph-bfs",
    title: "Graph BFS",
    category: "Trees & Graphs",
    timeComplexity: "O(V + E)",
    spaceComplexity: "O(V)",
    description: "Breadth-First Search level-by-level exploration using a FIFO queue.",
    availableOperations: ["BFS from Node 1"],
  },
  {
    id: "graph-dfs",
    title: "Graph DFS",
    category: "Trees & Graphs",
    timeComplexity: "O(V + E)",
    spaceComplexity: "O(V)",
    description: "Depth-First Search recursive exploration and backtracking with a call stack.",
    availableOperations: ["DFS from Node 1"],
  },
  {
    id: "two-pointers",
    title: "Two Pointers Pattern",
    category: "Patterns",
    timeComplexity: "O(n)",
    spaceComplexity: "O(1)",
    description: "Synchronized left and right pointer convergence for sorted target pair matching.",
    availableOperations: ["Find Target Sum Pair"],
  },
  {
    id: "sliding-window",
    title: "Sliding Window Pattern",
    category: "Patterns",
    timeComplexity: "O(n)",
    spaceComplexity: "O(1)",
    description: "Dynamic window boundary adjustments to optimize contiguous subarray queries.",
    availableOperations: ["Max Subarray of Size K"],
  },
  {
    id: "recursion",
    title: "Recursion & Call Stack",
    category: "Patterns",
    timeComplexity: "O(2^n)",
    spaceComplexity: "O(n) stack",
    description: "Visualizing function frame pushes, base case returns, and stack frame popping.",
    availableOperations: ["Fibonacci Call Stack"],
  },
];

export function getVisualizerFrames(
  type: VisualizerType,
  customParams?: Record<string, any>
): VisualizerFrame[] {
  const p = customParams || {};

  switch (type) {
    case "array":
      if (p.operation === "insert") {
        return generateArrayInsertFrames(p.array || [10, 20, 30, 40, 50], p.index ?? 2, p.value ?? 99);
      }
      return generateLinearSearchFrames(p.array || [14, 28, 42, 56, 70, 84], p.target ?? 42);

    case "binary-search":
      return generateBinarySearchFrames(p.array || [2, 7, 11, 15, 23, 34, 56, 72, 89], p.target ?? 23);

    case "sorting":
      return generateBubbleSortFrames(p.array || [45, 12, 85, 32, 89, 39, 69, 22]);

    case "two-pointers":
      return generateTwoPointersFrames(p.array || [1, 3, 4, 7, 11, 15, 19], p.target ?? 15);

    case "sliding-window":
      return generateSlidingWindowFrames(p.array || [2, 1, 5, 1, 3, 2, 8, 4], p.k ?? 3);

    case "stack":
      return generateStackFrames(p.initial || [10, 20, 30]);

    case "queue":
      return generateQueueFrames(p.initial || [10, 20, 30]);

    case "linked-list":
      return generateLinkedListFrames(p.initial || [12, 99, 37, 45, 80]);

    case "binary-tree":
      return generateBinaryTreeTraversalFrames();

    case "bst":
      return generateBstSearchFrames(p.target ?? 60);

    case "heap":
      return generateMinHeapFrames(p.array || [4, 10, 15, 20, 25]);

    case "graph-bfs":
      return generateGraphBfsFrames();

    case "graph-dfs":
      return generateGraphDfsFrames();

    case "recursion":
      return generateRecursionFrames(p.n ?? 4);

    default:
      return generateLinearSearchFrames([1, 2, 3, 4, 5], 3);
  }
}
