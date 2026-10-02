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

export interface OrderSummary {
  order_number: string;
  status: string;
  total_amount: string;
  currency: string;
  created_at: string;
}

export interface OrderItem {
  sku: string;
  product_name: string;
  quantity: number;
  unit_price: string;
  line_total: string;
}

export interface OrderShipment {
  carrier: string | null;
  tracking_number: string | null;
  status: string;
  shipped_at: string | null;
  estimated_delivery_at: string | null;
  delivered_at: string | null;
}

export interface OrderPayment {
  provider: string;
  payment_method: string;
  status: string;
  amount: string;
  currency: string;
}

export interface OrderDetail {
  order_number: string;
  status: string;

  subtotal: string;
  shipping_amount: string;
  tax_amount: string;
  discount_amount: string;
  total_amount: string;
  currency: string;

  shipping_recipient_name: string;
  shipping_line1: string;
  shipping_line2: string | null;
  shipping_city: string;
  shipping_state: string;
  shipping_postal_code: string;
  shipping_country_code: string;

  created_at: string;
  updated_at: string;

  items: OrderItem[];
  payments: OrderPayment[];
  shipments: OrderShipment[];
}