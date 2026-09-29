import { VisualizerFrame } from "../types.ts";

export function generateMinHeapFrames(initialArr: number[]): VisualizerFrame[] {
  // Heap representation as an array where leftChild = 2*i + 1, rightChild = 2*i + 2
  const heap = [...initialArr.slice(0, 6)].sort((a, b) => a - b);
  const frames: VisualizerFrame[] = [];

  frames.push({
    stepIndex: 0,
    description: `Min-Heap array: [${heap.join(", ")}]. Root is min element heap[0] = ${heap[0]}.`,
    dataState: [...heap],
    pointers: { min: 0 },
    highlighted: [0],
  });

  // Insert 3 and bubble up
  const newVal = 3;
  heap.push(newVal);
  let idx = heap.length - 1;

  frames.push({
    stepIndex: frames.length,
    description: `Inserted new element ${newVal} at index ${idx} (end of array). Beginning bubble-up (sift-up).`,
    dataState: [...heap],
    pointers: { insert: idx },
    highlighted: [idx],
    activeIndices: [idx],
  });

  while (idx > 0) {
    const parentIdx = Math.floor((idx - 1) / 2);
    if (heap[idx] < heap[parentIdx]) {
      frames.push({
        stepIndex: frames.length,
        description: `heap[${idx}] = ${heap[idx]} < heap[${parentIdx}] = ${heap[parentIdx]}. Swapping with parent to restore heap invariant.`,
        dataState: [...heap],
        pointers: { child: idx, parent: parentIdx },
        highlighted: [idx, parentIdx],
      });

      const temp = heap[idx];
      heap[idx] = heap[parentIdx];
      heap[parentIdx] = temp;

      idx = parentIdx;

      frames.push({
        stepIndex: frames.length,
        description: `Swapped. Element is now at index ${idx}.`,
        dataState: [...heap],
        pointers: { current: idx },
        activeIndices: [idx],
      });
    } else {
      break;
    }
  }

  frames.push({
    stepIndex: frames.length,
    description: `Min-Heap property restored! Array: [${heap.join(", ")}]. Insert took O(log n) time.`,
    dataState: [...heap],
    pointers: { min: 0 },
    isCompleted: true,
  });

  return frames;
}

export function generateGraphBfsFrames(): VisualizerFrame[] {
  // Directed acyclic or simple undirected graph with 5 vertices
  const adj: Record<number, number[]> = {
    1: [2, 3],
    2: [1, 4, 5],
    3: [1, 5],
    4: [2],
    5: [2, 3],
  };

  const frames: VisualizerFrame[] = [];
  const queue: number[] = [1];
  const visited = new Set<number>([1]);
  const traversalOrder: number[] = [];

  frames.push({
    stepIndex: 0,
    description: "Graph BFS starting from Node 1. Queue: [1], Visited: {1}.",
    dataState: { queue: [...queue], visited: Array.from(visited), traversal: [] },
    pointers: { start: 1 },
    highlighted: [1],
  });

  while (queue.length > 0) {
    const curr = queue.shift()!;
    traversalOrder.push(curr);

    frames.push({
      stepIndex: frames.length,
      description: `Dequeued Node ${curr}. Expanding neighbors: [${adj[curr].join(", ")}].`,
      dataState: { queue: [...queue], visited: Array.from(visited), traversal: [...traversalOrder] },
      pointers: { current: curr },
      activeIndices: [curr],
    });

    for (const neighbor of adj[curr]) {
      if (!visited.has(neighbor)) {
        visited.add(neighbor);
        queue.push(neighbor);

        frames.push({
          stepIndex: frames.length,
          description: `Discovered unvisited neighbor Node ${neighbor}. Added to Queue. Queue: [${queue.join(", ")}].`,
          dataState: { queue: [...queue], visited: Array.from(visited), traversal: [...traversalOrder] },
          highlighted: [neighbor],
        });
      }
    }
  }

  frames.push({
    stepIndex: frames.length,
    description: `BFS Traversal complete! Order: [${traversalOrder.join(" -> ")}]. Explored V+E vertices and edges in O(V + E) time.`,
    dataState: { queue: [], visited: Array.from(visited), traversal: [...traversalOrder] },
    isCompleted: true,
  });

  return frames;
}

export function generateGraphDfsFrames(): VisualizerFrame[] {
  const adj: Record<number, number[]> = {
    1: [2, 3],
    2: [4, 5],
    3: [],
    4: [],
    5: [],
  };

  const frames: VisualizerFrame[] = [];
  const visited = new Set<number>();
  const stack: number[] = [];
  const order: number[] = [];

  function dfs(u: number) {
    visited.add(u);
    stack.push(u);
    order.push(u);

    frames.push({
      stepIndex: frames.length,
      description: `DFS visiting Node ${u}. Pushed to call stack. Stack: [${stack.join(", ")}].`,
      dataState: { stack: [...stack], visited: Array.from(visited), order: [...order] },
      pointers: { current: u },
      activeIndices: [u],
    });

    for (const v of adj[u]) {
      if (!visited.has(v)) {
        dfs(v);
      }
    }

    stack.pop();
    frames.push({
      stepIndex: frames.length,
      description: `Backtracking from Node ${u}. Popped from call stack. Stack: [${stack.join(", ")}].`,
      dataState: { stack: [...stack], visited: Array.from(visited), order: [...order] },
    });
  }

  dfs(1);

  frames.push({
    stepIndex: frames.length,
    description: `DFS traversal complete! Order: [${order.join(" -> ")}]. Time: O(V + E), Space: O(V) stack.`,
    dataState: { stack: [], visited: Array.from(visited), order: [...order] },
    isCompleted: true,
  });

  return frames;
}

export function generateRecursionFrames(n: number = 4): VisualizerFrame[] {
  const val = Math.max(1, Math.min(n, 5));
  const frames: VisualizerFrame[] = [];
  const callStack: string[] = [];

  function fib(k: number): number {
    callStack.push(`fib(${k})`);
    frames.push({
      stepIndex: frames.length,
      description: `Call fib(${k}): Pushed new stack frame. Call stack depth = ${callStack.length}.`,
      dataState: { stack: [...callStack], result: null },
      pointers: { current: `fib(${k})` },
    });

    if (k <= 1) {
      frames.push({
        stepIndex: frames.length,
        description: `Base case reached: fib(${k}) returns ${k}.`,
        dataState: { stack: [...callStack], result: k },
        activeIndices: [callStack.length - 1],
      });
      callStack.pop();
      return k;
    }

    const a = fib(k - 1);
    const b = fib(k - 2);
    const ans = a + b;

    frames.push({
      stepIndex: frames.length,
      description: `Computed fib(${k}) = fib(${k - 1}) + fib(${k - 2}) = ${a} + ${b} = ${ans}. Popping frame.`,
      dataState: { stack: [...callStack], result: ans },
    });

    callStack.pop();
    return ans;
  }

  const finalAns = fib(val);

  frames.push({
    stepIndex: frames.length,
    description: `Recursion finished! fib(${val}) = ${finalAns}. Max stack depth = ${val}.`,
    dataState: { stack: [], result: finalAns },
    isCompleted: true,
  });

  return frames;
}
