import { VisualizerFrame } from "../types.ts";

export function generateLinearSearchFrames(arr: number[], target: number): VisualizerFrame[] {
  const boundedArr = arr.slice(0, 15);
  const frames: VisualizerFrame[] = [];

  frames.push({
    stepIndex: 0,
    description: `Start linear search for target ${target} across ${boundedArr.length} elements.`,
    dataState: [...boundedArr],
    pointers: { i: 0 },
    highlighted: [],
  });

  for (let i = 0; i < boundedArr.length; i++) {
    const isMatch = boundedArr[i] === target;
    frames.push({
      stepIndex: frames.length,
      description: `Checking index ${i}: element ${boundedArr[i]} ${isMatch ? "matches target!" : "does not match."}`,
      dataState: [...boundedArr],
      pointers: { i },
      highlighted: [i],
      activeIndices: isMatch ? [i] : [],
      isCompleted: isMatch,
    });

    if (isMatch) {
      frames.push({
        stepIndex: frames.length,
        description: `Target ${target} found at index ${i}. Search completed in O(${i + 1}) steps.`,
        dataState: [...boundedArr],
        pointers: { match: i },
        activeIndices: [i],
        isCompleted: true,
      });
      return frames;
    }
  }

  frames.push({
    stepIndex: frames.length,
    description: `Target ${target} was not found after inspecting all ${boundedArr.length} elements. Time complexity: O(n).`,
    dataState: [...boundedArr],
    pointers: {},
    highlighted: [],
    isCompleted: true,
  });

  return frames;
}

export function generateArrayInsertFrames(arr: number[], index: number, value: number): VisualizerFrame[] {
  const current = arr.slice(0, 12);
  const targetIdx = Math.max(0, Math.min(index, current.length));
  const frames: VisualizerFrame[] = [];

  frames.push({
    stepIndex: 0,
    description: `Preparing to insert value ${value} at index ${targetIdx}.`,
    dataState: [...current],
    pointers: { insertAt: targetIdx },
  });

  const state = [...current, 0];
  for (let j = state.length - 1; j > targetIdx; j--) {
    state[j] = state[j - 1];
    frames.push({
      stepIndex: frames.length,
      description: `Shifting element ${state[j]} from index ${j - 1} to index ${j}.`,
      dataState: [...state],
      pointers: { shift: j },
      highlighted: [j, j - 1],
    });
  }

  state[targetIdx] = value;
  frames.push({
    stepIndex: frames.length,
    description: `Inserted ${value} at index ${targetIdx}. Insertion complete!`,
    dataState: [...state],
    activeIndices: [targetIdx],
    pointers: { inserted: targetIdx },
    isCompleted: true,
  });

  return frames;
}
