import Link from "next/link";
import {
  LifeBuoy,
  Loader2,
  MessageSquareText,
  MoreHorizontal,
  PackageSearch,
  Plus,
  Trash2,
} from "lucide-react";

import { LogoutButton } from "@/components/auth/logout-button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { CurrentUser } from "@/lib/auth/get-current-user";
import type { ConversationSummary } from "@/types/api";

function initials(user: CurrentUser) {
  return `${user.first_name[0] ?? ""}${user.last_name[0] ?? ""}`.toUpperCase();
}

export function SupportSidebar({
  user,
  conversations,
  activeConversationId,
  isLoadingConversations,
  isLoadingConversation,
  isSending,
  deletingConversationId,
  onNewConversation,
  onSelectConversation,
  onDeleteConversation,
}: {
  user: CurrentUser;
  conversations: ConversationSummary[];
  activeConversationId: string | null;
  isLoadingConversations: boolean;
  isLoadingConversation: boolean;
  isSending: boolean;
  deletingConversationId: string | null;
  onNewConversation: () => void;
  onSelectConversation: (conversationId: string) => void;
  onDeleteConversation: (
    conversationId: string,
    title: string | null,
  ) => void;
}) {
  const busy = isLoadingConversation || isSending;

  return (
    <div className="flex h-full flex-col">
      <div className="flex h-16 items-center gap-3 border-b px-5">
        <div className="flex size-9 items-center justify-center rounded-xl bg-primary text-primary-foreground">
          <LifeBuoy className="size-5" />
        </div>

        <div>
          <p className="font-semibold tracking-tight">VoltNest</p>
          <p className="text-xs text-muted-foreground">
            Customer Support
          </p>
        </div>
      </div>

      <div className="p-4">
        <Button
          className="w-full justify-start"
          onClick={onNewConversation}
          disabled={busy}
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

      <nav
        className="min-h-0 flex-1 px-3"
        aria-label="Support conversations"
      >
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

                const deleting =
                  conversation.id === deletingConversationId;

                return (
                  <div
                    key={conversation.id}
                    className={`group flex items-center rounded-lg transition-colors ${
                      active
                        ? "bg-muted"
                        : "hover:bg-muted/60"
                    }`}
                  >
                    <button
                      type="button"
                      onClick={() =>
                        onSelectConversation(conversation.id)
                      }
                      disabled={busy || deleting}
                      aria-current={active ? "page" : undefined}
                      className={`flex min-w-0 flex-1 items-center gap-2 rounded-lg px-3 py-2 text-left text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
                        active
                          ? "font-medium"
                          : "text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      {deleting ? (
                        <Loader2 className="size-4 shrink-0 animate-spin" />
                      ) : (
                        <MessageSquareText className="size-4 shrink-0" />
                      )}

                      <span className="truncate">
                        {conversation.title ??
                          "Support conversation"}
                      </span>
                    </button>

                    <DropdownMenu>
                      <DropdownMenuTrigger
                        render={
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            className="mr-1 size-8 shrink-0 opacity-70 transition-opacity hover:opacity-100 focus-visible:opacity-100 lg:opacity-0 lg:group-hover:opacity-100"
                            disabled={busy || deleting}
                            aria-label={`Conversation options for ${
                              conversation.title ??
                              "support conversation"
                            }`}
                          />
                        }
                      >
                        <MoreHorizontal className="size-4" />
                      </DropdownMenuTrigger>

                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          variant="destructive"
                          onClick={() =>
                            onDeleteConversation(
                              conversation.id,
                              conversation.title,
                            )
                          }
                        >
                          <Trash2 className="size-4" />
                          Delete conversation
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </nav>

      <div className="border-t p-4">
        <div className="mb-3 flex items-center gap-3">
          <Avatar>
            <AvatarFallback>{initials(user)}</AvatarFallback>
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