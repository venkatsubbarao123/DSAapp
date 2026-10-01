/**
 * Authentication and authorization types matching Phase 2 backend contracts.
 */

export type UserRole = "STUDENT" | "CONTENT_EDITOR" | "MODERATOR" | "ADMIN";

export interface UserProfile {
  id: string;
  user_id: string;
  display_name?: string;
  avatar_url?: string;
  bio?: string;
  github_username?: string;
  leetcode_username?: string;
  preferred_language: string;
  timezone: string;
  created_at: string;
  updated_at: string;
}

export interface User {
  id: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
  plan: "FREE" | "PREMIUM";
  premium_active: boolean;
  profile?: UserProfile;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  display_name?: string;
}

export interface AuthResponseData {
  access_token: string;
  token_type: string;
  expires_in_seconds?: number;
  refresh_token?: string;
  user?: User;
}

export interface OrderCreateResponse {
  order_id: string;
  plan_id: string;
  amount: number;
  currency: string;
  status: string;
  checkout_url?: string;
  created_at: string;
}

export interface OrderStatusResponse {
  order_id: string;
  status: string;
  amount: number;
  currency: string;
  plan_id: string;
  created_at: string;
}

export interface PaymentHistoryItem {
  id: string;
  order_id: string;
  amount: number;
  currency: string;
  status: string;
  created_at: string;
}
