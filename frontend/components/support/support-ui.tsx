"use client";

import {
  CheckCircle2,
  PackageCheck,
  RotateCcw,
  TriangleAlert,
} from "lucide-react";
import { Button } from "@/components/ui/button";

import type {
  CancellationResultUIData,
  ConfirmationUIData,
  ReturnResultUIData,
  SupportUI,
} from "@/types/api";


type SupportUIProps = {
  ui: SupportUI;
  actionable: boolean;
  isSending: boolean;
  onConfirm: () => void;
  onDecline: () => void;
};


function ConfirmationCard({
  data,
  actionable,
  isSending,
  onConfirm,
  onDecline,
}: {
  data: ConfirmationUIData;
  actionable: boolean;
  isSending: boolean;
  onConfirm: () => void;
  onDecline: () => void;
}) {
  const isCancellation =
    data.action === "cancel_order";

  return (
    <div className="mt-3 overflow-hidden rounded-xl border bg-background">
      <div className="flex gap-3 p-4">
        <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-muted">
          {isCancellation ? (
            <TriangleAlert className="size-4" />
          ) : (
            <RotateCcw className="size-4" />
          )}
        </div>

        <div className="min-w-0 flex-1">
          <p className="font-medium">
            {data.title}
          </p>

          <p className="mt-1 text-sm leading-6 text-muted-foreground">
            {data.description}
          </p>

          <div className="mt-3 rounded-lg bg-muted/50 px-3 py-2">
            <div className="flex items-center justify-between gap-4 text-sm">
              <span className="text-muted-foreground">
                Order
              </span>

              <span className="font-medium">
                {data.order_number}
              </span>
            </div>

            {data.product_name && (
              <div className="mt-2 flex items-start justify-between gap-4 text-sm">
                <span className="text-muted-foreground">
                  Item
                </span>

                <span className="text-right font-medium">
                  {data.product_name}
                </span>
              </div>
            )}

            {data.quantity !== undefined && (
              <div className="mt-2 flex items-center justify-between gap-4 text-sm">
                <span className="text-muted-foreground">
                  Quantity
                </span>

                <span className="font-medium">
                  {data.quantity}
                </span>
              </div>
            )}

            {data.reason && (
              <div className="mt-2 flex items-start justify-between gap-4 text-sm">
                <span className="text-muted-foreground">
                  Reason
                </span>

                <span className="max-w-[65%] text-right font-medium">
                  {data.reason}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {actionable ? (
        <div className="flex flex-col-reverse gap-2 border-t bg-muted/20 p-3 sm:flex-row sm:justify-end">
          <Button
            type="button"
            variant="outline"
            onClick={onDecline}
            disabled={isSending}
          >
            {data.cancel_label}
          </Button>

          <Button
            type="button"
            variant={
              isCancellation
                ? "destructive"
                : "default"
            }
            onClick={onConfirm}
            disabled={isSending}
          >
            {data.confirm_label}
          </Button>
        </div>
      ) : (
        <div className="border-t bg-muted/20 px-4 py-2.5 text-xs text-muted-foreground">
          This request is no longer awaiting a response.
        </div>
      )}
    </div>
  );
}


function CancellationResultCard({
  data,
}: {
  data: CancellationResultUIData;
}) {
  return (
    <div className="mt-3 rounded-xl border bg-background p-4">
      <div className="flex gap-3">
        <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-muted">
          <CheckCircle2 className="size-5" />
        </div>

        <div className="min-w-0 flex-1">
          <p className="font-medium">
            Order cancelled
          </p>

          <p className="mt-1 text-sm text-muted-foreground">
            {data.order_number}
          </p>

          <div className="mt-3 space-y-2 text-sm">
            <div className="flex items-center justify-between gap-4">
              <span className="text-muted-foreground">
                Status
              </span>

              <span className="font-medium capitalize">
                {data.status}
              </span>
            </div>

            <div className="flex items-center justify-between gap-4">
              <span className="text-muted-foreground">
                Refund
              </span>

              <span className="text-right font-medium">
                {data.requires_refund
                  ? "Refund initiated"
                  : "No refund required"}
              </span>
            </div>

            {data.refund_id && (
              <div className="flex items-center justify-between gap-4">
                <span className="text-muted-foreground">
                  Refund reference
                </span>

                <span className="break-all text-right font-medium">
                  {data.refund_id}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}


function ReturnResultCard({
  data,
}: {
  data: ReturnResultUIData;
}) {
  return (
    <div className="mt-3 rounded-xl border bg-background p-4">
      <div className="flex gap-3">
        <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-muted">
          <PackageCheck className="size-5" />
        </div>

        <div className="min-w-0 flex-1">
          <p className="font-medium">
            Return created
          </p>

          <p className="mt-1 text-sm text-muted-foreground">
            {data.return_number}
          </p>

          <div className="mt-3 space-y-2 text-sm">
            <div className="flex items-center justify-between gap-4">
              <span className="text-muted-foreground">
                Order
              </span>

              <span className="font-medium">
                {data.order_number}
              </span>
            </div>

            <div className="flex items-start justify-between gap-4">
              <span className="text-muted-foreground">
                Item
              </span>

              <span className="text-right font-medium">
                {data.product_name}
              </span>
            </div>

            <div className="flex items-center justify-between gap-4">
              <span className="text-muted-foreground">
                Quantity
              </span>

              <span className="font-medium">
                {data.quantity}
              </span>
            </div>

            <div className="flex items-center justify-between gap-4">
              <span className="text-muted-foreground">
                Status
              </span>

              <span className="font-medium capitalize">
                {data.status.replaceAll("_", " ")}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}


export function SupportUIRenderer({
  ui,
  actionable,
  isSending,
  onConfirm,
  onDecline,
}: SupportUIProps) {
  switch (ui.type) {
    case "confirmation":
      return (
        <ConfirmationCard
          data={ui.data}
          actionable={actionable}
          isSending={isSending}
          onConfirm={onConfirm}
          onDecline={onDecline}
        />
      );

    case "cancellation_result":
      return (
        <CancellationResultCard
          data={ui.data}
        />
      );

    case "return_result":
      return (
        <ReturnResultCard
          data={ui.data}
        />
      );

    /*
     * These contracts already exist so the API remains
     * forward-compatible. We'll give them dedicated
     * presentation once the corresponding graph nodes
     * emit their payloads.
     */
    case "order_status":
    case "support_ticket":
      return null;

    default: {
      const exhaustiveCheck: never = ui;

      return exhaustiveCheck;
    }
  }
}