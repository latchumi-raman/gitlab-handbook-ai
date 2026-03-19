import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import type { ConfidenceBucket } from "@/types";

interface ConfidenceGaugeProps {
  data: ConfidenceBucket[];
}

const BAR_COLORS = ["#ef4444", "#f97316", "#eab308", "#84cc16", "#22c55e"];

export function ConfidenceGauge({ data }: ConfidenceGaugeProps) {
  if (!data.length || data.every((d) => d.count === 0)) {
    return (
      <div className="h-40 flex items-center justify-center text-sm text-gray-400">
        No data yet
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={160}>
      <BarChart data={data} margin={{ top: 5, right: 10, bottom: 0, left: -20 }}>
        <CartesianGrid strokeDasharray="3 3" opacity={0.3} vertical={false} />
        <XAxis
          dataKey="range"
          tick={{ fontSize: 10, fill: "#9ca3af" }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 10, fill: "#9ca3af" }}
          axisLine={false}
          tickLine={false}
          allowDecimals={false}
        />
        <Tooltip
          contentStyle={{ fontSize: 12, borderRadius: 8 }}
          formatter={(v: number) => [v, "queries"]}
        />
        <Bar dataKey="count" name="Queries" radius={[4, 4, 0, 0]}>
          {data.map((_, i) => (
            <Cell key={i} fill={BAR_COLORS[i] ?? "#9ca3af"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}