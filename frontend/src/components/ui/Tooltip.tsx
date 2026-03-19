import { useState } from "react";
import { cn } from "@/lib/utils";

interface TooltipProps {
  text:     string;
  children: React.ReactNode;
  position?: "top" | "bottom";
}

export function Tooltip({ text, children, position = "top" }: TooltipProps) {
  const [show, setShow] = useState(false);

  return (
    <span
      className="relative inline-flex"
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
    >
      {children}
      {show && (
        <span className={cn(
          "absolute z-50 whitespace-nowrap rounded-md px-2 py-1 text-xs",
          "bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900",
          "pointer-events-none animate-fade-in",
          position === "top"    && "bottom-full left-1/2 -translate-x-1/2 mb-1.5",
          position === "bottom" && "top-full  left-1/2 -translate-x-1/2 mt-1.5",
        )}>
          {text}
        </span>
      )}
    </span>
  );
}