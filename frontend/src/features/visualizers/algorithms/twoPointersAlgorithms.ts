import { VisualizerFrame } from "../types.ts";

export function generateTwoPointersFrames(arr: number[], target: number): VisualizerFrame[] {
  const sorted = [...arr.slice(0, 12)].sort((a, b) => a - b);
  const frames: VisualizerFrame[] = [];

  let left = 0;
  let right = sorted.length - 1;

  frames.push({
    stepIndex: 0,
    description: `Two Pointers search for target sum ${target}. Initialize left pointer at 0 (${sorted[0]}) and right pointer at ${right} (${sorted[right]}).`,
    dataState: [...sorted],
    pointers: { left, right },
    highlighted: [left, right],
  });

  while (left < right) {
    const currentSum = sorted[left] + sorted[right];

    frames.push({
      stepIndex: frames.length,
      description: `Evaluating sum at left=${left} (${sorted[left]}) and right=${right} (${sorted[right]}): ${sorted[left]} + ${sorted[right]} = ${currentSum}.`,
      dataState: [...sorted],
      pointers: { left, right },
      highlighted: [left, right],
      activeIndices: [left, right],
    });

    if (currentSum === target) {
      frames.push({
        stepIndex: frames.length,
        description: `Target pair found! Elements ${sorted[left]} (idx ${left}) and ${sorted[right]} (idx ${right}) sum to ${target}. Time: O(n).`,
        dataState: [...sorted],
        pointers: { matchLeft: left, matchRight: right },
        activeIndices: [left, right],
        isCompleted: true,
      });
      return frames;
    } else if (currentSum < target) {
      frames.push({
        stepIndex: frames.length,
        description: `Current sum ${currentSum} < ${target}. To increase the sum, advance left pointer from ${left} to ${left + 1}.`,
        dataState: [...sorted],
        pointers: { left: left + 1, right },
        highlighted: [left + 1, right],
      });
      left++;
    } else {
      frames.push({
        stepIndex: frames.length,
        description: `Current sum ${currentSum} > ${target}. To decrease the sum, decrement right pointer from ${right} to ${right - 1}.`,
        dataState: [...sorted],
        pointers: { left, right: right - 1 },
        highlighted: [left, right - 1],
      });
      right--;
    }
  }

  frames.push({
    stepIndex: frames.length,
    description: `Pointers met (left >= right). No two elements in the array sum to ${target}.`,
    dataState: [...sorted],
    pointers: {},
    isCompleted: true,
  });

  return frames;
}
