import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts";

interface FeedbackChartProps {
  positive: number;
  negative: number;
}

export function FeedbackChart({ positive, negative }: FeedbackChartProps) {
  const total = positive + negative;

  if (total === 0) {
    return (
      <div className="h-40 flex items-center justify-center text-sm text-gray-400">
        No feedback yet
      </div>
    );
  }

  const data = [
    { name: "Helpful",     value: positive, color: "#22c55e" },
    { name: "Not helpful", value: negative, color: "#ef4444" },
  ];

  return (
    <ResponsiveContainer width="100%" height={160}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={45}
          outerRadius={68}
          paddingAngle={3}
          dataKey="value"
        >
          {data.map((entry) => (
            <Cell key={entry.name} fill={entry.color} stroke="transparent" />
          ))}
        </Pie>
        <Tooltip
          formatter={(value: number) => [`${value} (${Math.round(value / total * 100)}%)`, ""]}
          contentStyle={{ fontSize: 12, borderRadius: 8 }}
        />
        <Legend
          iconType="circle"
          iconSize={8}
          wrapperStyle={{ fontSize: 12 }}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}