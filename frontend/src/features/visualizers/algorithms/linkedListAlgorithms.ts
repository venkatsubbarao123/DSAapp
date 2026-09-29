import { VisualizerFrame } from "../types.ts";

export interface ListNodeState {
  id: number;
  val: number;
  nextId: number | null;
}

export function generateLinkedListFrames(initialValues: number[]): VisualizerFrame[] {
  const vals = initialValues.slice(0, 7);
  const nodes: ListNodeState[] = vals.map((val, idx) => ({
    id: idx,
    val,
    nextId: idx < vals.length - 1 ? idx + 1 : null,
  }));

  const frames: VisualizerFrame[] = [];

  frames.push({
    stepIndex: 0,
    description: `Singly Linked List with ${nodes.length} nodes. Head points to Node(val=${nodes[0]?.val}).`,
    dataState: JSON.parse(JSON.stringify(nodes)),
    pointers: { head: 0 },
  });

  // Traversal demo
  for (let i = 0; i < nodes.length; i++) {
    frames.push({
      stepIndex: frames.length,
      description: `Traversing: Current pointer at Node(val=${nodes[i].val}). ${nodes[i].nextId !== null ? "Advancing current = current.next." : "Reached tail (next is null)." }`,
      dataState: JSON.parse(JSON.stringify(nodes)),
      pointers: { curr: i },
      highlighted: [i],
      activeIndices: [i],
    });
  }

  // Insert at head
  const newNodeVal = 77;
  const newHeadNode: ListNodeState = {
    id: 99,
    val: newNodeVal,
    nextId: 0,
  };
  const updatedNodes = [newHeadNode, ...nodes];

  frames.push({
    stepIndex: frames.length,
    description: `Insert at Head: Created new Node(val=${newNodeVal}). Set new_node.next = head, then head = new_node. O(1) time.`,
    dataState: updatedNodes,
    pointers: { newHead: 99 },
    activeIndices: [99],
    isCompleted: true,
  });

  return frames;
}
