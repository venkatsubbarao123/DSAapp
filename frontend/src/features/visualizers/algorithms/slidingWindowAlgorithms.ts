import { VisualizerFrame } from "../types.ts";

export function generateSlidingWindowFrames(arr: number[], k: number): VisualizerFrame[] {
  const boundedArr = arr.slice(0, 12);
  const windowSize = Math.max(1, Math.min(k, boundedArr.length));
  const frames: VisualizerFrame[] = [];

  frames.push({
    stepIndex: 0,
    description: `Sliding Window: Finding maximum sum subarray of fixed size k=${windowSize}.`,
    dataState: [...boundedArr],
    pointers: {},
  });

  // Compute sum of initial window
  let windowSum = 0;
  for (let i = 0; i < windowSize; i++) {
    windowSum += boundedArr[i];
  }
  let maxSum = windowSum;
  let bestStart = 0;

  const initialIndices = Array.from({ length: windowSize }, (_, i) => i);
  frames.push({
    stepIndex: frames.length,
    description: `Initial window [0..${windowSize - 1}] sum = ${windowSum}. Current maximum = ${maxSum}.`,
    dataState: [...boundedArr],
    pointers: { left: 0, right: windowSize - 1 },
    highlighted: initialIndices,
    activeIndices: initialIndices,
  });

  // Slide window
  for (let i = windowSize; i < boundedArr.length; i++) {
    const leavingIdx = i - windowSize;
    const leavingVal = boundedArr[leavingIdx];
    const enteringIdx = i;
    const enteringVal = boundedArr[enteringIdx];

    windowSum = windowSum - leavingVal + enteringVal;
    const isNewMax = windowSum > maxSum;
    if (isNewMax) {
      maxSum = windowSum;
      bestStart = leavingIdx + 1;
    }

    const currentWindowIndices = Array.from({ length: windowSize }, (_, idx) => leavingIdx + 1 + idx);

    frames.push({
      stepIndex: frames.length,
      description: `Slide window right: subtract ${leavingVal} (idx ${leavingIdx}), add ${enteringVal} (idx ${enteringIdx}). New sum = ${windowSum}. ${isNewMax ? `New Max Found: ${maxSum}!` : `Max remains ${maxSum}.`}`,
      dataState: [...boundedArr],
      pointers: { left: leavingIdx + 1, right: enteringIdx },
      highlighted: currentWindowIndices,
      activeIndices: isNewMax ? currentWindowIndices : [],
    });
  }

  const optimalWindowIndices = Array.from({ length: windowSize }, (_, idx) => bestStart + idx);
  frames.push({
    stepIndex: frames.length,
    description: `Sliding Window complete! Maximum subarray sum of size ${windowSize} is ${maxSum} (starting at index ${bestStart}). Time: O(n).`,
    dataState: [...boundedArr],
    pointers: { bestStart },
    highlighted: optimalWindowIndices,
    activeIndices: optimalWindowIndices,
    isCompleted: true,
  });

  return frames;
}
