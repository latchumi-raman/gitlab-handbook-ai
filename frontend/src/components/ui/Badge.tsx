import { cn } from "@/lib/utils";

interface BadgeProps {
  children:  React.ReactNode;
  variant?:  "info" | "success" | "warning" | "default" | "orange";
  className?: string;
}

export function Badge({ children, variant = "default", className }: BadgeProps) {
  return (
    <span className={cn(
      "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium",
      variant === "info"    && "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300",
      variant === "success" && "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300",
      variant === "warning" && "bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300",
      variant === "orange"  && "bg-orange-100 dark:bg-orange-900/30 text-gitlab-orange dark:text-orange-400",
      variant === "default" && "bg-surface-100 dark:bg-surface-800 text-gray-600 dark:text-gray-400",
      className,
    )}>
      {children}
    </span>
  );
}