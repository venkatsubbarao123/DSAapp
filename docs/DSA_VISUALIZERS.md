# DSA Visualizers Engine Specification

**Component**: Interactive Algorithm & Data Structure Visualizer  
**Phase**: Phase 6  
**Status**: Production-Grade / Active  

---

## 1. Engine Design & Architecture

The DSA Visualizer Engine is a deterministic, frame-based simulation system built with React and TypeScript. Unlike canvas-only or black-box visualizer widgets, this engine generates discrete state snapshots (frames) before playback.

### Core Architecture Principles:
1. **Pure Deterministic State Generation**: Algorithm generators (`frontend/src/features/visualizers/algorithms/`) take inputs and synchronously compute an immutable array of `VisualizerFrame` objects.
2. **Safe Input Bounds**: Every visualizer enforces input caps (maximum 15 elements, values between -99 and 999, recursion depth $\le 10$) to prevent browser memory exhaustion and UI freezes.
3. **Discrete Bidirectional Stepping**: Students can play, pause, step forward, step backward, or jump to any step index via a progress scrubber.
4. **Variable Playback Speed**: Supports 0.5x, 1x, 2x, and 4x animation speeds.
5. **Multi-Model Data Visualization**: Visualizes Arrays, Linked Lists (with pointer arrows), Stacks, Queues, Binary Trees, Heaps, and Graphs (with adjacency nodes and visited sets).

---

## 2. Visualizer Catalog (14 Algorithms & Structures)

| ID | Name | Category | Big-O Time | Big-O Space | Visual Presentation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `array-linear` | Array & Linear Search | Linear | $O(N)$ | $O(1)$ | Indexed array cells with highlight and target match. |
| `linked-list` | Singly Linked List | Linear | $O(N)$ | $O(1)$ | Node cards connected by directional SVG arrows. |
| `stack` | Stack (LIFO) | Linear | $O(1)$ | $O(N)$ | Vertical stack container with Push, Pop, and Top pointer. |
| `queue` | Queue (FIFO) | Linear | $O(1)$ | $O(N)$ | Horizontal pipeline with Enqueue (tail) and Dequeue (head). |
| `binary-search` | Binary Search | Algorithmic | $O(\log N)$ | $O(1)$ | Low, Mid, and High pointer badges narrowing search window. |
| `sorting-bubble` | Bubble Sort | Algorithmic | $O(N^2)$ | $O(1)$ | Adjacent element swap comparisons and sorted partition. |
| `binary-tree-inorder` | Tree Inorder Traversal | Traversal | $O(N)$ | $O(H)$ | Binary tree hierarchy with active node and traversal output. |
| `bst-search` | BST Search | Trees & Graphs | $O(\log N)$ | $O(H)$ | Left/Right branch decision highlighting along tree depth. |
| `heap-min` | Min-Heap Operations | Trees & Graphs | $O(\log N)$ | $O(N)$ | Complete binary tree with Bubble-Up parent/child swaps. |
| `graph-bfs` | Graph BFS | Trees & Graphs | $O(V + E)$ | $O(V)$ | Graph nodes, frontier Queue, and Visited set panel. |
| `graph-dfs` | Graph DFS | Trees & Graphs | $O(V + E)$ | $O(V)$ | Graph nodes, recursive Call Stack, and backtracking. |
| `two-pointers` | Two Pointers | Algorithmic | $O(N)$ | $O(1)$ | Left & Right convergence pointers with running sum check. |
| `sliding-window` | Sliding Window | Algorithmic | $O(N)$ | $O(1)$ | Translucent bounding window moving across contiguous subarray. |
| `recursion-fib` | Recursion Call Stack | Algorithmic | $O(2^N)$ | $O(N)$ | Dynamic call stack frames with argument passing and return. |

---

## 3. Frame Data Contract (`VisualizerFrame`)

```typescript
export interface VisualizerFrame {
  stepIndex: number;
  description: string;
  dataState: any; // Type-specific state: array, pointers, nodes, stack, queue
  highlightIndices?: number[];
  activePointers?: Record<string, number | string>;
  codeLine?: number;
}
```

---

## 4. Integration with AI Tutor & Curriculum

The AI Tutor is context-aware of the visualizer catalog. When a student asks questions regarding algorithms (e.g. *"How does binary search eliminate half the array?"* or *"Explain breadth-first search"*), the AI response returns a structured `visualization_suggestion`:

```json
{
  "visualizer_id": "binary-search",
  "title": "Interactive Binary Search Visualizer",
  "reason": "Step through low, mid, and high pointer updates interactively to see search space halving."
}
```

The frontend renders a one-click button (`Open Visualizer →`) directly within the AI Tutor guidance card, routing the student to the active visualizer simulation.
