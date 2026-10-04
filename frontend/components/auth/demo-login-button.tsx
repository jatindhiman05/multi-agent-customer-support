"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  LoaderCircle,
} from "lucide-react";

import { Button } from "@/components/ui/button";

export function DemoLoginButton({
  className,
}: {
  className?: string;
}) {
  const router = useRouter();

  const [isLoading, setIsLoading] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  async function handleDemoLogin() {
    if (isLoading) {
      return;
    }

    setError(null);
    setIsLoading(true);

    try {
      const response = await fetch(
        "/api/auth/demo",
        {
          method: "POST",
        },
      );

      const data = await response.json();

      if (!response.ok) {
        setError(
          data.detail ??
            "Unable to start the demo.",
        );
        return;
      }

      router.push("/support");
      router.refresh();
    } catch {
      setError(
        "Unable to connect to VoltNest. Please try again.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div>
      <Button
        type="button"
        size="lg"
        onClick={handleDemoLogin}
        disabled={isLoading}
        className={className}
      >
        {isLoading ? (
          <>
            <LoaderCircle className="size-4 animate-spin" />
            Starting demo...
          </>
        ) : (
          <>
            Try live demo
            <ArrowRight className="size-4" />
          </>
        )}
      </Button>

      {error && (
        <p
          role="alert"
          className="mt-2 text-sm text-destructive"
        >
          {error}
        </p>
      )}
    </div>
  );
}