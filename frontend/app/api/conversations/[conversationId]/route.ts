import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { BACKEND_API_URL } from "@/lib/api/server";
import { SESSION_COOKIE_NAME } from "@/lib/auth/session";

interface RouteContext {
  params: Promise<{
    conversationId: string;
  }>;
}

export async function DELETE(
  _request: Request,
  context: RouteContext,
) {
  const { conversationId } = await context.params;

  const cookieStore = await cookies();
  const token = cookieStore.get(SESSION_COOKIE_NAME)?.value;

  if (!token) {
    return NextResponse.json(
      { detail: "Authentication required." },
      { status: 401 },
    );
  }

  try {
    const response = await fetch(
      `${BACKEND_API_URL}/conversations/${encodeURIComponent(
        conversationId,
      )}`,
      {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        cache: "no-store",
      },
    );

    if (response.status === 204) {
      return new Response(null, {
        status: 204,
      });
    }

    const data = await response.json().catch(() => null);

    if (response.status === 401 || response.status === 403) {
      const result = NextResponse.json(
        {
          detail:
            data?.detail ??
            data?.error?.message ??
            "Your session is no longer valid.",
        },
        { status: response.status },
      );

      result.cookies.set(SESSION_COOKIE_NAME, "", {
        httpOnly: true,
        secure: process.env.NODE_ENV === "production",
        sameSite: "lax",
        path: "/",
        maxAge: 0,
      });

      return result;
    }

    return NextResponse.json(
      {
        detail:
          data?.detail ??
          data?.error?.message ??
          "Unable to delete this conversation.",
      },
      { status: response.status },
    );
  } catch {
    return NextResponse.json(
      {
        detail:
          "Conversation deletion is temporarily unavailable.",
      },
      { status: 503 },
    );
  }
}