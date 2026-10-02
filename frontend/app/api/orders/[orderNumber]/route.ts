import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { BACKEND_API_URL } from "@/lib/api/server";
import { SESSION_COOKIE_NAME } from "@/lib/auth/session";
import type { OrderDetail } from "@/types/api";

type RouteContext = {
  params: Promise<{
    orderNumber: string;
  }>;
};

export async function GET(
  _request: Request,
  context: RouteContext,
) {
  const { orderNumber } =
    await context.params;

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

  try {
    const response = await fetch(
      `${BACKEND_API_URL}/orders/${encodeURIComponent(
        orderNumber,
      )}`,
      {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
        },
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
            "Unable to load this order.",
        },
        {
          status: response.status,
        },
      );
    }

    return NextResponse.json(
      data as OrderDetail,
    );
  } catch {
    return NextResponse.json(
      {
        detail:
          "VoltNest Orders is temporarily unavailable.",
      },
      {
        status: 503,
      },
    );
  }
}