import type { FormEvent, KeyboardEvent } from "react";
import { ArrowUp, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import type { SupportError } from "@/components/support/support-types";

export function SupportComposer({
  input,
  error,
  disabled,
  onInputChange,
  onSend,
  onDismissError,
}: {
  input: string;
  error: SupportError | null;
  disabled: boolean;
  onInputChange: (value: string) => void;
  onSend: (message: string) => void;
  onDismissError: () => void;
}) {
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!disabled && input.trim()) {
      onSend(input);
    }
  }

  function keyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (!disabled && input.trim()) {
        onSend(input);
      }
    }
  }

  return (
    <div className="shrink-0 border-t bg-background px-4 py-4 md:px-8">
      <div className="mx-auto w-full max-w-4xl">
        {error && (
          <div
            role="alert"
            className="mb-3 flex items-start justify-between gap-3 rounded-lg border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive"
          >
            <div>
              <p>{error.message}</p>
              {error.kind === "network" && (
                <p className="mt-1 text-xs opacity-80">
                  Your message is still visible above. Check your connection before sending it again.
                </p>
              )}
            </div>
            <button
              type="button"
              onClick={onDismissError}
              aria-label="Dismiss error"
              className="rounded-sm p-1 hover:bg-destructive/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <X className="size-4" />
            </button>
          </div>
        )}

        <form onSubmit={submit} className="relative">
          <Textarea
            value={input}
            onChange={(event) => onInputChange(event.target.value)}
            onKeyDown={keyDown}
            placeholder="Ask VoltNest Support..."
            className="min-h-14 max-h-40 resize-none pr-14"
            maxLength={4000}
            disabled={disabled}
            aria-label="Support message"
          />
          <Button
            type="submit"
            size="icon"
            className="absolute bottom-3 right-3"
            disabled={disabled || !input.trim()}
            aria-label="Send message"
          >
            <ArrowUp className="size-4" />
          </Button>
        </form>

        <p className="mt-2 text-center text-[11px] text-muted-foreground">
          Review order changes before confirming them.
        </p>
      </div>
    </div>
  );
}
