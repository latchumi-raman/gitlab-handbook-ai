import { useQuery }  from "@tanstack/react-query";
import { fetchHealth } from "@/lib/api";
import { Tooltip }   from "./Tooltip";
import { cn }        from "@/lib/utils";

export function StatusIndicator() {
  const { data, isLoading, isError } = useQuery({
    queryKey:        ["health"],
    queryFn:         fetchHealth,
    refetchInterval: 30_000,   // poll every 30s
    retry:           1,
  });

  const status =
    isLoading ? "checking"
    : isError  ? "offline"
    : data?.status === "ok" ? "online"
    : "degraded";

  const label =
    status === "online"   ? `Online — ${data?.chunks_indexed?.toLocaleString()} chunks indexed`
    : status === "degraded" ? "Degraded — DB issue"
    : status === "offline"  ? "Backend offline"
    : "Checking…";

  return (
    <Tooltip text={label} position="bottom">
      <span className="flex items-center gap-1.5 cursor-default">
        <span className={cn(
          "w-2 h-2 rounded-full",
          status === "online"   && "bg-green-500 animate-pulse",
          status === "degraded" && "bg-amber-400",
          status === "offline"  && "bg-red-500",
          status === "checking" && "bg-gray-400",
        )} />
        <span className="text-xs text-gray-400 dark:text-gray-500 hidden sm:inline">
          {status === "online" ? "Online" : status}
        </span>
      </span>
    </Tooltip>
  );
}