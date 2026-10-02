import Link from "next/link";
import { cookies } from "next/headers";
import {
  ArrowLeft,
  CreditCard,
  LifeBuoy,
  MapPin,
  Package,
  Truck,
  User,
} from "lucide-react";
import {
  notFound,
  redirect,
} from "next/navigation";

import { Button } from "@/components/ui/button";
import { BACKEND_API_URL } from "@/lib/api/server";
import { SESSION_COOKIE_NAME } from "@/lib/auth/session";
import { getCurrentUser } from "@/lib/auth/get-current-user";
import type { OrderDetail } from "@/types/api";

type PageProps = {
  params: Promise<{
    orderNumber: string;
  }>;
};

function money(
  amount: string,
  currency: string,
) {
  return new Intl.NumberFormat(
    "en-US",
    {
      style: "currency",
      currency,
    },
  ).format(Number(amount));
}

function dateTime(
  value: string | null,
) {
  if (!value) {
    return "Not available";
  }

  return new Intl.DateTimeFormat(
    "en-US",
    {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    },
  ).format(new Date(value));
}

async function getOrder(
  orderNumber: string,
  token: string,
): Promise<OrderDetail> {
  const response = await fetch(
    `${BACKEND_API_URL}/orders/${encodeURIComponent(
      orderNumber,
    )}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      cache: "no-store",
    },
  );

  if (response.status === 401) {
    redirect("/login");
  }

  if (response.status === 404) {
    notFound();
  }

  if (!response.ok) {
    throw new Error(
      "Unable to load order.",
    );
  }

  return response.json();
}

export default async function OrderPage({
  params,
}: PageProps) {
  const user = await getCurrentUser();

  if (!user) {
    redirect("/login");
  }

  const { orderNumber } =
    await params;

  const cookieStore = await cookies();

  const token = cookieStore.get(
    SESSION_COOKIE_NAME,
  )?.value;

  if (!token) {
    redirect("/login");
  }

  const order = await getOrder(
    orderNumber,
    token,
  );

  return (
    <div className="min-h-screen bg-muted/20">
      <header className="border-b bg-background">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 md:px-6">
          <Link
            href="/orders"
            className="flex items-center gap-3"
          >
            <div className="flex size-9 items-center justify-center rounded-xl bg-primary text-primary-foreground">
              <Package className="size-5" />
            </div>

            <span className="font-semibold">
              VoltNest
            </span>
          </Link>
          <Button
            variant="ghost"
            render={<Link href="/account" />}
          >
            <User className="size-4" />
            Account
          </Button>
          <Button
            variant="ghost"
            render={
              <Link href="/support" />
            }
          >
            <LifeBuoy className="size-4" />
            Support
          </Button>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-8 md:px-6 md:py-12">
        <Button
          variant="ghost"
          className="-ml-3 mb-6"
          render={
            <Link href="/orders" />
          }
        >
          <ArrowLeft className="size-4" />
          Back to orders
        </Button>

        <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm text-muted-foreground">
              Order
            </p>

            <h1 className="mt-1 text-3xl font-semibold tracking-tight">
              {order.order_number}
            </h1>

            <p className="mt-2 capitalize text-muted-foreground">
              {order.status}
            </p>
          </div>

          <Button
            render={
              <Link
                href={`/support?order=${encodeURIComponent(
                  order.order_number,
                )}`}
              />
            }
          >
            <LifeBuoy className="size-4" />
            Get support for this order
          </Button>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1.6fr_1fr]">
          <div className="space-y-6">
            <section className="rounded-2xl border bg-background p-6">
              <div className="mb-5 flex items-center gap-2">
                <Package className="size-5" />

                <h2 className="font-semibold">
                  Items
                </h2>
              </div>

              <div className="divide-y">
                {order.items.map(
                  (item) => (
                    <div
                      key={item.sku}
                      className="flex items-start justify-between gap-5 py-4 first:pt-0 last:pb-0"
                    >
                      <div>
                        <p className="font-medium">
                          {
                            item.product_name
                          }
                        </p>

                        <p className="mt-1 text-sm text-muted-foreground">
                          SKU {item.sku}
                        </p>

                        <p className="mt-1 text-sm text-muted-foreground">
                          Qty {item.quantity}
                        </p>
                      </div>

                      <p className="font-medium">
                        {money(
                          item.line_total,
                          order.currency,
                        )}
                      </p>
                    </div>
                  ),
                )}
              </div>
            </section>

            <section className="rounded-2xl border bg-background p-6">
              <div className="mb-5 flex items-center gap-2">
                <Truck className="size-5" />

                <h2 className="font-semibold">
                  Shipping
                </h2>
              </div>

              {order.shipments.length ===
              0 ? (
                <p className="text-sm text-muted-foreground">
                  Shipment information is
                  not available yet.
                </p>
              ) : (
                <div className="space-y-5">
                  {order.shipments.map(
                    (
                      shipment,
                      index,
                    ) => (
                      <div
                        key={`${shipment.tracking_number ?? "shipment"}-${index}`}
                        className="rounded-xl border p-4"
                      >
                        <div className="flex items-center justify-between gap-4">
                          <p className="font-medium capitalize">
                            {
                              shipment.status
                            }
                          </p>

                          {shipment.carrier && (
                            <span className="text-sm text-muted-foreground">
                              {
                                shipment.carrier
                              }
                            </span>
                          )}
                        </div>

                        {shipment.tracking_number && (
                          <p className="mt-3 text-sm">
                            Tracking:{" "}
                            <span className="font-medium">
                              {
                                shipment.tracking_number
                              }
                            </span>
                          </p>
                        )}

                        <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
                          <div>
                            <dt className="text-muted-foreground">
                              Shipped
                            </dt>

                            <dd className="mt-1">
                              {dateTime(
                                shipment.shipped_at,
                              )}
                            </dd>
                          </div>

                          <div>
                            <dt className="text-muted-foreground">
                              Estimated delivery
                            </dt>

                            <dd className="mt-1">
                              {dateTime(
                                shipment.estimated_delivery_at,
                              )}
                            </dd>
                          </div>
                        </dl>
                      </div>
                    ),
                  )}
                </div>
              )}
            </section>

            <section className="rounded-2xl border bg-background p-6">
              <div className="mb-5 flex items-center gap-2">
                <CreditCard className="size-5" />

                <h2 className="font-semibold">
                  Payment
                </h2>
              </div>

              {order.payments.length ===
              0 ? (
                <p className="text-sm text-muted-foreground">
                  No payment information
                  available.
                </p>
              ) : (
                <div className="space-y-4">
                  {order.payments.map(
                    (
                      payment,
                      index,
                    ) => (
                      <div
                        key={`${payment.provider}-${index}`}
                        className="flex items-center justify-between gap-4"
                      >
                        <div>
                          <p className="font-medium capitalize">
                            {
                              payment.payment_method
                            }
                          </p>

                          <p className="mt-1 text-sm capitalize text-muted-foreground">
                            {
                              payment.status
                            }
                          </p>
                        </div>

                        <p className="font-medium">
                          {money(
                            payment.amount,
                            payment.currency,
                          )}
                        </p>
                      </div>
                    ),
                  )}
                </div>
              )}
            </section>
          </div>

          <div className="space-y-6">
            <section className="rounded-2xl border bg-background p-6">
              <h2 className="font-semibold">
                Order summary
              </h2>

              <dl className="mt-5 space-y-3 text-sm">
                <div className="flex justify-between gap-4">
                  <dt className="text-muted-foreground">
                    Subtotal
                  </dt>
                  <dd>
                    {money(
                      order.subtotal,
                      order.currency,
                    )}
                  </dd>
                </div>

                <div className="flex justify-between gap-4">
                  <dt className="text-muted-foreground">
                    Shipping
                  </dt>
                  <dd>
                    {money(
                      order.shipping_amount,
                      order.currency,
                    )}
                  </dd>
                </div>

                <div className="flex justify-between gap-4">
                  <dt className="text-muted-foreground">
                    Tax
                  </dt>
                  <dd>
                    {money(
                      order.tax_amount,
                      order.currency,
                    )}
                  </dd>
                </div>

                {Number(
                  order.discount_amount,
                ) > 0 && (
                  <div className="flex justify-between gap-4">
                    <dt className="text-muted-foreground">
                      Discount
                    </dt>
                    <dd>
                      -
                      {money(
                        order.discount_amount,
                        order.currency,
                      )}
                    </dd>
                  </div>
                )}

                <div className="flex justify-between gap-4 border-t pt-4 text-base font-semibold">
                  <dt>Total</dt>
                  <dd>
                    {money(
                      order.total_amount,
                      order.currency,
                    )}
                  </dd>
                </div>
              </dl>
            </section>

            <section className="rounded-2xl border bg-background p-6">
              <div className="mb-4 flex items-center gap-2">
                <MapPin className="size-5" />

                <h2 className="font-semibold">
                  Shipping address
                </h2>
              </div>

              <address className="text-sm not-italic leading-6 text-muted-foreground">
                <span className="font-medium text-foreground">
                  {
                    order.shipping_recipient_name
                  }
                </span>
                <br />

                {order.shipping_line1}
                <br />

                {order.shipping_line2 && (
                  <>
                    {
                      order.shipping_line2
                    }
                    <br />
                  </>
                )}

                {order.shipping_city},{" "}
                {order.shipping_state}{" "}
                {
                  order.shipping_postal_code
                }
                <br />

                {
                  order.shipping_country_code
                }
              </address>
            </section>

            <section className="rounded-2xl border bg-background p-6">
              <h2 className="font-semibold">
                Need help?
              </h2>

              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                Ask VoltNest Support about
                shipping, returns,
                cancellation or anything
                else related to this order.
              </p>

              <Button
                className="mt-5 w-full"
                render={
                  <Link
                    href={`/support?order=${encodeURIComponent(
                      order.order_number,
                    )}`}
                  />
                }
              >
                <LifeBuoy className="size-4" />
                Contact support
              </Button>
            </section>
          </div>
        </div>
      </main>
    </div>
  );
}