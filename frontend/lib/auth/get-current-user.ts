import "server-only";

import { cookies } from "next/headers";

import { BACKEND_API_URL } from "@/lib/api/server";
import { SESSION_COOKIE_NAME } from "@/lib/auth/session";

export interface CurrentUser {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
}

export async function getCurrentUser():
  Promise<CurrentUser | null> {
  const cookieStore = await cookies();

  const token = cookieStore.get(
    SESSION_COOKIE_NAME,
  )?.value;

  if (!token) {
    return null;
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
      return null;
    }

    const user =
      (await response.json()) as CurrentUser;

    return user;
  } catch {
    return null;
  }
}