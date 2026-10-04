"use client";



import Link from "next/link";

import {
  CheckCircle2,
  Clock3,
  Headphones,
  MapPin,
  Package,
  PackageCheck,
  RotateCcw,
  Truck,
  TriangleAlert,
  CreditCard,
} from "lucide-react";



import { Button } from "@/components/ui/button";


import type {
  CancellationResultUIData,
  ConfirmationUIData,
  OrderDetailsUIData,
  OrderListUIData,
  OrderStatusUIData,
  PaymentStatusUIData,
  ReturnResultUIData,
  ShipmentEventUIData,
  ShipmentUIData,
  SupportTicketUIData,
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

function formatCurrency(
  amount: string,
  currency: string,
): string {
  const numericAmount = Number(amount);

  if (!Number.isFinite(numericAmount)) {
    return `${amount} ${currency}`;
  }

  try {
    return new Intl.NumberFormat(
      "en-US",
      {
        style: "currency",
        currency,
      },
    ).format(numericAmount);
  } catch {
    return `${amount} ${currency}`;
  }
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

function OrderListCard({
  data,
}: {
  data: OrderListUIData;
}) {
  if (data.orders.length === 0) {
    return (
      <div className="mt-3 rounded-xl border bg-background p-4">
        <div className="flex items-center gap-3">
          <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-muted">
            <Package className="size-5" />
          </div>

          <div>
            <p className="font-medium">
              No orders found
            </p>

            <p className="mt-0.5 text-sm text-muted-foreground">
              There are no orders associated with your account.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mt-3 overflow-hidden rounded-xl border bg-background">
      <div className="flex items-center gap-3 border-b p-4">
        <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-muted">
          <Package className="size-5" />
        </div>

        <div>
          <p className="font-medium">
            Your orders
          </p>

          <p className="mt-0.5 text-sm text-muted-foreground">
            {data.orders.length}{" "}
            {data.orders.length === 1
              ? "order"
              : "orders"}
          </p>
        </div>
      </div>

      <div className="divide-y">
        {data.orders.map((order) => {
          const placedAt =
            formatDate(order.created_at);

          return (
            <div
              key={order.order_number}
              className="p-4"
            >
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="font-medium">
                      {order.order_number}
                    </p>

                    <span className="rounded-full border bg-muted/40 px-2.5 py-1 text-xs font-medium">
                      {formatStatus(
                        order.status,
                      )}
                    </span>
                  </div>

                  {placedAt && (
                    <p className="mt-1 text-sm text-muted-foreground">
                      Placed {placedAt}
                    </p>
                  )}
                </div>

                <div className="flex items-center justify-between gap-4 sm:justify-end">
                  <div className="text-left sm:text-right">
                    <p className="text-xs text-muted-foreground">
                      Total
                    </p>

                    <p className="mt-0.5 font-medium">
                      {new Intl.NumberFormat(
                        "en-US",
                        {
                          style: "currency",
                          currency:
                            order.currency,
                        },
                      ).format(
                        Number(
                          order.total_amount,
                        ),
                      )}
                    </p>
                  </div>

                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    render={
                      <Link
                        href={`/orders/${encodeURIComponent(
                          order.order_number,
                        )}`}
                      />
                    }
                  >
                    View order
                  </Button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function OrderDetailsCard({
  data,
}: {
  data: OrderDetailsUIData;
}) {
  const placedAt = formatDate(
    data.created_at,
  );

  return (
    <div className="mt-3 overflow-hidden rounded-xl border bg-background">
      <div className="flex items-start gap-3 p-4">
        <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-muted">
          <Package className="size-5" />
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
            <div>
              <p className="font-medium">
                Order {data.order_number}
              </p>

              {placedAt && (
                <p className="mt-0.5 text-sm text-muted-foreground">
                  Placed {placedAt}
                </p>
              )}
            </div>

            <span className="w-fit rounded-full border bg-muted/40 px-2.5 py-1 text-xs font-medium">
              {formatStatus(data.status)}
            </span>
          </div>
        </div>
      </div>

      <div className="border-t">
        <div className="p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Items
          </p>

          <div className="mt-3 divide-y rounded-lg border">
            {data.items.map(
              (item, index) => (
                <div
                  key={`${item.sku}-${index}`}
                  className="flex flex-col gap-3 p-3 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="min-w-0">
                    <p className="font-medium">
                      {item.product_name}
                    </p>

                    <p className="mt-0.5 text-xs text-muted-foreground">
                      {item.sku} · Qty{" "}
                      {item.quantity}
                    </p>
                  </div>

                  <div className="shrink-0 sm:text-right">
                    <p className="text-sm font-medium">
                      {formatCurrency(
                        item.line_total,
                        data.currency,
                      )}
                    </p>

                    <p className="mt-0.5 text-xs text-muted-foreground">
                      {formatCurrency(
                        item.unit_price,
                        data.currency,
                      )}{" "}
                      each
                    </p>
                  </div>
                </div>
              ),
            )}
          </div>
        </div>

        <div className="border-t bg-muted/20 p-4">
          <div className="ml-auto max-w-sm space-y-2 text-sm">
            <div className="flex items-center justify-between gap-4">
              <span className="text-muted-foreground">
                Subtotal
              </span>

              <span>
                {formatCurrency(
                  data.subtotal,
                  data.currency,
                )}
              </span>
            </div>

            <div className="flex items-center justify-between gap-4">
              <span className="text-muted-foreground">
                Shipping
              </span>

              <span>
                {formatCurrency(
                  data.shipping_amount,
                  data.currency,
                )}
              </span>
            </div>

            <div className="flex items-center justify-between gap-4">
              <span className="text-muted-foreground">
                Tax
              </span>

              <span>
                {formatCurrency(
                  data.tax_amount,
                  data.currency,
                )}
              </span>
            </div>

            {Number(
              data.discount_amount,
            ) > 0 && (
              <div className="flex items-center justify-between gap-4">
                <span className="text-muted-foreground">
                  Discount
                </span>

                <span>
                  -
                  {formatCurrency(
                    data.discount_amount,
                    data.currency,
                  )}
                </span>
              </div>
            )}

            <div className="flex items-center justify-between gap-4 border-t pt-2 font-medium">
              <span>Total</span>

              <span>
                {formatCurrency(
                  data.total_amount,
                  data.currency,
                )}
              </span>
            </div>
          </div>
        </div>

        {data.payments.length > 0 && (
          <div className="border-t p-4">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Payment
            </p>

            <div className="mt-3 space-y-2">
              {data.payments.map(
                (payment, index) => (
                  <div
                    key={`${payment.payment_method}-${index}`}
                    className="flex flex-col gap-2 rounded-lg bg-muted/40 p-3 sm:flex-row sm:items-center sm:justify-between"
                  >
                    <div>
                      <p className="text-sm font-medium">
                        {formatStatus(
                          payment.payment_method,
                        )}
                      </p>

                      <p className="mt-0.5 text-xs text-muted-foreground">
                        {formatStatus(
                          payment.status,
                        )}
                      </p>
                    </div>

                    <p className="text-sm font-medium">
                      {formatCurrency(
                        payment.amount,
                        payment.currency,
                      )}
                    </p>
                  </div>
                ),
              )}
            </div>
          </div>
        )}
      </div>

      <div className="flex justify-end border-t bg-muted/20 p-3">
        <Button
          type="button"
          variant="outline"
          size="sm"
          render={
            <Link
              href={`/orders/${encodeURIComponent(
                data.order_number,
              )}`}
            />
          }
        >
          View full order
        </Button>
      </div>
    </div>
  );
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

  type="button"

  variant="outline"

  size="sm"

  render={

    <Link

      href={`/orders/${encodeURIComponent(

        data.order_number,

      )}`}

    />

  }

>

  View order

</Button>

      </div>

    </div>

  );

}


function PaymentStatusCard({
  data,
}: {
  data: PaymentStatusUIData;
}) {
  return (
    <div className="mt-3 overflow-hidden rounded-xl border bg-background">
      <div className="flex items-start gap-3 p-4">
        <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-muted">
          <CreditCard className="size-5" />
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
            <div>
              <p className="font-medium">
                Payment details
              </p>

              <p className="mt-0.5 text-sm text-muted-foreground">
                Order {data.order_number}
              </p>
            </div>

            <span className="w-fit rounded-full border bg-muted/40 px-2.5 py-1 text-xs font-medium">
              {formatStatus(data.order_status)}
            </span>
          </div>
        </div>
      </div>

      {data.payments.length > 0 && (
        <div className="border-t p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Payments
          </p>

          <div className="mt-3 space-y-3">
            {data.payments.map(
              (payment, index) => (
                <div
                  key={`${payment.payment_method}-${payment.amount}-${index}`}
                  className="rounded-lg border p-3"
                >
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="text-sm font-medium">
                          {formatStatus(
                            payment.payment_method,
                          )}
                        </p>

                        <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-medium">
                          {formatStatus(
                            payment.status,
                          )}
                        </span>
                      </div>

                      {payment.provider && (
                        <p className="mt-1 text-xs text-muted-foreground">
                          Processed by{" "}
                          {formatStatus(
                            payment.provider,
                          )}
                        </p>
                      )}
                    </div>

                    <p className="text-sm font-medium">
                      {formatCurrency(
                        payment.amount,
                        payment.currency,
                      )}
                    </p>
                  </div>

                  {(payment.failure_message ||
                    payment.failure_code) && (
                    <div className="mt-3 flex gap-2 rounded-lg bg-muted/50 px-3 py-2.5">
                      <TriangleAlert className="mt-0.5 size-4 shrink-0" />

                      <div className="min-w-0 text-sm">
                        <p className="font-medium">
                          Payment issue
                        </p>

                        {payment.failure_message && (
                          <p className="mt-0.5 text-muted-foreground">
                            {
                              payment.failure_message
                            }
                          </p>
                        )}

                        {!payment.failure_message &&
                          payment.failure_code && (
                            <p className="mt-0.5 text-muted-foreground">
                              {formatStatus(
                                payment.failure_code,
                              )}
                            </p>
                          )}
                      </div>
                    </div>
                  )}
                </div>
              ),
            )}
          </div>
        </div>
      )}

      {data.refunds.length > 0 && (
        <div className="border-t p-4">
          <div className="flex items-center gap-2">
            <RotateCcw className="size-4" />

            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Refunds
            </p>
          </div>

          <div className="mt-3 space-y-3">
            {data.refunds.map(
              (refund, index) => (
                <div
                  key={`${refund.amount}-${refund.status}-${index}`}
                  className="rounded-lg bg-muted/40 p-3"
                >
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="text-sm font-medium">
                          Refund
                        </p>

                        <span className="rounded-full border bg-background px-2 py-0.5 text-xs font-medium">
                          {formatStatus(
                            refund.status,
                          )}
                        </span>
                      </div>

                      {refund.reason && (
                        <p className="mt-1 text-xs text-muted-foreground">
                          {refund.reason}
                        </p>
                      )}
                    </div>

                    <p className="text-sm font-medium">
                      {formatCurrency(
                        refund.amount,
                        refund.currency,
                      )}
                    </p>
                  </div>

                  {(refund.failure_message ||
                    refund.failure_code) && (
                    <div className="mt-3 flex gap-2 rounded-lg border px-3 py-2.5">
                      <TriangleAlert className="mt-0.5 size-4 shrink-0" />

                      <div className="min-w-0 text-sm">
                        <p className="font-medium">
                          Refund issue
                        </p>

                        {refund.failure_message && (
                          <p className="mt-0.5 text-muted-foreground">
                            {
                              refund.failure_message
                            }
                          </p>
                        )}

                        {!refund.failure_message &&
                          refund.failure_code && (
                            <p className="mt-0.5 text-muted-foreground">
                              {formatStatus(
                                refund.failure_code,
                              )}
                            </p>
                          )}
                      </div>
                    </div>
                  )}
                </div>
              ),
            )}
          </div>
        </div>
      )}

      {data.payments.length === 0 &&
        data.refunds.length === 0 && (
          <div className="border-t p-4">
            <p className="text-sm text-muted-foreground">
              No payment or refund records are
              available for this order.
            </p>
          </div>
        )}

      <div className="flex justify-end border-t bg-muted/20 p-3">
        <Button
          type="button"
          variant="outline"
          size="sm"
          render={
            <Link
              href={`/orders/${encodeURIComponent(
                data.order_number,
              )}`}
            />
          }
        >
          View order
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





function SupportTicketCard({
  data,
}: {
  data: SupportTicketUIData;
}) {
  return (
    <div className="mt-3 overflow-hidden rounded-xl border bg-background">
      <div className="flex items-start gap-3 p-4">
        <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-muted">
          <Headphones className="size-4" />
        </div>

        <div className="min-w-0 flex-1">
          <p className="font-medium">
            Human support requested
          </p>

          <p className="mt-1 text-sm leading-6 text-muted-foreground">
            Your request has been sent to the VoltNest support team.
          </p>
        </div>
      </div>

      <div className="grid gap-4 border-t bg-muted/20 p-4 sm:grid-cols-2">
        <div>
          <p className="text-xs text-muted-foreground">
            Ticket
          </p>

          <p className="mt-1 break-all text-sm font-medium">
            {data.ticket_number}
          </p>
        </div>

        <div>
          <p className="text-xs text-muted-foreground">
            Status
          </p>

          <p className="mt-1 text-sm font-medium">
            {formatStatus(data.status)}
          </p>
        </div>

        {data.priority && (
          <div>
            <p className="text-xs text-muted-foreground">
              Priority
            </p>

            <p className="mt-1 text-sm font-medium">
              {formatStatus(data.priority)}
            </p>
          </div>
        )}

        {data.order_number && (
          <div>
            <p className="text-xs text-muted-foreground">
              Related order
            </p>

            <p className="mt-1 text-sm font-medium">
              {data.order_number}
            </p>
          </div>
        )}
      </div>

      {data.order_number && (
        <div className="flex justify-end border-t bg-muted/20 p-3">
          <Button
            type="button"
            variant="outline"
            size="sm"
            render={
              <Link
                href={`/orders/${encodeURIComponent(
                  data.order_number,
                )}`}
              />
            }
          >
            View order
          </Button>
        </div>
      )}
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

      case "order_list":
        return (
          <OrderListCard
            data={ui.data}
          />
        );
      case "order_details":
        return (
          <OrderDetailsCard
            data={ui.data}
          />
        );
      case "payment_status":
        return (
          <PaymentStatusCard
            data={ui.data}
          />
        );

    /*

     * Contract exists already. We'll add the ticket

     * presentation when the escalation node emits it.

     */

    case "support_ticket":
      return (
        <SupportTicketCard
          data={ui.data}
        />
      );

    default: {

      const exhaustiveCheck: never = ui;



      return exhaustiveCheck;

    }

  }

}