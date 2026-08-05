import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { CHART_CATEGORICAL, CHART_INK } from "../styles/chartColors";
import type { ChartPoint } from "../types/dashboard";

interface SimpleBarChartProps {
  data: ChartPoint[];
  colorIndex?: number;
  emptyLabel?: string;
}

export default function SimpleBarChart({ data, colorIndex = 0, emptyLabel = "No data yet." }: SimpleBarChartProps) {
  if (data.length === 0) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", color: CHART_INK.muted, fontSize: 14 }}>
        {emptyLabel}
      </div>
    );
  }

  const color = CHART_CATEGORICAL.light[colorIndex % CHART_CATEGORICAL.light.length];

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid vertical={false} stroke={CHART_INK.gridline} />
        <XAxis
          dataKey="label"
          tick={{ fill: CHART_INK.muted, fontSize: 12 }}
          axisLine={{ stroke: CHART_INK.baseline }}
          tickLine={false}
        />
        <YAxis
          allowDecimals={false}
          tick={{ fill: CHART_INK.muted, fontSize: 12 }}
          axisLine={false}
          tickLine={false}
          width={32}
        />
        <Tooltip
          cursor={{ fill: "rgba(0,0,0,0.04)" }}
          contentStyle={{ borderRadius: 8, border: `1px solid ${CHART_INK.gridline}`, fontSize: 13 }}
        />
        <Bar dataKey="value" fill={color} radius={[4, 4, 0, 0]} maxBarSize={24} />
      </BarChart>
    </ResponsiveContainer>
  );
}
