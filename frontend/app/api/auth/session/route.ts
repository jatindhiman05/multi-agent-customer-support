import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { BACKEND_API_URL } from "@/lib/api/server";
import {
  SESSION_COOKIE_NAME,
  sessionCookieOptions,
} from "@/lib/auth/session";

export async function GET() {
  const cookieStore = await cookies();

  const token = cookieStore.get(
    SESSION_COOKIE_NAME,
  )?.value;

  if (!token) {
    return NextResponse.json(
      {
        authenticated: false,
      },
      {
        status: 401,
      },
    );
  }

  try {
    const response = await fetch(
      `${BACKEND_API_URL}/auth/me`,
      {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        cache: "no-store",
      },
    );

    if (!response.ok) {
      const result = NextResponse.json(
        {
          authenticated: false,
        },
        {
          status: 401,
        },
      );

      result.cookies.set(
        SESSION_COOKIE_NAME,
        "",
        {
          ...sessionCookieOptions,
          maxAge: 0,
        },
      );

      return result;
    }

    const user = await response.json();

    return NextResponse.json({
      authenticated: true,
      user,
    });
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