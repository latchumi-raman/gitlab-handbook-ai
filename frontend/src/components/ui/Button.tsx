import { cn } from "@/lib/utils";
import type { ButtonHTMLAttributes } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "ghost" | "danger";
  size?:    "sm" | "md";
}

export function Button({ variant = "ghost", size = "md", className, children, ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-1.5 rounded-lg font-medium transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed select-none",
        size === "sm" ? "px-2.5 py-1 text-xs" : "px-3.5 py-2 text-sm",
        variant === "primary" && "bg-gitlab-orange hover:bg-gitlab-red text-white",
        variant === "ghost"   && "hover:bg-surface-100 dark:hover:bg-surface-800 text-gray-600 dark:text-gray-400",
        variant === "danger"  && "hover:bg-red-50 dark:hover:bg-red-900/20 text-red-500",
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}