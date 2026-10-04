import Link from "next/link";
import {
  ArrowRight,
  Bot,
  CheckCircle2,
  CreditCard,
  Headphones,
  PackageSearch,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  Truck,
} from "lucide-react";

import { DemoLoginButton } from "@/components/auth/demo-login-button";
import { Button } from "@/components/ui/button";
import { getCurrentUser } from "@/lib/auth/get-current-user";

const capabilities = [
  {
    title: "Order tracking",
    description:
      "Check order and delivery status using authenticated customer data.",
    icon: Truck,
  },
  {
    title: "Returns & cancellations",
    description:
      "Validate eligibility and safely complete customer actions.",
    icon: RotateCcw,
  },
  {
    title: "Payments & refunds",
    description:
      "Understand payment status, failed payments, charges, and refunds.",
    icon: CreditCard,
  },
  {
    title: "Policy support",
    description:
      "Answer support questions using retrieval-augmented knowledge.",
    icon: PackageSearch,
  },
];

const safeguards = [
  "Customer-scoped operational tools",
  "Explicit confirmation for sensitive actions",
  "Deterministic business rules",
  "Grounded policy retrieval",
];

export default async function HomePage() {
  const user = await getCurrentUser();

  return (
    <main className="min-h-screen bg-background">
      <header className="border-b">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-5 md:px-8">
          <Link
            href="/"
            className="flex items-center gap-2 font-semibold tracking-tight"
          >
            <div className="flex size-9 items-center justify-center rounded-xl bg-primary text-primary-foreground">
              <Headphones className="size-4" />
            </div>

            <span>VoltNest</span>
          </Link>

          <div className="flex items-center gap-2">
            {user ? (
              <Button
                nativeButton={false}
                render={
                  <Link href="/support">
                    Open support
                    <ArrowRight />
                  </Link>
                }
              />
            ) : (
              <Button
                nativeButton={false}
                variant="ghost"
                render={
                  <Link href="/login">
                    Sign in
                  </Link>
                }
              />
            )}
          </div>
        </div>
      </header>

      <section className="border-b">
        <div className="mx-auto grid max-w-7xl gap-14 px-5 py-20 md:px-8 md:py-28 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
          <div>
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border bg-muted/40 px-3 py-1.5 text-sm text-muted-foreground">
              <Sparkles className="size-4" />
              AI-powered customer support
            </div>

            <h1 className="max-w-3xl text-4xl font-semibold tracking-tight sm:text-5xl md:text-6xl">
              Customer support that can actually take action.
            </h1>

            <p className="mt-6 max-w-2xl text-base leading-7 text-muted-foreground md:text-lg">
              VoltNest combines AI reasoning with authenticated
              customer data, support knowledge, and controlled
              business workflows for orders, returns, payments,
              cancellations, and more.
            </p>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              {user ? (
                <Button
                  nativeButton={false}
                  size="lg"
                  render={
                    <Link href="/support">
                      Continue to support
                      <ArrowRight />
                    </Link>
                  }
                />
              ) : (
                <>
                  <DemoLoginButton />

                  <Button
                    nativeButton={false}
                    size="lg"
                    variant="outline"
                    render={
                      <Link href="/login">
                        Customer sign in
                      </Link>
                    }
                  />
                </>
              )}
            </div>

            <p className="mt-4 text-sm text-muted-foreground">
              Explore the support experience using a prepared
              demo customer account.
            </p>
          </div>

          <div className="rounded-3xl border bg-card p-3 shadow-xl shadow-foreground/5">
            <div className="rounded-2xl border bg-background">
              <div className="flex items-center gap-3 border-b px-5 py-4">
                <div className="flex size-9 items-center justify-center rounded-xl bg-primary text-primary-foreground">
                  <Bot className="size-4" />
                </div>

                <div>
                  <p className="text-sm font-medium">
                    VoltNest Support
                  </p>

                  <p className="text-xs text-muted-foreground">
                    Customer assistance
                  </p>
                </div>

                <div className="ml-auto flex items-center gap-1.5 text-xs text-muted-foreground">
                  <span className="size-2 rounded-full bg-emerald-500" />
                  Online
                </div>
              </div>

              <div className="space-y-5 p-5 md:p-6">
                <div className="max-w-[85%] rounded-2xl rounded-tl-sm bg-muted px-4 py-3 text-sm leading-6">
                  Hi! How can I help with your VoltNest order today?
                </div>

                <div className="ml-auto max-w-[85%] rounded-2xl rounded-tr-sm bg-primary px-4 py-3 text-sm leading-6 text-primary-foreground">
                  Can you check the payment status for my order?
                </div>

                <div className="max-w-[90%] rounded-2xl rounded-tl-sm border bg-card px-4 py-4">
                  <div className="mb-3 flex items-center gap-2">
                    <CreditCard className="size-4" />

                    <p className="text-sm font-medium">
                      Payment status
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <p className="text-xs text-muted-foreground">
                        Status
                      </p>

                      <p className="mt-1 font-medium">
                        Captured
                      </p>
                    </div>

                    <div>
                      <p className="text-xs text-muted-foreground">
                        Method
                      </p>

                      <p className="mt-1 font-medium">
                        Card
                      </p>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <ShieldCheck className="size-4" />
                  Customer-scoped and permission-aware
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 py-20 md:px-8">
        <div className="max-w-2xl">
          <p className="text-sm font-medium text-muted-foreground">
            One support experience
          </p>

          <h2 className="mt-2 text-3xl font-semibold tracking-tight md:text-4xl">
            From question to resolution.
          </h2>

          <p className="mt-4 leading-7 text-muted-foreground">
            The assistant can answer support questions and connect
            customers to controlled operational workflows when
            account data or an action is required.
          </p>
        </div>

        <div className="mt-10 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {capabilities.map((capability) => {
            const Icon = capability.icon;

            return (
              <div
                key={capability.title}
                className="rounded-2xl border bg-card p-5"
              >
                <div className="mb-4 flex size-10 items-center justify-center rounded-xl bg-muted">
                  <Icon className="size-5" />
                </div>

                <h3 className="font-medium">
                  {capability.title}
                </h3>

                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  {capability.description}
                </p>
              </div>
            );
          })}
        </div>
      </section>

      <section className="border-y bg-muted/30">
        <div className="mx-auto grid max-w-7xl gap-10 px-5 py-16 md:px-8 lg:grid-cols-2 lg:items-center">
          <div>
            <div className="mb-4 flex size-11 items-center justify-center rounded-xl border bg-background">
              <ShieldCheck className="size-5" />
            </div>

            <h2 className="text-2xl font-semibold tracking-tight md:text-3xl">
              AI reasoning, controlled execution.
            </h2>

            <p className="mt-4 max-w-xl leading-7 text-muted-foreground">
              Operational actions are separated from model
              reasoning. Customer ownership, eligibility and
              confirmation are enforced by application logic
              before state-changing operations execute.
            </p>
          </div>

          <div className="grid gap-3">
            {safeguards.map((safeguard) => (
              <div
                key={safeguard}
                className="flex items-center gap-3 rounded-xl border bg-background px-4 py-3"
              >
                <CheckCircle2 className="size-5 shrink-0" />

                <span className="text-sm">
                  {safeguard}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 py-20 md:px-8">
        <div className="rounded-3xl border bg-card px-6 py-10 text-center md:px-10 md:py-14">
          <h2 className="text-3xl font-semibold tracking-tight">
            Experience VoltNest Support
          </h2>

          <p className="mx-auto mt-3 max-w-xl leading-7 text-muted-foreground">
            Try realistic customer-support workflows using a
            prepared demo account.
          </p>

          <div className="mt-7 flex justify-center">
            {user ? (
              <Button
                nativeButton={false}
                size="lg"
                render={
                  <Link href="/support">
                    Open support
                    <ArrowRight />
                  </Link>
                }
              />
            ) : (
              <DemoLoginButton />
            )}
          </div>
        </div>
      </section>

      <footer className="border-t">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-5 py-8 text-sm text-muted-foreground md:flex-row md:items-center md:justify-between md:px-8">
          <p>VoltNest Customer Support</p>

          <div className="flex items-center gap-2">
            <ShieldCheck className="size-4" />

            <span>
              AI-assisted, application-controlled
            </span>
          </div>
        </div>
      </footer>
    </main>
  );
}