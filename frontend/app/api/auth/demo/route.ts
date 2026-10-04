import { NextResponse } from "next/server";

import { BACKEND_API_URL } from "@/lib/api/server";
import {
  SESSION_COOKIE_NAME,
  sessionCookieOptions,
} from "@/lib/auth/session";

export async function POST() {
  const email = process.env.DEMO_USER_EMAIL;
  const password = process.env.DEMO_USER_PASSWORD;

  if (!email || !password) {
    return NextResponse.json(
      {
        detail: "The demo account is not configured.",
      },
      {
        status: 503,
      },
    );
  }

  try {
    const response = await fetch(
      `${BACKEND_API_URL}/auth/login`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email,
          password,
        }),
        cache: "no-store",
      },
    );

    if (!response.ok) {
      return NextResponse.json(
        {
          detail:
            "The demo account is temporarily unavailable.",
        },
        {
          status: 503,
        },
      );
    }

    const data = await response.json();

    const token = data.access_token;

    if (
      typeof token !== "string" ||
      token.length === 0
    ) {
      return NextResponse.json(
        {
          detail:
            "The demo authentication service returned an invalid response.",
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
          "The demo authentication service is unavailable.",
      },
      {
        status: 503,
      },
    );
  }
}