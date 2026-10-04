"use client";



import Link from "next/link";

import { useRouter } from "next/navigation";

import { useCallback, useEffect, useRef, useState } from "react";

import { Loader2, Menu, User } from "lucide-react";



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


  ConversationHistory,

  ConversationSummary,

} from "@/types/api";



function messagesFromHistory(

  history: ConversationHistory,

): SupportMessage[] {

  return history.messages.map((message) => ({

    id: message.id,

    role: message.role,

    content: message.content,

    route: message.route ?? undefined,

    ui: message.ui,

  }));

}



async function readJson(

  response: Response,

): Promise<Record<string, unknown>> {

  try {

    return (await response.json()) as Record<string, unknown>;

  } catch {

    return {};

  }

}



function detailFrom(

  data: Record<string, unknown>,

  fallback: string,

) {

  return typeof data.detail === "string"

    ? data.detail

    : fallback;

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

    () =>

      initialHistory

        ? messagesFromHistory(initialHistory)

        : [],

  );



  const [conversationId, setConversationId] =

    useState<string | null>(

      initialHistory?.id ?? null,

    );



  const [conversations, setConversations] =

    useState<ConversationSummary[]>(

      initialConversations,

    );



  const [

    isLoadingConversations,

    setIsLoadingConversations,

  ] = useState(false);



  const [

    isLoadingConversation,

    setIsLoadingConversation,

  ] = useState(false);



  const [input, setInput] = useState("");

  const [isSending, setIsSending] = useState(false);



  const [

    deletingConversationId,

    setDeletingConversationId,

  ] = useState<string | null>(null);



  const [

    isMobileNavigationOpen,

    setIsMobileNavigationOpen,

  ] = useState(false);



  const [error, setError] =

    useState<SupportError | null>(null);



  type PendingChatRetry = {

    requestId: string;

    message: string;

    conversationId: string | null;

  };



  const [pendingChatRetry, setPendingChatRetry] =

    useState<PendingChatRetry | null>(null);



  const [orderNumber, setOrderNumber] =

    useState<string | null>(

      initialOrderNumber,

    );



  const loadingConversationRef = useRef(false);



  /*

   * Scroll only the conversation container.

   *

   * Using scrollIntoView() on a bottom sentinel can also move

   * ancestor/viewport scroll positions. Keeping the scroll

   * operation scoped to <main> prevents the composer from being

   * pulled around when a message is sent.

   */

  const scrollContainerRef =

    useRef<HTMLElement>(null);



  useEffect(() => {

    const container = scrollContainerRef.current;



    if (!container) {

      return;

    }



    container.scrollTo({

      top: container.scrollHeight,

      behavior: "smooth",

    });

  }, [messages, isSending]);



  const handleAuthenticationFailure =

    useCallback(() => {

      router.replace("/login");

      router.refresh();

    }, [router]);



  const loadConversations = useCallback(

    async () => {

      try {

        setIsLoadingConversations(true);



        const response = await fetch(

          "/api/conversations",

          {

            method: "GET",

            cache: "no-store",

          },

        );



        const data = await readJson(response);



        if (!response.ok) {

          if (

            response.status === 401 ||

            response.status === 403

          ) {

            handleAuthenticationFailure();

            return;

          }



          throw new Error(

            detailFrom(

              data,

              "Unable to load conversations.",

            ),

          );

        }



        setConversations(

          data as unknown as ConversationSummary[],

        );

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

    },

    [handleAuthenticationFailure],

  );



  const loadConversation = useCallback(

    async (

      selectedConversationId: string,

    ) => {

      if (loadingConversationRef.current) {

        return;

      }



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

        setPendingChatRetry(null);



        const response = await fetch(

          `/api/conversations/${encodeURIComponent(

            selectedConversationId,

          )}/messages`,

          {

            method: "GET",

            cache: "no-store",

          },

        );



        const data = await readJson(response);



        if (!response.ok) {

          if (

            response.status === 401 ||

            response.status === 403

          ) {

            handleAuthenticationFailure();

            return;

          }



          if (response.status === 404) {

            setConversationId(null);

            setMessages([]);

            setOrderNumber(null);



            router.replace("/support", {

              scroll: false,

            });



            setError({

              kind: "request",

              message:

                "That conversation is no longer available.",

            });



            return;

          }



          throw new Error(

            detailFrom(

              data,

              "Unable to load this conversation.",

            ),

          );

        }



        const history =

          data as unknown as ConversationHistory;



        setConversationId(history.id);

        setMessages(

          messagesFromHistory(history),

        );

        setOrderNumber(null);

        setInput("");



        router.replace(

          `/support?conversation=${encodeURIComponent(

            history.id,

          )}`,

          {

            scroll: false,

          },

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

    if (

      isSending ||

      isLoadingConversation ||

      deletingConversationId

    ) {

      return;

    }



    setMessages([]);

    setConversationId(null);

    setOrderNumber(null);

    setInput("");

    setError(null);

    setPendingChatRetry(null);

    setIsMobileNavigationOpen(false);



    router.replace("/support", {

      scroll: false,

    });

  }



  async function deleteConversation(

    selectedConversationId: string,

    title: string | null,

  ) {

    if (

      isSending ||

      isLoadingConversation ||

      deletingConversationId

    ) {

      return;

    }



    const displayTitle =

      title?.trim() || "this conversation";



    const confirmed = window.confirm(

      `Delete "${displayTitle}"?\n\nThis conversation will be removed from your support history.`,

    );



    if (!confirmed) {

      return;

    }



    setDeletingConversationId(

      selectedConversationId,

    );

    setError(null);



    try {

      const response = await fetch(

        `/api/conversations/${encodeURIComponent(

          selectedConversationId,

        )}`,

        {

          method: "DELETE",

        },

      );



      if (!response.ok) {

        const data = await readJson(response);



        if (

          response.status === 401 ||

          response.status === 403

        ) {

          handleAuthenticationFailure();

          return;

        }



        /*

         * If another request/device already removed the

         * conversation, treat the UI state as deleted too.

         */

        if (response.status !== 404) {

          throw new Error(

            detailFrom(

              data,

              "Unable to delete this conversation.",

            ),

          );

        }

      }



      setConversations((current) =>

        current.filter(

          (conversation) =>

            conversation.id !==

            selectedConversationId,

        ),

      );



      if (

        selectedConversationId ===

        conversationId

      ) {

        setConversationId(null);

        setMessages([]);

        setOrderNumber(null);

        setInput("");

        setError(null);



        router.replace("/support", {

          scroll: false,

        });

      }



      setIsMobileNavigationOpen(false);

    } catch (caughtError) {

      setError({

        kind: "request",

        message:

          caughtError instanceof Error

            ? caughtError.message

            : "Unable to delete this conversation.",

      });

    } finally {

      setDeletingConversationId(null);

    }

  }



  async function executeChatRequest({

    requestId,

    message,

    currentConversationId,

    appendUserMessage,

  }: {

    requestId: string;

    message: string;

    currentConversationId: string | null;

    appendUserMessage: boolean;

  }) {



    const userMessage: SupportMessage = {

      id: crypto.randomUUID(),

      role: "user",

      content: message,

    };



    const assistantMessageId =

      crypto.randomUUID();



    const assistantMessage: SupportMessage = {

      id: assistantMessageId,

      role: "assistant",

      content: "",

    };



    /*

    * Add both immediately.

    *

    * The assistant message acts as the live streaming

    * target. Token events update this same message

    * instead of creating a new message per token.

    */

    setMessages((current) => [

      ...current,

      ...(appendUserMessage

        ? [userMessage]

        : []),

      assistantMessage,

    ]);



    setInput("");

    setError(null);

    setPendingChatRetry(null);

    setIsSending(true);



    try {

      const response = await fetch(

        "/api/chat/stream",

        {

          method: "POST",

          headers: {

            "Content-Type":

              "application/json",

            Accept:

              "application/x-ndjson",

          },

          body: JSON.stringify({

            request_id: requestId,

            message,

            conversation_id:

              currentConversationId,

          }),

        },

      );



      if (!response.ok) {

        const data = await readJson(response);



        /*

        * Remove the empty streaming placeholder.

        * The user's message remains visible.

        */

        setMessages((current) =>

          current.filter(

            (item) =>

              item.id !==

              assistantMessageId,

          ),

        );



        if (

          response.status === 401 ||

          response.status === 403

        ) {

          setPendingChatRetry(null);

          handleAuthenticationFailure();

          return;

        }



        if (response.status === 429) {

          setPendingChatRetry({

            requestId,

            message,

            conversationId: currentConversationId,

          });

          setError({

            kind: "rate_limit",

            message:

              "You're sending messages too quickly. Please wait a moment and try again.",

          });



          return;

        }



        if (response.status >= 500) {

          setPendingChatRetry({

            requestId,

            message,

            conversationId: currentConversationId,

          });

          setError({

            kind: "server",

            message:

              "VoltNest Support is temporarily unavailable. Your message remains visible above.",

          });



          return;

        }



        setError({

          kind: "request",

          message: detailFrom(

            data,

            "Unable to send your message.",

          ),

        });



        return;

      }



      if (!response.body) {

        setMessages((current) =>

          current.filter(

            (item) =>

              item.id !==

              assistantMessageId,

          ),

        );



        setPendingChatRetry({

          requestId,

          message,

          conversationId: currentConversationId,

        });

        setError({

          kind: "server",

          message:

            "VoltNest Support returned an empty response.",

        });



        return;

      }



      const reader =

        response.body.getReader();



      const decoder = new TextDecoder();



      let buffer = "";

      let streamedContent = "";

      let receivedFinal = false;



      const processLine = (

        line: string,

      ) => {

        if (!line.trim()) {

          return;

        }



        const event = JSON.parse(

          line,

        ) as Record<string, unknown>;



        const eventType = event.type;



        if (eventType === "started") {

          return;

        }



        if (eventType === "token") {

          const delta = event.delta;



          if (

            typeof delta !== "string"

          ) {

            throw new Error(

              "Invalid token event.",

            );

          }



          streamedContent += delta;



          setMessages((current) =>

            current.map((item) =>

              item.id ===

              assistantMessageId

                ? {

                    ...item,

                    content:

                      streamedContent,

                  }

                : item,

            ),

          );



          return;

        }



        if (eventType === "error") {

          const message =

            typeof event.message ===

            "string"

              ? event.message

              : "VoltNest Support could not process your request.";



          const statusCode =

            typeof event.status_code ===

            "number"

              ? event.status_code

              : 500;



          const streamError =

            new Error(message) as Error & {

              statusCode?: number;

            };



          streamError.statusCode =

            statusCode;



          throw streamError;

        }



        if (eventType === "final") {

          if (

            typeof event.response !==

              "string" ||

            typeof event.route !==

              "string" ||

            typeof

              event.conversation_id !==

              "string"

          ) {

            throw new Error(

              "Invalid final chat event.",

            );

          }



          receivedFinal = true;

          setPendingChatRetry(null);



          /*

          * The final event is authoritative.

          *

          * Even though streamedContent should equal

          * event.response, we deliberately replace

          * the accumulated text with the persisted

          * backend result.

          */

          setMessages((current) =>

            current.map((item) =>

              item.id ===

              assistantMessageId

                ? {

                    ...item,

                    content:

                      event.response as string,

                    route:

                      event.route as SupportMessage["route"],

                    ui:

                      (event.ui ??

                        null) as SupportMessage["ui"],

                  }

                : item,

            ),

          );



          const finalConversationId =

            event.conversation_id;



          setConversationId(

            finalConversationId,

          );



          setOrderNumber(null);



          router.replace(

            `/support?conversation=${encodeURIComponent(

              finalConversationId,

            )}`,

            {

              scroll: false,

            },

          );



          return;

        }



        throw new Error(

          "Unknown chat stream event.",

        );

      };



      while (true) {

        const {

          value,

          done,

        } = await reader.read();



        if (done) {

          break;

        }



        buffer += decoder.decode(

          value,

          {

            stream: true,

          },

        );



        const lines = buffer.split("\n");



        /*

        * The last entry may contain only part

        * of an NDJSON event, so retain it for

        * the next network chunk.

        */

        buffer = lines.pop() ?? "";



        for (const line of lines) {

          processLine(line);

        }

      }



      buffer += decoder.decode();



      if (buffer.trim()) {

        processLine(buffer);

      }



      if (!receivedFinal) {

        throw new Error(

          "Chat stream ended before the final response.",

        );

      }



      await loadConversations();

    } catch (caughtError) {

      /*

      * If some text streamed before the failure,

      * remove that partial assistant response.

      *

      * The backend final event is the authority,

      * so incomplete model output should not

      * remain looking like a completed answer.

      */

      setMessages((current) =>

        current.filter(

          (item) =>

            item.id !==

            assistantMessageId,

        ),

      );



      setPendingChatRetry({

        requestId,

        message,

        conversationId: currentConversationId,

      });



      const statusCode =

        caughtError instanceof Error &&

        "statusCode" in caughtError &&

        typeof (

          caughtError as Error & {

            statusCode?: unknown;

          }

        ).statusCode === "number"

          ? (

              caughtError as Error & {

                statusCode: number;

              }

            ).statusCode

          : null;



      if (statusCode === 409) {

        setPendingChatRetry(null);

        setError({

          kind: "request",

          message:

            caughtError instanceof Error

              ? caughtError.message

              : "This request is already being processed.",

        });



        return;

      }



      if (

        caughtError instanceof Error &&

        caughtError.message !==

          "Chat stream ended before the final response." &&

        caughtError.message !==

          "Invalid token event." &&

        caughtError.message !==

          "Invalid final chat event." &&

        caughtError.message !==

          "Unknown chat stream event."

      ) {

        setError({

          kind: "network",

          message:

            caughtError.message,

        });



        return;

      }



      setError({

        kind: "network",

        message:

          "The connection to VoltNest Support was interrupted. Your message remains visible above.",

      });

    } finally {

      setIsSending(false);

    }

  }



  async function sendMessage(

    rawMessage: string,

  ) {

    const message = rawMessage.trim();



    if (

      !message ||

      isSending ||

      isLoadingConversation ||

      deletingConversationId

    ) {

      return;

    }



    await executeChatRequest({

      requestId: crypto.randomUUID(),

      message,

      currentConversationId: conversationId,

      appendUserMessage: true,

    });

  }



  async function retryFailedMessage() {

    if (

      !pendingChatRetry ||

      isSending ||

      isLoadingConversation ||

      deletingConversationId

    ) {

      return;

    }



    await executeChatRequest({

      requestId: pendingChatRetry.requestId,

      message: pendingChatRetry.message,

      currentConversationId: pendingChatRetry.conversationId,

      appendUserMessage: false,

    });

  }



  const empty = messages.length === 0;

  const latestMessage = messages.at(-1);



  const busy =

    isSending ||

    isLoadingConversation ||

    deletingConversationId !== null;



  const sidebarProps = {

    user,

    conversations,

    activeConversationId:

      conversationId,

    isLoadingConversations,

    isLoadingConversation,

    isSending,

    deletingConversationId,



    onNewConversation:

      newConversation,



    onSelectConversation: (

      selectedConversationId: string,

    ) => {

      setIsMobileNavigationOpen(false);



      void loadConversation(

        selectedConversationId,

      );

    },



    onDeleteConversation: (

      selectedConversationId: string,

      title: string | null,

    ) => {

      void deleteConversation(

        selectedConversationId,

        title,

      );

    },

  };



  return (

    <div className="h-dvh overflow-hidden bg-background">

      <aside className="fixed inset-y-0 left-0 hidden w-72 border-r bg-muted/20 lg:block">

        <SupportSidebar

          {...sidebarProps}

        />

      </aside>



      <div className="flex h-full min-h-0 flex-col lg:pl-72">

        <header className="flex h-16 shrink-0 items-center justify-between border-b bg-background/95 px-4 md:px-6">

          <div className="flex items-center gap-3">

            <Sheet

              open={

                isMobileNavigationOpen

              }

              onOpenChange={

                setIsMobileNavigationOpen

              }

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

                <span className="sr-only">

                  Open navigation

                </span>

              </SheetTrigger>



              <SheetContent

                side="left"

                className="w-72 p-0"

                showCloseButton

              >

                <SheetHeader className="sr-only">

                  <SheetTitle>

                    VoltNest Support

                  </SheetTitle>

                  <SheetDescription>

                    Support navigation

                  </SheetDescription>

                </SheetHeader>



                <SupportSidebar

                  {...sidebarProps}

                />

              </SheetContent>

            </Sheet>



            <div>

              <h1 className="font-semibold tracking-tight">

                Support

              </h1>



              <p className="hidden text-xs text-muted-foreground sm:block">

                Orders, returns, warranty and

                account help

              </p>

            </div>

          </div>



          <div className="flex items-center gap-2">

            <span className="hidden text-sm text-muted-foreground md:inline">

              Signed in as{" "}

              <span className="font-medium text-foreground">

                {user.first_name}

              </span>

            </span>



            <Button

              variant="ghost"

              size="sm"

              render={

                <Link href="/account" />

              }

            >

              <User className="size-4" />

              <span className="hidden sm:inline">

                Account

              </span>

            </Button>

          </div>

        </header>



        <main

          ref={scrollContainerRef}

          className="min-h-0 flex-1 overflow-y-auto overscroll-contain"

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

                onSend={(message) =>

                  void sendMessage(message)

                }

              />

            ) : (

              <div className="flex-1 space-y-7 py-8">

                {messages.map(

                  (message) => {

                    const actionable =

                      message.role ===

                        "assistant" &&

                      message.ui?.type ===

                        "confirmation" &&

                      latestMessage?.id ===

                        message.id;



                    return (

                      <SupportMessageItem

                        key={message.id}

                        message={message}

                        actionable={

                          actionable

                        }

                        isSending={

                          isSending

                        }

                        onConfirm={() =>

                          void sendMessage(

                            "Confirm",

                          )

                        }

                        onDecline={() =>

                          void sendMessage(

                            "Decline",

                          )

                        }

                      />

                    );

                  },

                )}



                {isSending &&

            !(

              latestMessage?.role === "assistant" &&

              latestMessage.content.length > 0

            ) && (

              <SupportTypingIndicator />

            )}

              </div>

            )}

          </div>

        </main>



        <div className="shrink-0">

          <SupportComposer

            input={input}

            error={error}

            disabled={busy}

            canRetry={pendingChatRetry !== null}

            onInputChange={setInput}

            onSend={(message) =>

              void sendMessage(message)

            }

            onRetry={() =>

              void retryFailedMessage()

            }

            onDismissError={() => {

              setError(null);

              setPendingChatRetry(null);

            }}

          />

        </div>

      </div>

    </div>

  );

}