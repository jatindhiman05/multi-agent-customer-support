import {
  Headphones,
  MessageCircle,
  RotateCcw,
  ShieldCheck,
  Truck,
  XCircle,
} from "lucide-react";

import type { CurrentUser } from "@/lib/auth/get-current-user";

type QuickAction = {
  label: string;
  description: string;
  prompt: string;
  icon: typeof Truck;
};

const GENERAL_QUICK_ACTIONS: QuickAction[] = [
  {
    label: "Track an order",
    description: "Get the latest delivery status",
    prompt: "I want to track my order.",
    icon: Truck,
  },
  {
    label: "Return an item",
    description: "Check eligibility and start a return",
    prompt: "I want to return an item from my order.",
    icon: RotateCcw,
  },
  {
    label: "Cancel an order",
    description: "Check whether an order can be cancelled",
    prompt: "I want to cancel my order.",
    icon: XCircle,
  },
  {
    label: "Warranty & policies",
    description: "Ask about coverage or store policies",
    prompt: "I have a question about warranty or store policy.",
    icon: ShieldCheck,
  },
];

function orderQuickActions(
  orderNumber: string,
): QuickAction[] {
  return [
    {
      label: "Track this order",
      description: "Get the latest delivery status",
      prompt: `Where is my order ${orderNumber}?`,
      icon: Truck,
    },
    {
      label: "Return an item",
      description: "Check eligibility and start a return",
      prompt: `I want to return an item from order ${orderNumber}.`,
      icon: RotateCcw,
    },
    {
      label: "Cancel this order",
      description: "Check whether this order can be cancelled",
      prompt: `I want to cancel order ${orderNumber}.`,
      icon: XCircle,
    },
    {
      label: "Something else",
      description: "Ask another question about this order",
      prompt: `I need help with order ${orderNumber}.`,
      icon: MessageCircle,
    },
  ];
}

export function SupportEmptyState({
  user,
  orderNumber,
  disabled,
  onSend,
}: {
  user: CurrentUser;
  orderNumber?: string | null;
  disabled: boolean;
  onSend: (message: string) => void;
}) {
  const actions = orderNumber
    ? orderQuickActions(orderNumber)
    : GENERAL_QUICK_ACTIONS;

  return (
    <div className="flex flex-1 flex-col justify-center py-12 md:py-20">
      <div className="mx-auto w-full max-w-2xl">
        <div className="mb-8">
          <div className="mb-4 flex size-11 items-center justify-center rounded-xl border bg-muted/40">
            <Headphones className="size-5" />
          </div>

          {orderNumber ? (
            <>
              <p className="mb-2 text-sm font-medium text-muted-foreground">
                Support for order
              </p>

              <h2 className="text-2xl font-semibold tracking-tight md:text-3xl">
                {orderNumber}
              </h2>

              <p className="mt-2 max-w-xl text-sm leading-6 text-muted-foreground md:text-base">
                What can we help you with for this order?
              </p>
            </>
          ) : (
            <>
              <h2 className="text-2xl font-semibold tracking-tight md:text-3xl">
                How can we help, {user.first_name}?
              </h2>

              <p className="mt-2 max-w-xl text-sm leading-6 text-muted-foreground md:text-base">
                Ask about an order, return, cancellation, warranty,
                payment, delivery issue, or anything else related to
                VoltNest.
              </p>
            </>
          )}
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          {actions.map((action) => {
            const Icon = action.icon;

            return (
              <button
                key={action.label}
                type="button"
                onClick={() => onSend(action.prompt)}
                disabled={disabled}
                className="group rounded-xl border bg-card p-4 text-left transition-colors hover:bg-muted/40 disabled:opacity-50"
              >
                <Icon className="mb-3 size-5 text-muted-foreground transition-colors group-hover:text-foreground" />

                <p className="text-sm font-medium">
                  {action.label}
                </p>

                <p className="mt-1 text-xs leading-5 text-muted-foreground">
                  {action.description}
                </p>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}