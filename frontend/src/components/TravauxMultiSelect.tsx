import { useEffect, useRef, useState } from "react";
import { Autocomplete, TextField } from "@mui/material";
import { useQueries, useQuery } from "@tanstack/react-query";
import { getTravail, listTravaux } from "../services/travailService";
import type { Travail } from "../types/referenceData";

interface TravauxMultiSelectProps {
  value: number[];
  onChange: (ids: number[]) => void;
  error?: boolean;
  helperText?: string;
  disabled?: boolean;
}

// No debounce utility exists elsewhere in the codebase (and no debounce
// library in package.json) — a plain setTimeout is enough for this.
const SEARCH_DEBOUNCE_MS = 300;

export default function TravauxMultiSelect({
  value,
  onChange,
  error,
  helperText,
  disabled,
}: TravauxMultiSelectProps) {
  // Ch.41 / Rule: free typing is never allowed — options come only from the
  // catalog. onInputChange below only ever updates what's searched for, never
  // what can be committed as a value — selecting still requires picking an
  // option from the list via onChange, exactly as before.
  const [inputValue, setInputValue] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(inputValue), SEARCH_DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [inputValue]);

  // The catalog is never fetched whole — each distinct search term is its
  // own live backend query (real substring match on code/name, see
  // travail_repository.list_query), so a travail past any fixed page cutoff
  // is reachable by typing its name instead of silently never appearing.
  const { data } = useQuery({
    queryKey: ["travaux", "search", debouncedSearch],
    queryFn: () => listTravaux({ page_size: 50, active_only: true, search: debouncedSearch || undefined }),
  });

  const searchResults = data?.items ?? [];

  // Selected chips must stay visible even once a new search's results no
  // longer include them — accumulate every Travail object this component has
  // ever seen (across all past searches) so a previously-picked item still
  // resolves to a name/code after the user searches for something else.
  const knownById = useRef(new Map<number, Travail>());
  for (const t of searchResults) knownById.current.set(t.id, t);

  // A selected id can arrive already-known (e.g. loading a saved
  // intervention for edit) before any search has ever run, so it won't be in
  // knownById yet — fetch those specific ids by id rather than requiring a
  // matching search first, exactly like InterventionDetailsPage/
  // InterventionReviewViewer resolve an already-known id.
  const unresolvedIds = value.filter((id) => !knownById.current.has(id));
  const resolvedQueries = useQueries({
    queries: unresolvedIds.map((id) => ({
      queryKey: ["travaux", "by-id", id],
      queryFn: () => getTravail(id),
    })),
  });
  for (const q of resolvedQueries) {
    if (q.data) knownById.current.set(q.data.id, q.data);
  }

  const options = searchResults;
  const selected = value.map((id) => knownById.current.get(id)).filter((t): t is Travail => t != null);

  return (
    <Autocomplete
      multiple
      disabled={disabled}
      options={options}
      value={selected}
      inputValue={inputValue}
      onInputChange={(_, next) => setInputValue(next)}
      onChange={(_, next) => onChange((next as Travail[]).map((t) => t.id))}
      getOptionLabel={(option) => `${option.travail_code} — ${option.travail_name}`}
      isOptionEqualToValue={(option, val) => option.id === val.id}
      filterOptions={(x) => x}
      renderInput={(params) => (
        <TextField
          {...params}
          label="Travaux Effectués"
          placeholder="Type to search tasks..."
          error={error}
          helperText={helperText}
        />
      )}
    />
  );
}
