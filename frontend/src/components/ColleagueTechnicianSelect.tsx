import { useEffect, useRef, useState } from "react";
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

const SEARCH_DEBOUNCE_MS = 300;

export default function ColleagueTechnicianSelect({
  value,
  onChange,
  excludeUserId,
  error,
  helperText,
  disabled,
}: ColleagueTechnicianSelectProps) {
  const [inputValue, setInputValue] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(inputValue), SEARCH_DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [inputValue]);

  // The technician list is never fetched whole — each distinct search term is
  // its own live backend query (real substring match on first/last
  // name/username, see user_repository.list_query), so a technician past any
  // fixed page cutoff is reachable by typing their name instead of silently
  // never appearing. GET /users/technicians has no page_size cap at all
  // (returns a plain list, not a Page), so this differs from
  // TravauxMultiSelect/ClientSelect only in not needing a page_size param.
  const { data: searchResults } = useQuery({
    queryKey: ["users", "technician-options", "search", debouncedSearch],
    queryFn: () => listTechnicianOptions({ search: debouncedSearch || undefined }),
  });

  const options = (searchResults ?? []).filter((t) => t.id !== excludeUserId);

  // Selected chips must stay visible even once a new search's results no
  // longer include them — accumulate every TechnicianOption this component
  // has ever seen (across all past searches) so a previously-picked
  // colleague still resolves to a name after the user searches for someone
  // else.
  const knownById = useRef(new Map<number, TechnicianOption>());
  for (const t of options) knownById.current.set(t.id, t);

  // A selected id can arrive already-known (e.g. loading a saved
  // intervention for edit) before any search has ever run, so it won't be in
  // knownById yet. GET /users/{id} (the obvious by-id resolve, mirroring
  // getTravail/getClient) is restricted to admin_supervisor/ceo — a
  // technician viewing/editing their own intervention would get a 403 — so
  // this resolves the specific unresolved ids via GET /users/technicians'
  // own ids filter instead, which every role on this picker can call. That
  // filter also bypasses the active_only restriction (see
  // user_service.list_technician_options), so a colleague deactivated after
  // being added still resolves to a name.
  const unresolvedIds = value.filter((id) => !knownById.current.has(id));
  const { data: resolvedById } = useQuery({
    queryKey: ["users", "technician-options", "by-ids", unresolvedIds],
    queryFn: () => listTechnicianOptions({ ids: unresolvedIds.join(",") }),
    enabled: unresolvedIds.length > 0,
  });
  for (const t of resolvedById ?? []) knownById.current.set(t.id, t);

  const selected = value.map((id) => knownById.current.get(id)).filter((t): t is TechnicianOption => t != null);

  return (
    <Autocomplete
      multiple
      disabled={disabled}
      options={options}
      value={selected}
      inputValue={inputValue}
      onInputChange={(_, next) => setInputValue(next)}
      onChange={(_, next) => onChange((next as TechnicianOption[]).map((t) => t.id))}
      getOptionLabel={(option) => `${option.first_name} ${option.last_name}`}
      isOptionEqualToValue={(option, val) => option.id === val.id}
      filterOptions={(x) => x}
      renderInput={(params) => (
        <TextField
          {...params}
          label="Colleague Technicians"
          placeholder="Type to search technicians..."
          error={error}
          helperText={helperText}
        />
      )}
    />
  );
}
