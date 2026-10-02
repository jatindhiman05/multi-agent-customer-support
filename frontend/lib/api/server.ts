import "server-only";

const apiUrl = process.env.BACKEND_API_URL;

if (!apiUrl) {
  throw new Error(
    "BACKEND_API_URL is not configured.",
  );
}

export const BACKEND_API_URL =
  apiUrl.replace(/\/$/, "");