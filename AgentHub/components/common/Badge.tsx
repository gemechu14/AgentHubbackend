import type { ReactNode } from "react";

interface BadgeProps {
  variant?: "default" | "success" | "warning";
  children: ReactNode;
}

const variantClasses: Record<NonNullable<BadgeProps["variant"]>, string> = {
  default: "bg-slate-100 text-slate-700 ring-1 ring-slate-200",
  success: "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200",
  warning: "bg-slate-100 text-slate-700 ring-1 ring-slate-200",
};

export function Badge({ variant = "default", children }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-medium ${variantClasses[variant]}`}
    >
      {children}
    </span>
  );
}


