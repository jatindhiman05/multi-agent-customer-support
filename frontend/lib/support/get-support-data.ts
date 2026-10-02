import "server-only";

import { cookies } from "next/headers";
import { BACKEND_API_URL } from "@/lib/api/server";
import type {
  ConversationHistory,
  ConversationSummary,
} from "@/types/api";

const SESSION_COOKIE_NAME = "voltnest_session";

type SupportInitialData = {
  conversations: ConversationSummary[];
  history: ConversationHistory | null;
};

async function authenticatedBackendFetch(
  path: string,
): Promise<Response | null> {
  const cookieStore = await cookies();
  const token = cookieStore.get(
    SESSION_COOKIE_NAME,
  )?.value;

  if (!token) {
    return null;
  }

  try {
    return await fetch(
      `${BACKEND_API_URL}${path}`,
      {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: "application/json",
        },
        cache: "no-store",
      },
    );
  } catch {
    return null;
  }
}

export async function getSupportInitialData(
  conversationId: string | null,
): Promise<SupportInitialData> {
  const conversationsResponse =
    await authenticatedBackendFetch(
      "/conversations",
    );

  let conversations: ConversationSummary[] = [];

  if (conversationsResponse?.ok) {
    conversations =
      (await conversationsResponse.json()) as ConversationSummary[];
  }

  if (!conversationId) {
    return {
      conversations,
      history: null,
    };
  }

  const historyResponse =
    await authenticatedBackendFetch(
      `/conversations/${encodeURIComponent(
        conversationId,
      )}/messages`,
    );

  if (!historyResponse?.ok) {
    return {
      conversations,
      history: null,
    };
  }

  const history =
    (await historyResponse.json()) as ConversationHistory;

  return {
    conversations,
    history,
  };
}