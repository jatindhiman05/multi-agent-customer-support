"use client";

import Link from "next/link";
import {
  CheckCircle2,
  Clock3,
  MapPin,
  Package,
  PackageCheck,
  RotateCcw,
  Truck,
  TriangleAlert,
} from "lucide-react";

import { Button } from "@/components/ui/button";

import type {
  CancellationResultUIData,
  ConfirmationUIData,
  OrderStatusUIData,
  ReturnResultUIData,
  ShipmentEventUIData,
  ShipmentUIData,
  SupportUI,
} from "@/types/api";


type SupportUIProps = {
  ui: SupportUI;
  actionable: boolean;
  isSending: boolean;
  onConfirm: () => void;
  onDecline: () => void;
};


function formatDate(
  value: string | null | undefined,
): string | null {
  if (!value) {
    return null;
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return null;
  }

  return new Intl.DateTimeFormat(
    "en-US",
    {
      month: "short",
      day: "numeric",
      year: "numeric",
    },
  ).format(date);
}


function formatDateTime(
  value: string | null | undefined,
): string | null {
  if (!value) {
    return null;
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return null;
  }

  return new Intl.DateTimeFormat(
    "en-US",
    {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
    },
  ).format(date);
}


function formatStatus(
  value: string,
): string {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) =>
      character.toUpperCase(),
    );
}


function getLatestShipmentEvent(
  shipment: ShipmentUIData,
): ShipmentEventUIData | null {
  if (!shipment.events.length) {
    return null;
  }

  return shipment.events.reduce(
    (latest, current) => {
      const latestTime = new Date(
        latest.occurred_at,
      ).getTime();

      const currentTime = new Date(
        current.occurred_at,
      ).getTime();

      if (
        Number.isNaN(currentTime) ||
        currentTime <= latestTime
      ) {
        return latest;
      }

      return current;
    },
  );
}


function getPrimaryShipment(
  shipments: ShipmentUIData[],
): ShipmentUIData | null {
  if (!shipments.length) {
    return null;
  }

  /*
   * The service currently returns the customer's shipment
   * records. For the compact support card we show the most
   * recent shipment when multiple shipments exist.
   */
  return shipments[shipments.length - 1];
}


function OrderStatusCard({
  data,
}: {
  data: OrderStatusUIData;
}) {
  const shipment = getPrimaryShipment(
    data.shipments,
  );

  const latestEvent = shipment
    ? getLatestShipmentEvent(shipment)
    : null;

  const estimatedDelivery = shipment
    ? formatDate(
        shipment.estimated_delivery_at,
      )
    : null;

  const deliveredAt = shipment
    ? formatDate(shipment.delivered_at)
    : null;

  const latestEventTime = latestEvent
    ? formatDateTime(
        latestEvent.occurred_at,
      )
    : null;

  const isDelivered =
    data.status.toLowerCase() ===
      "delivered" ||
    shipment?.status.toLowerCase() ===
      "delivered";

  return (
    <div className="mt-3 overflow-hidden rounded-xl border bg-background">
      <div className="p-4">
        <div className="flex items-start gap-3">
          <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-muted">
            {isDelivered ? (
              <PackageCheck className="size-5" />
            ) : (
              <Truck className="size-5" />
            )}
          </div>

          <div className="min-w-0 flex-1">
            <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
              <div>
                <p className="font-medium">
                  Order {data.order_number}
                </p>

                <p className="mt-0.5 text-sm text-muted-foreground">
                  Shipment status
                </p>
              </div>

              <span className="w-fit rounded-full border bg-muted/40 px-2.5 py-1 text-xs font-medium">
                {formatStatus(data.status)}
              </span>
            </div>

            {shipment ? (
              <>
                <div className="mt-4 grid gap-3 rounded-lg bg-muted/40 p-3 sm:grid-cols-2">
                  <div>
                    <p className="text-xs text-muted-foreground">
                      Carrier
                    </p>

                    <p className="mt-1 text-sm font-medium">
                      {shipment.carrier}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs text-muted-foreground">
                      Tracking number
                    </p>

                    <p className="mt-1 break-all text-sm font-medium">
                      {shipment.tracking_number}
                    </p>
                  </div>

                  {deliveredAt ? (
                    <div className="sm:col-span-2">
                      <p className="text-xs text-muted-foreground">
                        Delivered
                      </p>

                      <div className="mt-1 flex items-center gap-1.5 text-sm font-medium">
                        <CheckCircle2 className="size-3.5" />
                        {deliveredAt}
                      </div>
                    </div>
                  ) : estimatedDelivery ? (
                    <div className="sm:col-span-2">
                      <p className="text-xs text-muted-foreground">
                        Estimated delivery
                      </p>

                      <div className="mt-1 flex items-center gap-1.5 text-sm font-medium">
                        <Clock3 className="size-3.5" />
                        {estimatedDelivery}
                      </div>
                    </div>
                  ) : null}
                </div>

                {latestEvent && (
                  <div className="mt-4">
                    <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                      Latest update
                    </p>

                    <div className="mt-2 flex gap-3">
                      <div className="mt-1 flex size-7 shrink-0 items-center justify-center rounded-full bg-muted">
                        <Package className="size-3.5" />
                      </div>

                      <div className="min-w-0">
                        <p className="text-sm font-medium">
                          {latestEvent.description}
                        </p>

                        {latestEvent.location && (
                          <div className="mt-1 flex items-center gap-1.5 text-xs text-muted-foreground">
                            <MapPin className="size-3.5 shrink-0" />

                            <span>
                              {latestEvent.location}
                            </span>
                          </div>
                        )}

                        {latestEventTime && (
                          <p className="mt-1 text-xs text-muted-foreground">
                            {latestEventTime}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="mt-4 rounded-lg bg-muted/40 px-3 py-2.5 text-sm text-muted-foreground">
                Shipment details are not available yet.
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="flex justify-end border-t bg-muted/20 p-3">
        <Button
          asChild
          type="button"
          variant="outline"
          size="sm"
        >
          <Link
            href={`/orders/${encodeURIComponent(
              data.order_number,
            )}`}
          >
            View order
          </Link>
        </Button>
      </div>
    </div>
  );
}


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
                {data.status.replaceAll(
                  "_",
                  " ",
                )}
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

    case "order_status":
      return (
        <OrderStatusCard
          data={ui.data}
        />
      );

    /*
     * Contract exists already. We'll add the ticket
     * presentation when the escalation node emits it.
     */
    case "support_ticket":
      return null;

    default: {
      const exhaustiveCheck: never = ui;

      return exhaustiveCheck;
    }
  }
}