import { ToggleButton, ToggleButtonGroup, Tooltip } from "@mui/material";
import BarChartIcon from "@mui/icons-material/BarChartOutlined";
import ShowChartIcon from "@mui/icons-material/ShowChartOutlined";

export type ChartType = "bar" | "line";

interface ChartTypeToggleProps {
  value: ChartType;
  onChange: (value: ChartType) => void;
}

export default function ChartTypeToggle({ value, onChange }: ChartTypeToggleProps) {
  return (
    <ToggleButtonGroup
      size="small"
      exclusive
      value={value}
      onChange={(_, next: ChartType | null) => next && onChange(next)}
    >
      <Tooltip title="Bar chart">
        <ToggleButton value="bar" aria-label="Bar chart">
          <BarChartIcon fontSize="small" />
        </ToggleButton>
      </Tooltip>
      <Tooltip title="Line chart">
        <ToggleButton value="line" aria-label="Line chart">
          <ShowChartIcon fontSize="small" />
        </ToggleButton>
      </Tooltip>
    </ToggleButtonGroup>
  );
}
