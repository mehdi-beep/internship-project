import { Grid } from "@mui/material";
import StatTile from "./StatTile";

export interface ProfileStatDef {
  label: string;
  value: string | number;
  accent?: string;
}

interface ProfileStatGridProps {
  stats: ProfileStatDef[];
}

export default function ProfileStatGrid({ stats }: ProfileStatGridProps) {
  return (
    <Grid container spacing={2}>
      {stats.map((stat) => (
        <Grid key={stat.label} size={{ xs: 6, sm: 4, md: 2 }}>
          <StatTile label={stat.label} value={stat.value} accent={stat.accent} />
        </Grid>
      ))}
    </Grid>
  );
}
