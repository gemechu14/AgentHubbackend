import type { ReactNode } from "react";

interface SkeletonProps {
  className?: string;
  children?: ReactNode;
}

export function Skeleton({ className = "", children }: SkeletonProps) {
  return (
    <div
      className={`animate-pulse rounded bg-slate-200 ${className}`}
      aria-label="Loading..."
    >
      {children}
    </div>
  );
}

