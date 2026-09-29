/**
 * TypeScript types for Phase 8 Object-Oriented Programming (OOP) & System Design Patterns.
 */

export interface OOPPillar {
  id: string;
  name: string;
  summary: string;
  explanation: string;
  code_examples: Record<string, string>; // language -> code
  common_pitfalls: string[];
}

export interface SOLIDPrinciple {
  letter: string;
  name: string;
  summary: string;
  bad_example: Record<string, string>;
  good_example: Record<string, string>;
  benefits: string[];
}

export interface OOPDesignPattern {
  name: string;
  category: 'CREATIONAL' | 'STRUCTURAL' | 'BEHAVIORAL';
  intent: string;
  use_cases: string[];
  structure_diagram_mermaid: string;
  implementation: Record<string, string>;
  tradeoffs: string[];
}

export interface OOPOverview {
  pillars: OOPPillar[];
  solid_principles: SOLIDPrinciple[];
  design_patterns: OOPDesignPattern[];
}
