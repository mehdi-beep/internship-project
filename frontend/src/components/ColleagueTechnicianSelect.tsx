import { Autocomplete, TextField } from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { listTechnicianOptions } from "../services/userService";
import type { TechnicianOption } from "../types/referenceData";

interface ColleagueTechnicianSelectProps {
  value: number[];
  onChange: (ids: number[]) => void;
  excludeUserId?: number;
  error?: boolean;
  helperText?: string;
  disabled?: boolean;
}

export default function ColleagueTechnicianSelect({
  value,
  onChange,
  excludeUserId,
  error,
  helperText,
  disabled,
}: ColleagueTechnicianSelectProps) {
  const { data } = useQuery({
    queryKey: ["users", "technician-options"],
    queryFn: listTechnicianOptions,
  });

  const options = (data ?? []).filter((t) => t.id !== excludeUserId);
  const selected = options.filter((t) => value.includes(t.id));

  return (
    <Autocomplete
      multiple
      disabled={disabled}
      options={options}
      value={selected}
      onChange={(_, next) => onChange((next as TechnicianOption[]).map((t) => t.id))}
      getOptionLabel={(option) => `${option.first_name} ${option.last_name}`}
      isOptionEqualToValue={(option, val) => option.id === val.id}
      renderInput={(params) => (
        <TextField
          {...params}
          label="Colleague Technicians"
          placeholder="Add technicians who assisted..."
          error={error}
          helperText={helperText}
        />
      )}
    />
  );
}
