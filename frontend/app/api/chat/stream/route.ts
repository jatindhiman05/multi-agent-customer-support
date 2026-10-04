import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { BACKEND_API_URL } from "@/lib/api/server";
import { SESSION_COOKIE_NAME } from "@/lib/auth/session";
import type { ChatRequest } from "@/types/api";


export const dynamic = "force-dynamic";


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

  if (!body.request_id) {
    return NextResponse.json(
      {
        detail: "Request ID is required.",
      },
      {
        status: 400,
      },
    );
  }

  try {
    const backendResponse = await fetch(
      `${BACKEND_API_URL}/chat/stream`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
          Accept: "application/x-ndjson",
        },
        body: JSON.stringify({
          request_id: body.request_id,
          message,
          conversation_id:
            body.conversation_id ?? null,
        }),
        cache: "no-store",
      },
    );

    if (!backendResponse.ok) {
      const data = await backendResponse
        .json()
        .catch(() => null);

      if (
        backendResponse.status === 401 ||
        backendResponse.status === 403
      ) {
        const result = NextResponse.json(
          {
            detail:
              data?.detail ??
              "Your session is no longer valid.",
          },
          {
            status: backendResponse.status,
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
          status: backendResponse.status,
        },
      );
    }

    if (!backendResponse.body) {
      return NextResponse.json(
        {
          detail:
            "VoltNest Support returned an empty response.",
        },
        {
          status: 502,
        },
      );
    }

    return new Response(
      backendResponse.body,
      {
        status: 200,
        headers: {
          "Content-Type":
            "application/x-ndjson; charset=utf-8",
          "Cache-Control":
            "no-cache, no-store, no-transform",
          "X-Accel-Buffering": "no",
        },
      },
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