import { VisualizerFrame } from "../types.ts";

export function generateBubbleSortFrames(arr: number[]): VisualizerFrame[] {
  const state = [...arr.slice(0, 10)];
  const n = state.length;
  const frames: VisualizerFrame[] = [];

  frames.push({
    stepIndex: 0,
    description: `Initial unsorted array of ${n} elements. Starting Bubble Sort.`,
    dataState: [...state],
    pointers: {},
  });

  for (let i = 0; i < n - 1; i++) {
    for (let j = 0; j < n - i - 1; j++) {
      const willSwap = state[j] > state[j + 1];

      frames.push({
        stepIndex: frames.length,
        description: `Comparing index ${j} (${state[j]}) and index ${j + 1} (${state[j + 1]}). ${willSwap ? "Needs swap." : "In correct order."}`,
        dataState: [...state],
        pointers: { j, next: j + 1 },
        highlighted: [j, j + 1],
      });

      if (willSwap) {
        const temp = state[j];
        state[j] = state[j + 1];
        state[j + 1] = temp;

        frames.push({
          stepIndex: frames.length,
          description: `Swapped ${state[j + 1]} and ${state[j]}.`,
          dataState: [...state],
          pointers: { j, next: j + 1 },
          activeIndices: [j, j + 1],
        });
      }
    }
  }

  frames.push({
    stepIndex: frames.length,
    description: `Bubble Sort complete! All ${n} elements are sorted in non-decreasing order. Worst-case time: O(n^2).`,
    dataState: [...state],
    pointers: {},
    isCompleted: true,
  });

  return frames;
}
