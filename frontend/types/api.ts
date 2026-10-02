export type SupportRoute =
  | "order"
  | "knowledge"
  | "returns"
  | "cancellation"
  | "escalation"
  | "confirmation";

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
}

export interface ChatRequest {
  message: string;
  conversation_id?: string | null;
}

export interface ChatResponse {
  response: string;
  route: SupportRoute;
  conversation_id: string;
}