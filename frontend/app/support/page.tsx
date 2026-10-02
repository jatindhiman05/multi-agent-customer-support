import { redirect } from "next/navigation";

import { LogoutButton } from "@/components/auth/logout-button";
import { getCurrentUser } from "@/lib/auth/get-current-user";

export default async function SupportPage() {
  const user = await getCurrentUser();

  if (!user) {
    redirect("/login");
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-muted/30 px-4">
      <div className="w-full max-w-lg rounded-xl border bg-background p-8 text-center shadow-sm">
        <h1 className="text-3xl font-semibold tracking-tight">
          VoltNest Support
        </h1>

        <p className="mt-3 text-muted-foreground">
          Welcome, {user.first_name}.
        </p>

        <p className="mt-1 text-sm text-muted-foreground">
          {user.email}
        </p>

        <div className="mt-6">
          <LogoutButton />
        </div>
      </div>
    </main>
  );
}