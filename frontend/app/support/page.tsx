import { redirect } from "next/navigation";

import { SupportApp } from "@/components/support/support-app";
import { getCurrentUser } from "@/lib/auth/get-current-user";
import { getSupportInitialData } from "@/lib/support/get-support-data";

export default async function SupportPage({
  searchParams,
}: {
  searchParams: Promise<{
    conversation?: string;
    order?: string;
  }>;
}) {
  const user = await getCurrentUser();

  if (!user) {
    redirect("/login");
  }

  const params = await searchParams;

  const conversationId =
    params.conversation?.trim() || null;

  const orderNumber =
    params.order?.trim() || null;

  const {
    conversations,
    history,
  } = await getSupportInitialData(
    conversationId,
  );

  /*
   * A conversation was explicitly requested but could
   * not be loaded. This covers stale/deleted IDs and
   * conversations that do not belong to this customer.
   *
   * FastAPI remains the authorization boundary.
   */
  if (conversationId && !history) {
    redirect("/support");
  }

  return (
    <SupportApp
      user={user}
      initialConversations={conversations}
      initialHistory={history}
      initialOrderNumber={
        history ? null : orderNumber
      }
    />
  );
}