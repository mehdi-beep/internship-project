import type { ReactNode } from "react";
import { Card, CardContent, Typography } from "@mui/material";

interface ChartCardProps {
  title: ReactNode;
  children: ReactNode;
  height?: number;
}

export default function ChartCard({ title, children, height = 280 }: ChartCardProps) {
  return (
    <Card variant="outlined" sx={{ height: "100%" }}>
      <CardContent>
        <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 2 }}>
          {title}
        </Typography>
        <div style={{ width: "100%", height }}>{children}</div>
      </CardContent>
    </Card>
  );
}
