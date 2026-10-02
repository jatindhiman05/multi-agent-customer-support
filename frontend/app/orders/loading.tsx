import { Skeleton } from "@/components/ui/skeleton";

export default function Loading() {
  return (
    <div className="min-h-screen bg-muted/20">
      <div className="border-b bg-background">
        <div className="mx-auto flex h-16 max-w-6xl items-center px-4 md:px-6">
          <Skeleton className="h-9 w-36" />
        </div>
      </div>

      <main className="mx-auto max-w-6xl px-4 py-8 md:px-6 md:py-12">
        <Skeleton className="h-9 w-48" />
        <Skeleton className="mt-3 h-5 w-72" />

        <div className="mt-8 space-y-4">
          {[1, 2, 3].map(
            (item) => (
              <Skeleton
                key={item}
                className="h-28 w-full rounded-2xl"
              />
            ),
          )}
        </div>
      </main>
    </div>
  );
}