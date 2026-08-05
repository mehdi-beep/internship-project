import { Card, CardContent, Typography } from "@mui/material";

interface StatTileProps {
  label: string;
  value: string | number;
  accent?: string;
}

export default function StatTile({ label, value, accent }: StatTileProps) {
  return (
    <Card variant="outlined" sx={{ height: "100%" }}>
      <CardContent>
        <Typography variant="body2" color="text.secondary">
          {label}
        </Typography>
        <Typography variant="h4" sx={{ fontWeight: 600, mt: 0.5, color: accent }}>
          {value}
        </Typography>
      </CardContent>
    </Card>
  );
}
