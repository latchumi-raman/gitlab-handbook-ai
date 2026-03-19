import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

interface StatsCardProps {
  label:     string;
  value:     string | number;
  sub?:      string;
  icon?:     ReactNode;
  accent?:   "orange" | "green" | "purple" | "red" | "blue";
  className?: string;
}

const ACCENT_COLORS = {
  orange: "text-gitlab-orange  bg-orange-50  dark:bg-orange-900/20",
  green:  "text-green-600      bg-green-50   dark:bg-green-900/20",
  purple: "text-gitlab-purple  bg-purple-50  dark:bg-purple-900/20",
  red:    "text-red-500        bg-red-50     dark:bg-red-900/20",
  blue:   "text-blue-600       bg-blue-50    dark:bg-blue-900/20",
};

export function StatsCard({ label, value, sub, icon, accent = "orange", className }: StatsCardProps) {
  return (
    <div className={cn(
      "bg-white dark:bg-surface-900 rounded-2xl border border-surface-200 dark:border-surface-800 p-5",
      className,
    )}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
            {label}
          </p>
          <p className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
            {value}
          </p>
          {sub && (
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">{sub}</p>
          )}
        </div>
        {icon && (
          <div className={cn("p-2.5 rounded-xl", ACCENT_COLORS[accent])}>
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}