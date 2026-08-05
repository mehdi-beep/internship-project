import { Box, MenuItem, TextField } from "@mui/material";
import type { ReactNode } from "react";

export interface FilterOption {
  value: string;
  label: string;
}

export interface FilterFieldConfig {
  name: string;
  label: string;
  value: string;
  options: FilterOption[];
  onChange: (value: string) => void;
}

interface FilterPanelProps {
  filters: FilterFieldConfig[];
  extra?: ReactNode;
}

export default function FilterPanel({ filters, extra }: FilterPanelProps) {
  return (
    <Box sx={{ display: "flex", gap: 1.5, flexWrap: "wrap", alignItems: "center" }}>
      {filters.map((filter) => (
        <TextField
          key={filter.name}
          select
          size="small"
          label={filter.label}
          value={filter.value}
          onChange={(e) => filter.onChange(e.target.value)}
          sx={{ minWidth: 160 }}
        >
          <MenuItem value="">All</MenuItem>
          {filter.options.map((option) => (
            <MenuItem key={option.value} value={option.value}>
              {option.label}
            </MenuItem>
          ))}
        </TextField>
      ))}
      {extra}
    </Box>
  );
}
