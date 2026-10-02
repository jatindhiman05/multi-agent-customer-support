import type { SupportRoute, SupportUI } from "@/types/api";

export type SupportMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  route?: SupportRoute;
  ui?: SupportUI | null;
};

export type SupportError = {
  message: string;
  kind: "network" | "rate_limit" | "server" | "request";
};
