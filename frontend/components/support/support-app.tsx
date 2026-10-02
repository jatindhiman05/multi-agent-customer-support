"use client";



import Link from "next/link";

import {
  useRouter
} from "next/navigation";

import {

  FormEvent,

  KeyboardEvent,

  useCallback,

  useEffect,

  useRef,

  useState,

} from "react";

import {

  ArrowUp,

  Headphones,

  LifeBuoy,

  Loader2,

  Menu,

  MessageSquareText,

  PackageSearch,

  Plus,

  RotateCcw,

  ShieldCheck,

  Trash2,

  Truck,

  XCircle,

} from "lucide-react";



import { LogoutButton } from "@/components/auth/logout-button";

import {

  Avatar,

  AvatarFallback,

} from "@/components/ui/avatar";

import { Button } from "@/components/ui/button";

import {

  Sheet,

  SheetContent,

  SheetDescription,

  SheetHeader,

  SheetTitle,

  SheetTrigger,

} from "@/components/ui/sheet";

import { Textarea } from "@/components/ui/textarea";

import type { CurrentUser } from "@/lib/auth/get-current-user";

import type {

  ChatResponse,

  ConversationHistory,

  ConversationSummary,

  SupportRoute,

} from "@/types/api";



type Message = {

  id: string;

  role: "user" | "assistant";

  content: string;

  route?: SupportRoute;

};



type QuickAction = {

  label: string;

  description: string;

  prompt: string;

  icon: typeof Truck;

};



const QUICK_ACTIONS: QuickAction[] = [

  {

    label: "Track an order",

    description: "Get the latest delivery status",

    prompt: "I want to track my order.",

    icon: Truck,

  },

  {

    label: "Return an item",

    description: "Check eligibility and start a return",

    prompt: "I want to return an item from my order.",

    icon: RotateCcw,

  },

  {

    label: "Cancel an order",

    description: "Check whether an order can be cancelled",

    prompt: "I want to cancel my order.",

    icon: XCircle,

  },

  {

    label: "Warranty & policies",

    description: "Ask about coverage or store policies",

    prompt:

      "I have a question about warranty or store policy.",

    icon: ShieldCheck,

  },

];



function initials(user: CurrentUser) {

  return (

    `${user.first_name[0] ?? ""}` +

    `${user.last_name[0] ?? ""}`

  ).toUpperCase();

}



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



function Sidebar({

  user,

  conversations,

  activeConversationId,

  isLoadingConversations,

  isLoadingConversation,

  onNewConversation,

  onSelectConversation,

}: {

  user: CurrentUser;

  conversations: ConversationSummary[];

  activeConversationId: string | null;

  isLoadingConversations: boolean;

  isLoadingConversation: boolean;

  onNewConversation: () => void;

  onSelectConversation: (conversationId: string) => void;

}) {

  return (

    <div className="flex h-full flex-col">

      <div className="flex h-16 items-center gap-3 border-b px-5">

        <div className="flex size-9 items-center justify-center rounded-xl bg-primary text-primary-foreground">

          <LifeBuoy className="size-5" />

        </div>



        <div>

          <p className="font-semibold tracking-tight">

            VoltNest

          </p>



          <p className="text-xs text-muted-foreground">

            Customer Support

          </p>

        </div>

      </div>



      <div className="p-4">

        <Button

          className="w-full justify-start"

          onClick={onNewConversation}

          disabled={isLoadingConversation}

        >

          <Plus className="size-4" />

          New conversation

        </Button>



        <Button

          variant="ghost"

          className="mt-2 w-full justify-start"

          render={<Link href="/orders" />}

        >

          <PackageSearch className="size-4" />

          My orders

        </Button>

      </div>



      <div className="min-h-0 flex-1 px-3">

        <p className="px-2 pb-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">

          Conversations

        </p>



        <div className="h-full overflow-y-auto pb-4">

          {isLoadingConversations ? (

            <div className="flex items-center gap-2 px-3 py-3 text-sm text-muted-foreground">

              <Loader2 className="size-4 animate-spin" />

              Loading conversations...

            </div>

          ) : conversations.length === 0 ? (

            <p className="px-2 py-3 text-sm leading-6 text-muted-foreground">

              Your support conversations will appear here.

            </p>

          ) : (

            <div className="space-y-1">

              {conversations.map((conversation) => {

                const active =

                  conversation.id === activeConversationId;



                return (

                  <button

                    key={conversation.id}

                    type="button"

                    onClick={() =>

                      onSelectConversation(conversation.id)

                    }

                    disabled={isLoadingConversation}

                    className={`flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm transition-colors ${

                      active

                        ? "bg-muted font-medium"

                        : "text-muted-foreground hover:bg-muted/60 hover:text-foreground"

                    }`}

                  >

                    <MessageSquareText className="size-4 shrink-0" />



                    <span className="truncate">

                      {conversation.title ??

                        "Support conversation"}

                    </span>

                  </button>

                );

              })}

            </div>

          )}

        </div>

      </div>



      <div className="border-t p-4">

        <div className="mb-3 flex items-center gap-3">

          <Avatar>

            <AvatarFallback>

              {initials(user)}

            </AvatarFallback>

          </Avatar>



          <div className="min-w-0 flex-1">

            <p className="truncate text-sm font-medium">

              {user.first_name} {user.last_name}

            </p>



            <p className="truncate text-xs text-muted-foreground">

              {user.email}

            </p>

          </div>

        </div>



        <LogoutButton />

      </div>

    </div>

  );

}



