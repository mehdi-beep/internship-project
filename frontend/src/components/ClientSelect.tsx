import { useEffect, useRef, useState } from "react";
import { Autocomplete, TextField } from "@mui/material";
import { useQueries, useQuery } from "@tanstack/react-query";
import { getClient, listClients } from "../services/clientService";
import type { Client } from "../types/referenceData";

// A plain TextField-select/MenuItem list (the previous shape of this
// component) has no way to filter-as-you-type at all — Autocomplete is the
// only one of the two that can support search-as-you-type, so this is a full
// conversion, not just a fetch-strategy change underneath the same markup.
interface ClientSelectProps {
  /** react-hook-form's Controller passes the field's current value/onChange
   * here via {...field} — kept as plain number (id), 0 meaning "none
   * selected", matching every existing call site's default value exactly. */
  value?: number;
  onChange?: (id: number) => void;
  disabled?: boolean;
  error?: boolean;
  helperText?: string;
}

const SEARCH_DEBOUNCE_MS = 300;

export default function ClientSelect({ value, onChange, disabled, error, helperText }: ClientSelectProps) {
  const [inputValue, setInputValue] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(inputValue), SEARCH_DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [inputValue]);

  // The catalog is never fetched whole — each distinct search term is its
  // own live backend query (real substring match on client_name, see
  // client_repository.list_query), so a client past any fixed page cutoff is
  // reachable by typing its name instead of silently never appearing.
  const { data } = useQuery({
    queryKey: ["clients", "search", debouncedSearch],
    queryFn: () => listClients({ page_size: 50, active_only: true, search: debouncedSearch || undefined }),
  });

  const searchResults = data?.items ?? [];

  // The selected client must stay resolvable even once a new search's
  // results no longer include it — accumulate every Client this component
  // has ever seen (across all past searches) so it keeps showing a name
  // instead of reverting to blank after the user searches for something else.
  const knownById = useRef(new Map<number, Client>());
  for (const c of searchResults) knownById.current.set(c.id, c);

  // The current value can arrive already-known (e.g. loading a saved
  // contract/site/planning entry for edit) before any search has ever run —
  // fetch it by id rather than requiring a matching search first.
  const needsFetch = !!value && !knownById.current.has(value);
  const [resolvedQuery] = useQueries({
    queries: [
      {
        queryKey: ["clients", "by-id", value],
        queryFn: () => getClient(value!),
        enabled: needsFetch,
      },
    ],
  });
  if (resolvedQuery.data) knownById.current.set(resolvedQuery.data.id, resolvedQuery.data);

  const options = searchResults;
  const selectedClient = value ? (knownById.current.get(value) ?? null) : null;

  return (
    <Autocomplete
      disabled={disabled}
      options={options}
      value={selectedClient}
      inputValue={inputValue}
      onInputChange={(_, next) => setInputValue(next)}
      onChange={(_, next) => onChange?.((next as Client | null)?.id ?? 0)}
      getOptionLabel={(option) => option.client_name}
      isOptionEqualToValue={(option, val) => option.id === val.id}
      filterOptions={(x) => x}
      renderInput={(params) => (
        <TextField
          {...params}
          label="Client"
          fullWidth
          placeholder="Type to search clients..."
          error={error}
          helperText={helperText}
        />
      )}
    />
  );
}
