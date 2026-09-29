import { VisualizerFrame } from "../types.ts";

export function generateStackFrames(initialValues: number[]): VisualizerFrame[] {
  const stack = [...initialValues.slice(0, 6)];
  const frames: VisualizerFrame[] = [];

  frames.push({
    stepIndex: 0,
    description: `Stack initialized with ${stack.length} elements (LIFO: Last-In, First-Out). Top is at right/top.`,
    dataState: [...stack],
    pointers: stack.length > 0 ? { top: stack.length - 1 } : {},
  });

  // Push 42
  const pushVal = 42;
  stack.push(pushVal);
  frames.push({
    stepIndex: frames.length,
    description: `PUSH operation: Added ${pushVal} to the top of the stack. O(1) time.`,
    dataState: [...stack],
    pointers: { top: stack.length - 1 },
    highlighted: [stack.length - 1],
    activeIndices: [stack.length - 1],
  });

  // Peek top
  frames.push({
    stepIndex: frames.length,
    description: `PEEK operation: Inspecting top element without removing it -> ${stack[stack.length - 1]}. O(1) time.`,
    dataState: [...stack],
    pointers: { top: stack.length - 1 },
    highlighted: [stack.length - 1],
  });

  // Pop
  const popped = stack.pop();
  frames.push({
    stepIndex: frames.length,
    description: `POP operation: Removed top element ${popped} from stack. New top is ${stack[stack.length - 1]}. O(1) time.`,
    dataState: [...stack],
    pointers: { top: stack.length - 1 },
    activeIndices: [stack.length - 1],
    isCompleted: true,
  });

  return frames;
}

export function generateQueueFrames(initialValues: number[]): VisualizerFrame[] {
  const queue = [...initialValues.slice(0, 6)];
  const frames: VisualizerFrame[] = [];

  frames.push({
    stepIndex: 0,
    description: `Queue initialized with ${queue.length} elements (FIFO: First-In, First-Out). Front at index 0, Rear at index ${queue.length - 1}.`,
    dataState: [...queue],
    pointers: queue.length > 0 ? { front: 0, rear: queue.length - 1 } : {},
  });

  // Enqueue 99
  const enqVal = 99;
  queue.push(enqVal);
  frames.push({
    stepIndex: frames.length,
    description: `ENQUEUE operation: Appended ${enqVal} to the rear of the queue. O(1) time.`,
    dataState: [...queue],
    pointers: { front: 0, rear: queue.length - 1 },
    highlighted: [queue.length - 1],
    activeIndices: [queue.length - 1],
  });

  // Dequeue
  const dequeued = queue.shift();
  frames.push({
    stepIndex: frames.length,
    description: `DEQUEUE operation: Removed front element ${dequeued}. Front element is now ${queue[0]}. O(1) time.`,
    dataState: [...queue],
    pointers: { front: 0, rear: queue.length - 1 },
    activeIndices: [0],
    isCompleted: true,
  });

  return frames;
}
