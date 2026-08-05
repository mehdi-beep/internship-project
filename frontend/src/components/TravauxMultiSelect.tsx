import { Autocomplete, TextField } from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { listTravaux } from "../services/travailService";
import type { Travail } from "../types/referenceData";

interface TravauxMultiSelectProps {
  value: number[];
  onChange: (ids: number[]) => void;
  error?: boolean;
  helperText?: string;
  disabled?: boolean;
}

export default function TravauxMultiSelect({
  value,
  onChange,
  error,
  helperText,
  disabled,
}: TravauxMultiSelectProps) {
  // Ch.41 / Rule: free typing is never allowed — options come only from the catalog.
  const { data } = useQuery({
    queryKey: ["travaux", "catalog-all"],
    queryFn: () => listTravaux({ page_size: 100, active_only: true }),
  });

  const options = data?.items ?? [];
  const selected = options.filter((t) => value.includes(t.id));

  return (
    <Autocomplete
      multiple
      disabled={disabled}
      options={options}
      value={selected}
      onChange={(_, next) => onChange((next as Travail[]).map((t) => t.id))}
      getOptionLabel={(option) => `${option.travail_code} — ${option.travail_name}`}
      isOptionEqualToValue={(option, val) => option.id === val.id}
      renderInput={(params) => (
        <TextField
          {...params}
          label="Travaux Effectués"
          placeholder="Select tasks..."
          error={error}
          helperText={helperText}
        />
      )}
    />
  );
}
