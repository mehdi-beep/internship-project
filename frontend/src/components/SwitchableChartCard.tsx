import { useState } from "react";
import { Card, CardContent, Stack, Typography } from "@mui/material";
import ChartTypeToggle, { type ChartType } from "./ChartTypeToggle";
import SimpleBarChart from "./SimpleBarChart";
import SimpleLineChart from "./SimpleLineChart";
import type { ChartPoint } from "../types/dashboard";

interface SwitchableChartCardProps {
  title: string;
  data: ChartPoint[];
  colorIndex?: number;
  emptyLabel?: string;
  height?: number;
  /** Which chart type this card opens in. Every dashboard chart defaulted to
   * one fixed type before this control existed (bar for most, line for
   * "Points Earned") — kept as the default here so nothing visually changes
   * until a user actually switches it. */
  defaultType?: ChartType;
}

export default function SwitchableChartCard({
  title,
  data,
  colorIndex = 0,
  emptyLabel,
  height = 280,
  defaultType = "bar",
}: SwitchableChartCardProps) {
  const [chartType, setChartType] = useState<ChartType>(defaultType);

  return (
    <Card variant="outlined" sx={{ height: "100%" }}>
      <CardContent>
        <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center", mb: 2, flexWrap: "wrap", gap: 1 }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
            {title}
          </Typography>
          <ChartTypeToggle value={chartType} onChange={setChartType} />
        </Stack>
        <div style={{ width: "100%", height }}>
          {chartType === "line" ? (
            <SimpleLineChart data={data} colorIndex={colorIndex} emptyLabel={emptyLabel} />
          ) : (
            <SimpleBarChart data={data} colorIndex={colorIndex} emptyLabel={emptyLabel} />
          )}
        </div>
      </CardContent>
    </Card>
  );
}
