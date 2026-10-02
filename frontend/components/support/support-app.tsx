"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { Loader2, Menu } from "lucide-react";

import { SupportComposer } from "@/components/support/support-composer";
import { SupportEmptyState } from "@/components/support/support-empty-state";
import {
  SupportMessageItem,
  SupportTypingIndicator,
} from "@/components/support/support-message";
import { SupportSidebar } from "@/components/support/support-sidebar";
import type {
  SupportError,
  SupportMessage,
} from "@/components/support/support-types";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import type { CurrentUser } from "@/lib/auth/get-current-user";
import type {
  ChatResponse,
  ConversationHistory,
  ConversationSummary,
} from "@/types/api";

function messagesFromHistory(history: ConversationHistory): SupportMessage[] {
  return history.messages.map((message) => ({
    id: message.id,
    role: message.role,
    content: message.content,
    route: message.route ?? undefined,
    ui: message.ui,
  }));
}

async function readJson(response: Response): Promise<Record<string, unknown>> {
  try {
    return (await response.json()) as Record<string, unknown>;
  } catch {
    return {};
  }
}

function detailFrom(data: Record<string, unknown>, fallback: string) {
  return typeof data.detail === "string" ? data.detail : fallback;
}

export function SupportApp({
  user,
  initialConversations,
  initialHistory,
  initialOrderNumber,
}: {
  user: CurrentUser;
  initialConversations: ConversationSummary[];
  initialHistory: ConversationHistory | null;
  initialOrderNumber: string | null;
}) {
  const router = useRouter();

  const [messages, setMessages] = useState<SupportMessage[]>(
    () => (initialHistory ? messagesFromHistory(initialHistory) : []),
  );
  const [conversationId, setConversationId] = useState<string | null>(
    initialHistory?.id ?? null,
  );
  const [conversations, setConversations] =
    useState<ConversationSummary[]>(initialConversations);
  const [isLoadingConversations, setIsLoadingConversations] = useState(false);
  const [isLoadingConversation, setIsLoadingConversation] = useState(false);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isMobileNavigationOpen, setIsMobileNavigationOpen] = useState(false);
  const [error, setError] = useState<SupportError | null>(null);
  const [orderNumber, setOrderNumber] =
    useState<string | null>(
      initialOrderNumber,
    );
  const endRef = useRef<HTMLDivElement>(null);
  const loadingConversationRef = useRef(false);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSending]);

  const handleAuthenticationFailure = useCallback(() => {
    router.replace("/login");
    router.refresh();
  }, [router]);

  const loadConversations = useCallback(async () => {
    try {
      setIsLoadingConversations(true);
      const response = await fetch("/api/conversations", {
        method: "GET",
        cache: "no-store",
      });
      const data = await readJson(response);

      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          handleAuthenticationFailure();
          return;
        }
        throw new Error(detailFrom(data, "Unable to load conversations."));
      }

      setConversations(data as unknown as ConversationSummary[]);
    } catch (caughtError) {
      setError({
        kind: "request",
        message:
          caughtError instanceof Error
            ? caughtError.message
            : "Unable to load conversations.",
      });
    } finally {
      setIsLoadingConversations(false);
    }
  }, [handleAuthenticationFailure]);

  const loadConversation = useCallback(
    async (selectedConversationId: string) => {
      if (loadingConversationRef.current) return;

      if (
        selectedConversationId === conversationId &&
        messages.length > 0
      ) {
        return;
      }

      loadingConversationRef.current = true;

      try {
        setIsLoadingConversation(true);
        setError(null);

        const response = await fetch(
          `/api/conversations/${encodeURIComponent(selectedConversationId)}/messages`,
          { method: "GET", cache: "no-store" },
        );
        const data = await readJson(response);

        if (!response.ok) {
          if (response.status === 401 || response.status === 403) {
            handleAuthenticationFailure();
            return;
          }

          if (response.status === 404) {
            setConversationId(null);
            setMessages([]);
            router.replace("/support");
            setError({
              kind: "request",
              message: "That conversation is no longer available.",
            });
            return;
          }

          throw new Error(
            detailFrom(data, "Unable to load this conversation."),
          );
        }

        const history = data as unknown as ConversationHistory;
        setConversationId(history.id);
        setMessages(messagesFromHistory(history));
        setInput("");
        router.replace(
          `/support?conversation=${encodeURIComponent(history.id)}`,
          { scroll: false },
        );
      } catch (caughtError) {
        setError({
          kind: "request",
          message:
            caughtError instanceof Error
              ? caughtError.message
              : "Unable to load this conversation.",
        });
      } finally {
        loadingConversationRef.current = false;
        setIsLoadingConversation(false);
      }
    },
    [
      conversationId,
      handleAuthenticationFailure,
      messages.length,
      router,
    ],
  );

  function newConversation() {
    if (isSending || isLoadingConversation) return;

    setMessages([]);
    setConversationId(null);
    setOrderNumber(null);
    setInput("");
    setError(null);
    setIsMobileNavigationOpen(false);
    router.replace("/support", { scroll: false });
  }

  async function sendMessage(rawMessage: string) {
    const message = rawMessage.trim();

    if (!message || isSending || isLoadingConversation) return;

    const currentConversationId = conversationId;
    const userMessage: SupportMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: message,
    };

    setMessages((current) => [...current, userMessage]);
    setInput("");
    setError(null);
    setIsSending(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          conversation_id: currentConversationId,
        }),
      });
      const data = await readJson(response);

      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          handleAuthenticationFailure();
          return;
        }

        if (response.status === 429) {
          setError({
            kind: "rate_limit",
            message:
              "You're sending messages too quickly. Please wait a moment and try again.",
          });
          return;
        }

        if (response.status >= 500) {
          setError({
            kind: "server",
            message:
              "VoltNest Support is temporarily unavailable. Your message remains visible above.",
          });
          return;
        }

        setError({
          kind: "request",
          message: detailFrom(data, "Unable to send your message."),
        });
        return;
      }

      const result = data as unknown as ChatResponse;

      setConversationId(result.conversation_id);
      setOrderNumber(null);
      router.replace(
        `/support?conversation=${encodeURIComponent(result.conversation_id)}`,
        { scroll: false },
      );

      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: result.response,
          route: result.route,
          ui: result.ui,
        },
      ]);

      await loadConversations();
    } catch {
      setError({
        kind: "network",
        message:
          "Couldn't reach VoltNest Support. Check your connection before sending another message.",
      });
    } finally {
      setIsSending(false);
    }
  }

  const empty = messages.length === 0;
  const latestMessage = messages.at(-1);
  const busy = isSending || isLoadingConversation;

  const sidebarProps = {
    user,
    conversations,
    activeConversationId: conversationId,
    isLoadingConversations,
    isLoadingConversation,
    isSending,
    onNewConversation: newConversation,
    onSelectConversation: (selectedConversationId: string) => {
      setIsMobileNavigationOpen(false);
      void loadConversation(selectedConversationId);
    },
  };

  return (
    <div className="h-dvh overflow-hidden bg-background">
      <aside className="fixed inset-y-0 left-0 hidden w-72 border-r bg-muted/20 lg:block">
        <SupportSidebar {...sidebarProps} />
      </aside>

      <div className="flex h-full flex-col lg:pl-72">
        <header className="flex h-16 shrink-0 items-center justify-between border-b bg-background/95 px-4 md:px-6">
          <div className="flex items-center gap-3">
            <Sheet
              open={isMobileNavigationOpen}
              onOpenChange={setIsMobileNavigationOpen}
            >
              <SheetTrigger
                render={
                  <Button
                    variant="outline"
                    size="icon"
                    className="lg:hidden"
                  />
                }
              >
                <Menu className="size-4" />
                <span className="sr-only">Open navigation</span>
              </SheetTrigger>
              <SheetContent
                side="left"
                className="w-72 p-0"
                showCloseButton
              >
                <SheetHeader className="sr-only">
                  <SheetTitle>VoltNest Support</SheetTitle>
                  <SheetDescription>Support navigation</SheetDescription>
                </SheetHeader>
                <SupportSidebar {...sidebarProps} />
              </SheetContent>
            </Sheet>

            <div>
              <h1 className="font-semibold tracking-tight">Support</h1>
              <p className="hidden text-xs text-muted-foreground sm:block">
                Orders, returns, warranty and account help
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span className="hidden sm:inline">Signed in as</span>
            <span className="font-medium text-foreground">{user.first_name}</span>
          </div>
        </header>

        <main
          className="min-h-0 flex-1 overflow-y-auto"
          aria-label="Support conversation"
        >
          <div className="mx-auto flex min-h-full w-full max-w-4xl flex-col px-4 md:px-8">
            {isLoadingConversation ? (
              <div className="flex flex-1 items-center justify-center">
                <div
                  className="flex items-center gap-2 text-sm text-muted-foreground"
                  role="status"
                >
                  <Loader2 className="size-4 animate-spin" />
                  Loading conversation...
                </div>
              </div>
            ) : empty ? (
              <SupportEmptyState
                user={user}
                orderNumber={orderNumber}
                disabled={busy}
                onSend={(message) => void sendMessage(message)}
              />
            ) : (
              <div className="flex-1 space-y-7 py-8">
                {messages.map((message) => {
                  const actionable =
                    message.role === "assistant" &&
                    message.ui?.type === "confirmation" &&
                    latestMessage?.id === message.id;

                  return (
                    <SupportMessageItem
                      key={message.id}
                      message={message}
                      actionable={actionable}
                      isSending={isSending}
                      onConfirm={() => void sendMessage("Confirm")}
                      onDecline={() => void sendMessage("Decline")}
                    />
                  );
                })}

                {isSending && <SupportTypingIndicator />}
                <div ref={endRef} />
              </div>
            )}
          </div>
        </main>

        <SupportComposer
          input={input}
          error={error}
          disabled={busy}
          onInputChange={setInput}
          onSend={(message) => void sendMessage(message)}
          onDismissError={() => setError(null)}
        />
      </div>
    </div>
  );
}