export function SupportApp({
  user,
  initialConversations,
  initialHistory,
}: {
  user: CurrentUser;
  initialConversations: ConversationSummary[];
  initialHistory: ConversationHistory | null;
}) {

  const router = useRouter();






  const [messages, setMessages] = useState<Message[]>(
  () =>
    initialHistory?.messages.map(
      (message) => ({
        id: message.id,
        role: message.role,
        content: message.content,
        route: message.route ?? undefined,
      }),
    ) ?? [],
);



  const [
  conversationId,
  setConversationId,
] = useState<string | null>(
  initialHistory?.id ?? null,
);



  const [
  conversations,
  setConversations,
] = useState<ConversationSummary[]>(
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



  const [error, setError] = useState<string | null>(null);



  const endRef = useRef<HTMLDivElement>(null);

  const loadingConversationRef = useRef(false);



  useEffect(() => {

    endRef.current?.scrollIntoView({

      behavior: "smooth",

    });

  }, [messages, isSending]);



  const handleAuthenticationFailure = useCallback(() => {
    router.replace("/login");
    router.refresh();
  }, [router]);

  const loadConversations = useCallback(async () => {
    try {
      setIsLoadingConversations(true);

      const response = await fetch(
        "/api/conversations",
        {
          method: "GET",
          cache: "no-store",
        },
      );

      const data = await response.json();

      if (!response.ok) {
        if (
          response.status === 401 ||
          response.status === 403
        ) {
          handleAuthenticationFailure();
          return;
        }

        throw new Error(
          data.detail ??
            "Unable to load conversations.",
        );
      }

      setConversations(
        data as ConversationSummary[],
      );
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "Unable to load conversations.",
      );
    } finally {
      setIsLoadingConversations(false);
    }
  }, [handleAuthenticationFailure]);

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

        const response = await fetch(
          `/api/conversations/${encodeURIComponent(
            selectedConversationId,
          )}/messages`,
          {
            method: "GET",
            cache: "no-store",
          },
        );

        const data = await response.json();

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
            router.replace("/support");
            setError(
              "That conversation is no longer available.",
            );
            return;
          }

          throw new Error(
            data.detail ??
              "Unable to load this conversation.",
          );
        }

        const history = data as ConversationHistory;

        const loadedMessages: Message[] =
          history.messages.map((message) => ({
            id: message.id,
            role: message.role,
            content: message.content,
            route: message.route ?? undefined,
          }));

        setConversationId(history.id);
        setMessages(loadedMessages);
        setInput("");

        router.replace(
            `/support?conversation=${encodeURIComponent(
              history.id,
            )}`,
            { scroll: false },
          );
      } catch (caughtError) {
        setError(
          caughtError instanceof Error
            ? caughtError.message
            : "Unable to load this conversation.",
        );
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

    isLoadingConversation

  ) {

    return;

  }



  setMessages([]);

  setConversationId(null);

  setInput("");

  setError(null);



  router.replace("/support", {

    scroll: false,

  });

}



  async function sendMessage(

    rawMessage: string,

  ) {

    const message = rawMessage.trim();



    if (

      !message ||

      isSending ||

      isLoadingConversation

    ) {

      return;

    }



    const currentConversationId =

      conversationId;



    const userMessage: Message = {

      id: crypto.randomUUID(),

      role: "user",

      content: message,

    };



    setMessages((current) => [

      ...current,

      userMessage,

    ]);



    setInput("");

    setError(null);

    setIsSending(true);



    try {

      const response = await fetch(

        "/api/chat",

        {

          method: "POST",

          headers: {

            "Content-Type":

              "application/json",

          },

          body: JSON.stringify({

            message,

            conversation_id:

              currentConversationId,

          }),

        },

      );



      const data = await response.json();



      if (!response.ok) {

        if (

          response.status === 401 ||

          response.status === 403

        ) {

          handleAuthenticationFailure();

          return;

        }



        throw new Error(

          data.detail ??

            "Unable to send your message.",

        );

      }



      const result = data as ChatResponse;



      setConversationId(

        result.conversation_id,

      );



      router.replace(

  `/support?conversation=${encodeURIComponent(

    result.conversation_id,

  )}`,

  {

    scroll: false,

  },

);



      setMessages((current) => [

        ...current,

        {

          id: crypto.randomUUID(),

          role: "assistant",

          content: result.response,

          route: result.route,

        },

      ]);



      await loadConversations();

    } catch (caughtError) {

      setError(

        caughtError instanceof Error

          ? caughtError.message

          : "Something went wrong. Please try again.",

      );

    } finally {

      setIsSending(false);

    }

  }



  function handleSubmit(

    event: FormEvent<HTMLFormElement>,

  ) {

    event.preventDefault();



    void sendMessage(input);

  }



  function handleKeyDown(

    event: KeyboardEvent<HTMLTextAreaElement>,

  ) {

    if (

      event.key === "Enter" &&

      !event.shiftKey

    ) {

      event.preventDefault();



      void sendMessage(input);

    }

  }



  const empty = messages.length === 0;



  const sidebarProps = {

    user,

    conversations,

    activeConversationId: conversationId,

    isLoadingConversations,

    isLoadingConversation,

    onNewConversation: newConversation,

    onSelectConversation: (

      selectedConversationId: string,

    ) => {

      void loadConversation(

        selectedConversationId,

      );

    },

  };



  return (

    <div className="h-dvh overflow-hidden bg-background">

      <aside className="fixed inset-y-0 left-0 hidden w-72 border-r bg-muted/20 lg:block">

        <Sidebar {...sidebarProps} />

      </aside>



      <div className="flex h-full flex-col lg:pl-72">

        <header className="flex h-16 shrink-0 items-center justify-between border-b bg-background/95 px-4 md:px-6">

          <div className="flex items-center gap-3">

            <Sheet>

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



                <Sidebar {...sidebarProps} />

              </SheetContent>

            </Sheet>



            <div>

              <h1 className="font-semibold tracking-tight">

                Support

              </h1>



              <p className="hidden text-xs text-muted-foreground sm:block">

                Orders, returns, warranty and account help

              </p>

            </div>

          </div>



          <div className="flex items-center gap-2 text-sm text-muted-foreground">

            <span className="hidden sm:inline">

              Signed in as

            </span>



            <span className="font-medium text-foreground">

              {user.first_name}

            </span>

          </div>

        </header>



        <main className="min-h-0 flex-1 overflow-y-auto">

          <div className="mx-auto flex min-h-full w-full max-w-4xl flex-col px-4 md:px-8">

            {isLoadingConversation ? (

              <div className="flex flex-1 items-center justify-center">

                <div className="flex items-center gap-2 text-sm text-muted-foreground">

                  <Loader2 className="size-4 animate-spin" />

                  Loading conversation...

                </div>

              </div>

            ) : empty ? (

              <div className="flex flex-1 flex-col justify-center py-12 md:py-20">

                <div className="mx-auto w-full max-w-2xl">

                  <div className="mb-8">

                    <div className="mb-4 flex size-11 items-center justify-center rounded-xl border bg-muted/40">

                      <Headphones className="size-5" />

                    </div>



                    <h2 className="text-2xl font-semibold tracking-tight md:text-3xl">

                      How can we help,{" "}

                      {user.first_name}?

                    </h2>



                    <p className="mt-2 max-w-xl text-sm leading-6 text-muted-foreground md:text-base">

                      Ask about an order, return,

                      cancellation, warranty, payment,

                      delivery issue, or anything else

                      related to VoltNest.

                    </p>

                  </div>



                  <div className="grid gap-3 sm:grid-cols-2">

                    {QUICK_ACTIONS.map(

                      (action) => {

                        const Icon =

                          action.icon;



                        return (

                          <button

                            key={action.label}

                            type="button"

                            onClick={() =>

                              void sendMessage(

                                action.prompt,

                              )

                            }

                            className="group rounded-xl border bg-card p-4 text-left transition-colors hover:bg-muted/40 disabled:opacity-50"

                            disabled={

                              isSending ||

                              isLoadingConversation

                            }

                          >

                            <Icon className="mb-3 size-5 text-muted-foreground transition-colors group-hover:text-foreground" />



                            <p className="text-sm font-medium">

                              {action.label}

                            </p>



                            <p className="mt-1 text-xs leading-5 text-muted-foreground">

                              {action.description}

                            </p>

                          </button>

                        );

                      },

                    )}

                  </div>

                </div>

              </div>

            ) : (

              <div className="flex-1 space-y-7 py-8">

                {messages.map(

                  (message) => (

                    <div

                      key={message.id}

                      className={

                        message.role === "user"

                          ? "ml-auto max-w-[85%] md:max-w-[72%]"

                          : "mr-auto max-w-[92%] md:max-w-[80%]"

                      }

                    >

                      <div className="mb-2 flex items-center gap-2 text-xs text-muted-foreground">

                        {message.role ===

                        "assistant" ? (

                          <>

                            <div className="flex size-6 items-center justify-center rounded-md bg-primary text-primary-foreground">

                              <LifeBuoy className="size-3.5" />

                            </div>



                            <span className="font-medium text-foreground">

                              VoltNest Support

                            </span>



                            {routeLabel(

                              message.route,

                            ) && (

                              <span>

                                {" "}

                                ·{" "}

                                {routeLabel(

                                  message.route,

                                )}

                              </span>

                            )}

                          </>

                        ) : (

                          <span className="ml-auto font-medium text-foreground">

                            You

                          </span>

                        )}

                      </div>



                      <div

                        className={

                          message.role === "user"

                            ? "whitespace-pre-wrap rounded-2xl rounded-tr-md bg-primary px-4 py-3 text-sm leading-6 text-primary-foreground"

                            : "whitespace-pre-wrap rounded-2xl rounded-tl-md border bg-card px-4 py-3 text-sm leading-6"

                        }

                      >

                        {message.content}

                      </div>

                    </div>

                  ),

                )}



                {isSending && (

                  <div className="mr-auto max-w-[80%]">

                    <div className="mb-2 flex items-center gap-2 text-xs">

                      <div className="flex size-6 items-center justify-center rounded-md bg-primary text-primary-foreground">

                        <LifeBuoy className="size-3.5" />

                      </div>



                      <span className="font-medium">

                        VoltNest Support

                      </span>

                    </div>



                    <div className="flex items-center gap-1.5 rounded-2xl rounded-tl-md border bg-card px-4 py-4">

                      <span className="size-1.5 animate-pulse rounded-full bg-muted-foreground" />

                      <span className="size-1.5 animate-pulse rounded-full bg-muted-foreground [animation-delay:150ms]" />

                      <span className="size-1.5 animate-pulse rounded-full bg-muted-foreground [animation-delay:300ms]" />

                    </div>

                  </div>

                )}



                <div ref={endRef} />

              </div>

            )}

          </div>

        </main>



        <div className="shrink-0 border-t bg-background px-4 py-4 md:px-8">

          <div className="mx-auto w-full max-w-4xl">

            {error && (

              <div

                role="alert"

                className="mb-3 flex items-start justify-between gap-3 rounded-lg border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive"

              >

                <span>{error}</span>



                <button

                  type="button"

                  onClick={() =>

                    setError(null)

                  }

                  aria-label="Dismiss error"

                >

                  <Trash2 className="size-4" />

                </button>

              </div>

            )}



            <form

              onSubmit={handleSubmit}

              className="relative"

            >

              <Textarea

                value={input}

                onChange={(event) =>

                  setInput(

                    event.target.value,

                  )

                }

                onKeyDown={handleKeyDown}

                placeholder="Ask VoltNest Support..."

                className="min-h-14 max-h-40 resize-none pr-14"

                maxLength={4000}

                disabled={

                  isSending ||

                  isLoadingConversation

                }

                aria-label="Support message"

              />



              <Button

                type="submit"

                size="icon"

                className="absolute bottom-3 right-3"

                disabled={

                  isSending ||

                  isLoadingConversation ||

                  !input.trim()

                }

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

      </div>

    </div>

  );

}