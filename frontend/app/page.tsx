import { redirect } from "next/navigation";

import { getCurrentUser } from "@/lib/auth/get-current-user";

export default async function HomePage() {
  const user = await getCurrentUser();

  redirect(
    user
      ? "/support"
      : "/login",
  );
}