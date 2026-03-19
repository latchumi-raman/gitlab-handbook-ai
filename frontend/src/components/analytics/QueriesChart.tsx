import {
  XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Area, AreaChart,
} from "recharts";
import type { QueryPerDay } from "@/types";
import { format, parseISO } from "date-fns";

interface QueriesChartProps {
  data: QueryPerDay[];
}

export function QueriesChart({ data }: QueriesChartProps) {
  if (!data.length) {
    return (
      <div className="h-48 flex items-center justify-center text-sm text-gray-400">
        No query data yet — start chatting!
      </div>
    );
  }

  const formatted = data.map((d) => ({
    ...d,
    label: format(parseISO(d.day), "MMM d"),
  }));

  return (
    <ResponsiveContainer width="100%" height={200}>
      <AreaChart data={formatted} margin={{ top: 5, right: 10, bottom: 0, left: -20 }}>
        <defs>
          <linearGradient id="queryGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%"  stopColor="#FC6D26" stopOpacity={0.25} />
            <stop offset="95%" stopColor="#FC6D26" stopOpacity={0.02} />
          </linearGradient>
          <linearGradient id="blockedGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%"  stopColor="#E24B4A" stopOpacity={0.2} />
            <stop offset="95%" stopColor="#E24B4A" stopOpacity={0.0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" opacity={0.3} />
        <XAxis
          dataKey="label"
          tick={{ fontSize: 11, fill: "#9ca3af" }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 11, fill: "#9ca3af" }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          contentStyle={{
            background:   "var(--tw-bg, #fff)",
            border:       "1px solid #e5e7eb",
            borderRadius: "10px",
            fontSize:     "12px",
          }}
          labelStyle={{ fontWeight: 600, marginBottom: 4 }}
        />
        <Area
          type="monotone"
          dataKey="total_queries"
          name="Total queries"
          stroke="#FC6D26"
          strokeWidth={2}
          fill="url(#queryGrad)"
          dot={false}
          activeDot={{ r: 4, strokeWidth: 0, fill: "#FC6D26" }}
        />
        <Area
          type="monotone"
          dataKey="blocked_queries"
          name="Blocked"
          stroke="#E24B4A"
          strokeWidth={1.5}
          fill="url(#blockedGrad)"
          dot={false}
          activeDot={{ r: 3, strokeWidth: 0, fill: "#E24B4A" }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}