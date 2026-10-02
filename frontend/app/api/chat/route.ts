import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { BACKEND_API_URL } from "@/lib/api/server";
import { SESSION_COOKIE_NAME } from "@/lib/auth/session";
import type {
  ChatRequest,
  ChatResponse,
} from "@/types/api";

export async function POST(request: Request) {
  const cookieStore = await cookies();

  const token = cookieStore.get(
    SESSION_COOKIE_NAME,
  )?.value;

  if (!token) {
    return NextResponse.json(
      {
        detail: "Authentication required.",
      },
      {
        status: 401,
      },
    );
  }

  let body: ChatRequest;

  try {
    body = (await request.json()) as ChatRequest;
  } catch {
    return NextResponse.json(
      {
        detail: "Invalid request body.",
      },
      {
        status: 400,
      },
    );
  }

  const message = body.message?.trim();

  if (
    !message ||
    message.length > 4000
  ) {
    return NextResponse.json(
      {
        detail:
          "Message must contain between 1 and 4000 characters.",
      },
      {
        status: 400,
      },
    );
  }

  try {
    const response = await fetch(
      `${BACKEND_API_URL}/chat`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message,
          conversation_id:
            body.conversation_id ?? null,
        }),
        cache: "no-store",
      },
    );

    const data = await response
      .json()
      .catch(() => null);

    if (!response.ok) {
      if (
        response.status === 401 ||
        response.status === 403
      ) {
        const result = NextResponse.json(
          {
            detail:
              data?.detail ??
              "Your session is no longer valid.",
          },
          {
            status: response.status,
          },
        );

        result.cookies.set(
          SESSION_COOKIE_NAME,
          "",
          {
            httpOnly: true,
            secure:
              process.env.NODE_ENV ===
              "production",
            sameSite: "lax",
            path: "/",
            maxAge: 0,
          },
        );

        return result;
      }

      return NextResponse.json(
        {
          detail:
            data?.detail ??
            data?.error?.message ??
            "VoltNest Support could not process your request.",
        },
        {
          status: response.status,
        },
      );
    }

    return NextResponse.json(
      data as ChatResponse,
    );
  } catch {
    return NextResponse.json(
      {
        detail:
          "VoltNest Support is temporarily unavailable.",
      },
      {
        status: 503,
      },
    );
  }
}