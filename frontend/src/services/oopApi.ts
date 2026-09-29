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
    if (!res.data) throw new Error("OOP overview unavailable");
    return res.data;
  },

  async getPillars(): Promise<OOPPillar[]> {
    const res = await fetchApi<OOPPillar[]>("/api/v1/oop/pillars");
    return res.data || [];
  },

  async getSolidPrinciples(): Promise<SOLIDPrinciple[]> {
    const res = await fetchApi<SOLIDPrinciple[]>("/api/v1/oop/solid");
    return res.data || [];
  },

  async getDesignPatterns(): Promise<OOPDesignPattern[]> {
    const res = await fetchApi<OOPDesignPattern[]>("/api/v1/oop/patterns");
    return res.data || [];
  },
};
