import Link from "next/link";
import { redirect } from "next/navigation";
import {
  LifeBuoy,
  Mail,
  Package,
  User,
} from "lucide-react";

import { LogoutButton } from "@/components/auth/logout-button";
import { Button } from "@/components/ui/button";
import { getCurrentUser } from "@/lib/auth/get-current-user";

export default async function AccountPage() {
  const user = await getCurrentUser();

  if (!user) {
    redirect("/login");
  }

  const fullName =
    `${user.first_name} ${user.last_name}`.trim();

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
                My Account
              </p>
            </div>
          </Link>

          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              render={<Link href="/orders" />}
            >
              <Package className="size-4" />
              Orders
            </Button>

            <Button
              variant="ghost"
              render={<Link href="/support" />}
            >
              <LifeBuoy className="size-4" />
              Support
            </Button>

            <LogoutButton />
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-4 py-8 md:px-6 md:py-12">
        <div className="mb-8">
          <p className="text-sm font-medium text-muted-foreground">
            Account
          </p>

          <h1 className="mt-1 text-3xl font-semibold tracking-tight">
            {fullName}
          </h1>

          <p className="mt-2 text-muted-foreground">
            View your VoltNest account and access your
            customer services.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-[1.4fr_1fr]">
          <section className="rounded-2xl border bg-background p-6 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="flex size-10 items-center justify-center rounded-xl bg-muted">
                <User className="size-5" />
              </div>

              <div>
                <h2 className="font-semibold">
                  Personal information
                </h2>

                <p className="text-sm text-muted-foreground">
                  Your customer account details
                </p>
              </div>
            </div>

            <dl className="mt-6 divide-y">
              <div className="py-4 first:pt-0">
                <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Name
                </dt>

                <dd className="mt-1 font-medium">
                  {fullName}
                </dd>
              </div>

              <div className="py-4">
                <dt className="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  <Mail className="size-3.5" />
                  Email
                </dt>

                <dd className="mt-1 break-all font-medium">
                  {user.email}
                </dd>
              </div>

              <div className="pt-4">
                <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Account type
                </dt>

                <dd className="mt-1 capitalize">
                  {user.role}
                </dd>
              </div>
            </dl>
          </section>

          <div className="space-y-4">
            <section className="rounded-2xl border bg-background p-5 shadow-sm">
              <Package className="size-5" />

              <h2 className="mt-4 font-semibold">
                Your orders
              </h2>

              <p className="mt-1 text-sm leading-6 text-muted-foreground">
                View purchases, delivery status and order
                details.
              </p>

              <Button
                variant="outline"
                className="mt-4 w-full"
                render={<Link href="/orders" />}
              >
                View orders
              </Button>
            </section>

            <section className="rounded-2xl border bg-background p-5 shadow-sm">
              <LifeBuoy className="size-5" />

              <h2 className="mt-4 font-semibold">
                Customer support
              </h2>

              <p className="mt-1 text-sm leading-6 text-muted-foreground">
                Get help with orders, returns, delivery,
                payments and policies.
              </p>

              <Button
                variant="outline"
                className="mt-4 w-full"
                render={<Link href="/support" />}
              >
                Open support
              </Button>
            </section>
          </div>
        </div>

        <section className="mt-6 rounded-2xl border bg-background p-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="font-semibold">
                Session
              </h2>

              <p className="mt-1 text-sm text-muted-foreground">
                Sign out of your VoltNest customer account.
              </p>
            </div>

            <LogoutButton />
          </div>
        </section>
      </main>
    </div>
  );
}