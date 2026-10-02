import { LifeBuoy } from "lucide-react";
import ReactMarkdown from "react-markdown";

import { SupportUIRenderer } from "@/components/support/support-ui";
import type { SupportRoute } from "@/types/api";
import type { SupportMessage } from "@/components/support/support-types";

function routeLabel(route?: SupportRoute) {
  switch (route) {
    case "order":
      return "Order support";
    case "knowledge":
      return "Knowledge";
    case "returns":
      return "Returns";
    case "cancellation":
      return "Cancellation";
    case "escalation":
      return "Human support";
    case "confirmation":
      return "Confirmation required";
    default:
      return null;
  }
}

export function SupportMessageItem({
  message,
  actionable,
  isSending,
  onConfirm,
  onDecline,
}: {
  message: SupportMessage;
  actionable: boolean;
  isSending: boolean;
  onConfirm: () => void;
  onDecline: () => void;
}) {
  const label = routeLabel(message.route);

  return (
    <div
      className={
        message.role === "user"
          ? "ml-auto max-w-[85%] md:max-w-[72%]"
          : "mr-auto max-w-[92%] md:max-w-[80%]"
      }
    >
      <div className="mb-2 flex items-center gap-2 text-xs text-muted-foreground">
        {message.role === "assistant" ? (
          <>
            <div className="flex size-6 items-center justify-center rounded-md bg-primary text-primary-foreground">
              <LifeBuoy className="size-3.5" />
            </div>
            <span className="font-medium text-foreground">VoltNest Support</span>
            {label && <span> · {label}</span>}
          </>
        ) : (
          <span className="ml-auto font-medium text-foreground">You</span>
        )}
      </div>

      <div
        className={
          message.role === "user"
            ? "whitespace-pre-wrap rounded-2xl rounded-tr-md bg-primary px-4 py-3 text-sm leading-6 text-primary-foreground"
            : "rounded-2xl rounded-tl-md border bg-card px-4 py-3 text-sm leading-6"
        }
      >
        {message.role === "assistant" ? (
          <ReactMarkdown
            components={{
              p: ({ children }) => <p className="mb-3 last:mb-0">{children}</p>,
              strong: ({ children }) => (
                <strong className="font-semibold text-foreground">{children}</strong>
              ),
              ul: ({ children }) => (
                <ul className="my-3 list-disc space-y-1 pl-5">{children}</ul>
              ),
              ol: ({ children }) => (
                <ol className="my-3 list-decimal space-y-1 pl-5">{children}</ol>
              ),
              li: ({ children }) => <li>{children}</li>,
              code: ({ children }) => (
                <code className="rounded bg-muted px-1 py-0.5 font-mono text-[0.9em]">
                  {children}
                </code>
              ),
            }}
          >
            {message.content}
          </ReactMarkdown>
        ) : (
          <div className="whitespace-pre-wrap">{message.content}</div>
        )}

        {message.role === "assistant" && message.ui && (
          <SupportUIRenderer
            ui={message.ui}
            actionable={actionable}
            isSending={isSending}
            onConfirm={onConfirm}
            onDecline={onDecline}
          />
        )}
      </div>
    </div>
  );
}

export function SupportTypingIndicator() {
  return (
    <div className="mr-auto max-w-[80%]" role="status" aria-live="polite">
      <div className="mb-2 flex items-center gap-2 text-xs">
        <div className="flex size-6 items-center justify-center rounded-md bg-primary text-primary-foreground">
          <LifeBuoy className="size-3.5" />
        </div>
        <span className="font-medium">VoltNest Support</span>
      </div>
      <div className="flex items-center gap-1.5 rounded-2xl rounded-tl-md border bg-card px-4 py-4">
        <span className="size-1.5 animate-pulse rounded-full bg-muted-foreground" />
        <span className="size-1.5 animate-pulse rounded-full bg-muted-foreground [animation-delay:150ms]" />
        <span className="size-1.5 animate-pulse rounded-full bg-muted-foreground [animation-delay:300ms]" />
        <span className="sr-only">VoltNest Support is responding</span>
      </div>
    </div>
  );
}
