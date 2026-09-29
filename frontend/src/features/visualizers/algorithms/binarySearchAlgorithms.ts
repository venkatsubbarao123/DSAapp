import { VisualizerFrame } from "../types.ts";

export function generateBinarySearchFrames(arr: number[], target: number): VisualizerFrame[] {
  // Ensure array is sorted for binary search
  const sorted = [...arr.slice(0, 15)].sort((a, b) => a - b);
  const frames: VisualizerFrame[] = [];

  let low = 0;
  let high = sorted.length - 1;

  frames.push({
    stepIndex: 0,
    description: `Binary Search on sorted array of ${sorted.length} elements for target ${target}. Initial interval [low: 0, high: ${high}].`,
    dataState: [...sorted],
    pointers: { low: 0, high },
    highlighted: [low, high],
  });

  while (low <= high) {
    const mid = Math.floor((low + high) / 2);
    const midVal = sorted[mid];

    frames.push({
      stepIndex: frames.length,
      description: `Compute midpoint mid = floor((${low} + ${high}) / 2) = ${mid}. Inspecting sorted[${mid}] = ${midVal}.`,
      dataState: [...sorted],
      pointers: { low, mid, high },
      highlighted: [mid],
      activeIndices: [mid],
    });

    if (midVal === target) {
      frames.push({
        stepIndex: frames.length,
        description: `Target ${target} found at index ${mid}! Comparison matched: ${midVal} == ${target}.`,
        dataState: [...sorted],
        pointers: { match: mid },
        activeIndices: [mid],
        isCompleted: true,
      });
      return frames;
    } else if (midVal < target) {
      frames.push({
        stepIndex: frames.length,
        description: `Since sorted[${mid}] = ${midVal} < ${target}, target must lie in the right half. Updating low = ${mid + 1}.`,
        dataState: [...sorted],
        pointers: { low: mid + 1, high },
        highlighted: [mid],
      });
      low = mid + 1;
    } else {
      frames.push({
        stepIndex: frames.length,
        description: `Since sorted[${mid}] = ${midVal} > ${target}, target must lie in the left half. Updating high = ${mid - 1}.`,
        dataState: [...sorted],
        pointers: { low, high: mid - 1 },
        highlighted: [mid],
      });
      high = mid - 1;
    }
  }

  frames.push({
    stepIndex: frames.length,
    description: `Search interval empty (low > high). Target ${target} is not in the array. Binary search completed in O(log n) steps.`,
    dataState: [...sorted],
    pointers: {},
    isCompleted: true,
  });

  return frames;
}
