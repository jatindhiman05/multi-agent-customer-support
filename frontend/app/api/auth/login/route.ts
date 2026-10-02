import { NextResponse } from "next/server";
import { z } from "zod";

import { BACKEND_API_URL } from "@/lib/api/server";
import {
  SESSION_COOKIE_NAME,
  sessionCookieOptions,
} from "@/lib/auth/session";

const loginSchema = z.object({
  email: z.email(),
  password: z.string().min(1),
});

export async function POST(request: Request) {
  try {
    const body = await request.json();

    const parsed = loginSchema.safeParse(body);

    if (!parsed.success) {
      return NextResponse.json(
        {
          detail:
            "Enter a valid email and password.",
        },
        {
          status: 400,
        },
      );
    }

    const response = await fetch(
      `${BACKEND_API_URL}/auth/login`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(parsed.data),
        cache: "no-store",
      },
    );

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        {
          detail:
            data.detail ??
            "Unable to sign in.",
        },
        {
          status: response.status,
        },
      );
    }

    const token = data.access_token;

    if (
      typeof token !== "string" ||
      token.length === 0
    ) {
      return NextResponse.json(
        {
          detail:
            "Invalid authentication response.",
        },
        {
          status: 502,
        },
      );
    }

    const result = NextResponse.json({
      authenticated: true,
    });

    result.cookies.set(
      SESSION_COOKIE_NAME,
      token,
      sessionCookieOptions,
    );

    return result;
  } catch {
    return NextResponse.json(
      {
        detail:
          "Authentication service is unavailable.",
      },
      {
        status: 503,
      },
    );
  }
}