import { VisualizerFrame } from "../types.ts";

export interface TreeNodeData {
  id: number;
  val: number;
  leftId: number | null;
  rightId: number | null;
  x: number;
  y: number;
}

export function generateBinaryTreeTraversalFrames(): VisualizerFrame[] {
  // Balanced sample binary tree:
  //         1
  //       /   \
  //      2     3
  //     / \   / \
  //    4   5 6   7
  const treeNodes: TreeNodeData[] = [
    { id: 1, val: 1, leftId: 2, rightId: 3, x: 200, y: 40 },
    { id: 2, val: 2, leftId: 4, rightId: 5, x: 100, y: 100 },
    { id: 3, val: 3, leftId: 6, rightId: 7, x: 300, y: 100 },
    { id: 4, val: 4, leftId: null, rightId: null, x: 50, y: 160 },
    { id: 5, val: 5, leftId: null, rightId: null, x: 150, y: 160 },
    { id: 6, val: 6, leftId: null, rightId: null, x: 250, y: 160 },
    { id: 7, val: 7, leftId: null, rightId: null, x: 350, y: 160 },
  ];

  const frames: VisualizerFrame[] = [];
  frames.push({
    stepIndex: 0,
    description: "Binary Tree: Inorder traversal (Left -> Root -> Right).",
    dataState: { nodes: treeNodes, visitedOrder: [] },
  });

  const inorderSequence = [4, 2, 5, 1, 6, 3, 7];
  const visited: number[] = [];

  for (const nodeId of inorderSequence) {
    visited.push(nodeId);
    frames.push({
      stepIndex: frames.length,
      description: `Inorder visit: Processed Node(${nodeId}). Traversal order so far: [${visited.join(", ")}].`,
      dataState: { nodes: treeNodes, visitedOrder: [...visited] },
      highlighted: [nodeId],
      activeIndices: [nodeId],
    });
  }

  frames.push({
    stepIndex: frames.length,
    description: `Inorder traversal complete: [${visited.join(", ")}]. Visited all 7 nodes in O(n) time.`,
    dataState: { nodes: treeNodes, visitedOrder: [...visited] },
    isCompleted: true,
  });

  return frames;
}

export function generateBstSearchFrames(target: number): VisualizerFrame[] {
  // BST:
  //         50
  //       /    \
  //      30     70
  //     /  \   /  \
  //    20  40 60  80
  const bstNodes: TreeNodeData[] = [
    { id: 50, val: 50, leftId: 30, rightId: 70, x: 200, y: 40 },
    { id: 30, val: 30, leftId: 20, rightId: 40, x: 100, y: 100 },
    { id: 70, val: 70, leftId: 60, rightId: 80, x: 300, y: 100 },
    { id: 20, val: 20, leftId: null, rightId: null, x: 50, y: 160 },
    { id: 40, val: 40, leftId: null, rightId: null, x: 150, y: 160 },
    { id: 60, val: 60, leftId: null, rightId: null, x: 250, y: 160 },
    { id: 80, val: 80, leftId: null, rightId: null, x: 350, y: 160 },
  ];

  const nodeMap = new Map(bstNodes.map(n => [n.id, n]));
  const frames: VisualizerFrame[] = [];

  frames.push({
    stepIndex: 0,
    description: `Binary Search Tree: Searching for target ${target}. Root is Node(50).`,
    dataState: { nodes: bstNodes },
    pointers: { curr: 50 },
    highlighted: [50],
  });

  let curr: TreeNodeData | undefined = nodeMap.get(50);
  while (curr) {
    frames.push({
      stepIndex: frames.length,
      description: `Comparing target ${target} with Node(${curr.val}).`,
      dataState: { nodes: bstNodes },
      pointers: { curr: curr.id },
      highlighted: [curr.id],
      activeIndices: [curr.id],
    });

    if (curr.val === target) {
      frames.push({
        stepIndex: frames.length,
        description: `Target ${target} found at Node(${curr.id})! BST property verified. Time: O(h).`,
        dataState: { nodes: bstNodes },
        pointers: { match: curr.id },
        activeIndices: [curr.id],
        isCompleted: true,
      });
      return frames;
    } else if (target < curr.val) {
      frames.push({
        stepIndex: frames.length,
        description: `${target} < ${curr.val}: Branching left into subtree (leftId = ${curr.leftId}).`,
        dataState: { nodes: bstNodes },
        pointers: { next: curr.leftId ?? -1 },
      });
      curr = curr.leftId ? nodeMap.get(curr.leftId) : undefined;
    } else {
      frames.push({
        stepIndex: frames.length,
        description: `${target} > ${curr.val}: Branching right into subtree (rightId = ${curr.rightId}).`,
        dataState: { nodes: bstNodes },
        pointers: { next: curr.rightId ?? -1 },
      });
      curr = curr.rightId ? nodeMap.get(curr.rightId) : undefined;
    }
  }

  frames.push({
    stepIndex: frames.length,
    description: `Target ${target} not found in BST (reached null leaf pointer).`,
    dataState: { nodes: bstNodes },
    isCompleted: true,
  });

  return frames;
}
