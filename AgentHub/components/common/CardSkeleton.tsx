import { Card } from "./Card";
import { Skeleton } from "./Skeleton";

export function CardSkeleton() {
  return (
    <Card>
      <div className="relative">
        <div className="absolute top-0 right-0">
          <Skeleton className="h-10 w-10 rounded-lg" />
        </div>
        <Skeleton className="h-4 w-24 mb-3" />
        <Skeleton className="h-8 w-16 mt-2" />
      </div>
    </Card>
  );
}

