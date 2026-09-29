/**
 * Types and interfaces for DSAapp Interactive Visualizer Engine.
 */

export type VisualizerType =
  | "array"
  | "linked-list"
  | "stack"
  | "queue"
  | "binary-search"
  | "sorting"
  | "binary-tree"
  | "bst"
  | "heap"
  | "graph-bfs"
  | "graph-dfs"
  | "two-pointers"
  | "sliding-window"
  | "recursion";

export interface VisualizerFrame {
  stepIndex: number;
  description: string;
  dataState: any;
  highlighted?: (number | string)[];
  activeIndices?: (number | string)[];
  pointers?: Record<string, number | string>;
  codeLine?: number;
  isCompleted?: boolean;
}

export interface VisualizerMetadata {
  id: VisualizerType;
  title: string;
  category: "Fundamentals" | "Algorithms" | "Trees & Graphs" | "Patterns";
  timeComplexity: string;
  spaceComplexity: string;
  description: string;
  availableOperations: string[];
}
