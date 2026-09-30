/**
 * Frontend API client for Phase 8 OOP Modules.
 */

import { fetchApi } from "./apiClient.ts";
import {
  OOPOverview,
  OOPPillar,
  SOLIDPrinciple,
  OOPDesignPattern,
} from "../types/oop.ts";

export const oopApi = {
  async getOverview(): Promise<OOPOverview> {
    const res = await fetchApi<OOPOverview>("/api/v1/oop/overview");
    const raw = res as unknown as { data?: OOPOverview } & OOPOverview;
    if (raw.pillars && raw.solid_principles && raw.design_patterns) {
      return raw;
    }
    if (raw.data) {
      return raw.data;
    }
    throw new Error("OOP overview unavailable");
  },

  async getPillars(): Promise<OOPPillar[]> {
    const res = await fetchApi<OOPPillar[]>("/api/v1/oop/pillars");
    const raw = res as unknown as { data?: OOPPillar[] } | OOPPillar[];
    if (Array.isArray(raw)) return raw;
    return (raw as { data?: OOPPillar[] })?.data || [];
  },

  async getSolidPrinciples(): Promise<SOLIDPrinciple[]> {
    const res = await fetchApi<SOLIDPrinciple[]>("/api/v1/oop/solid");
    const raw = res as unknown as { data?: SOLIDPrinciple[] } | SOLIDPrinciple[];
    if (Array.isArray(raw)) return raw;
    return (raw as { data?: SOLIDPrinciple[] })?.data || [];
  },

  async getDesignPatterns(): Promise<OOPDesignPattern[]> {
    const res = await fetchApi<OOPDesignPattern[]>("/api/v1/oop/patterns");
    const raw = res as unknown as { data?: OOPDesignPattern[] } | OOPDesignPattern[];
    if (Array.isArray(raw)) return raw;
    return (raw as { data?: OOPDesignPattern[] })?.data || [];
  },
};
