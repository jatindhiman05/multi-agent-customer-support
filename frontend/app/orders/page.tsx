import Link from "next/link";
import { redirect } from "next/navigation";
import {
  ArrowRight,
  LifeBuoy,
  Package,
  User
} from "lucide-react";

import { LogoutButton } from "@/components/auth/logout-button";
import { Button } from "@/components/ui/button";
import { BACKEND_API_URL } from "@/lib/api/server";
import { SESSION_COOKIE_NAME } from "@/lib/auth/session";
import { getCurrentUser } from "@/lib/auth/get-current-user";
import type { OrderSummary } from "@/types/api";
import { cookies } from "next/headers";

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

function date(value: string) {
  return new Intl.DateTimeFormat(
    "en-US",
    {
      year: "numeric",
      month: "short",
      day: "numeric",
    },
  ).format(new Date(value));
}

function statusStyle(status: string) {
  switch (status.toLowerCase()) {
    case "delivered":
      return "bg-green-50 text-green-700 ring-green-600/20";

    case "shipped":
      return "bg-blue-50 text-blue-700 ring-blue-600/20";

    case "cancelled":
      return "bg-red-50 text-red-700 ring-red-600/20";

    case "processing":
    case "confirmed":
      return "bg-amber-50 text-amber-700 ring-amber-600/20";

    default:
      return "bg-muted text-muted-foreground ring-border";
  }
}

async function getOrders(
  token: string,
): Promise<OrderSummary[]> {
  const response = await fetch(
    `${BACKEND_API_URL}/orders`,
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

  if (!response.ok) {
    throw new Error(
      "Unable to load orders.",
    );
  }

  return response.json();
}

export default async function OrdersPage() {
  const user = await getCurrentUser();

  if (!user) {
    redirect("/login");
  }

  const cookieStore = await cookies();

  const token = cookieStore.get(
    SESSION_COOKIE_NAME,
  )?.value;

  if (!token) {
    redirect("/login");
  }

  const orders = await getOrders(token);

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

            <div>
              <p className="font-semibold tracking-tight">
                VoltNest
              </p>

              <p className="text-xs text-muted-foreground">
                My Orders
              </p>
            </div>
          </Link>

          <div className="flex items-center gap-2">
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

            <LogoutButton />
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-8 md:px-6 md:py-12">
        <div className="mb-8">
          <h1 className="text-3xl font-semibold tracking-tight">
            Your orders
          </h1>

          <p className="mt-2 text-muted-foreground">
            View purchases, delivery
            status and order details.
          </p>
        </div>

        {orders.length === 0 ? (
          <div className="rounded-2xl border bg-background p-10 text-center">
            <Package className="mx-auto size-9 text-muted-foreground" />

            <h2 className="mt-4 font-semibold">
              No orders yet
            </h2>

            <p className="mt-2 text-sm text-muted-foreground">
              Your VoltNest orders will
              appear here.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {orders.map((order) => (
              <article
                key={order.order_number}
                className="rounded-2xl border bg-background p-5 shadow-sm transition-shadow hover:shadow-md md:p-6"
              >
                <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <div className="flex flex-wrap items-center gap-3">
                      <h2 className="text-lg font-semibold">
                        {order.order_number}
                      </h2>

                      <span
                        className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium capitalize ring-1 ring-inset ${statusStyle(
                          order.status,
                        )}`}
                      >
                        {order.status}
                      </span>
                    </div>

                    <p className="mt-2 text-sm text-muted-foreground">
                      Placed {date(
                        order.created_at,
                      )}
                    </p>
                  </div>

                  <div className="flex items-center justify-between gap-6 sm:justify-end">
                    <div className="text-left sm:text-right">
                      <p className="text-xs text-muted-foreground">
                        Total
                      </p>

                      <p className="mt-1 font-semibold">
                        {money(
                          order.total_amount,
                          order.currency,
                        )}
                      </p>
                    </div>

                    <Button
                      variant="outline"
                      render={
                        <Link
                          href={`/orders/${order.order_number}`}
                        />
                      }
                    >
                      View details
                      <ArrowRight className="size-4" />
                    </Button>
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}