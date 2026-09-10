import { useEffect, useMemo, useRef, useState } from "react";
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
  // MUI's Autocomplete internally resets inputValue whenever its `value` prop
  // is a *new array reference*, even when the contents are identical — see
  // useAutocomplete's `value !== previousProps.value` check, which (with
  // clearOnBlur defaulting to true for a non-freeSolo Autocomplete) wipes out
  // whatever was just typed. `selected` used to be a fresh `.map().filter()`
  // array on every render, and every keystroke re-renders this component
  // (onInputChange -> setInputValue), so MUI saw a "changed" value and reset
  // the input after every single character — confirmed live: the field
  // visibly could not hold more than one typed character. useMemo keeps the
  // reference stable across renders that don't actually change the resolved
  // selection, so MUI's reference check correctly sees "unchanged."
  //
  // Dependency key: a signature of exactly which ids in `value` are
  // currently resolvable in knownById, computed fresh every render — NOT
  // `resolvedQueries`/`resolvedIdsKey` derived only from it (an earlier
  // version of this fix used that and it was still broken). knownById is
  // populated from TWO independent paths (the search-results loop above,
  // and this by-id resolve), and on a fresh page load either can be the one
  // that actually lands the id first depending on request timing —
  // confirmed live: reloading a saved intervention's edit page sometimes
  // resolved a travail via a plain search finishing first, which a key
  // derived only from the by-id resolve would never reflect, silently
  // leaving the chip missing even though knownById.current already had it.
  const resolutionKey = value.map((id) => (knownById.current.has(id) ? id : "?")).join(",");
  const selected = useMemo(
    () => value.map((id) => knownById.current.get(id)).filter((t): t is Travail => t != null),
    // eslint-disable-next-line react-hooks/exhaustive-deps -- knownById is a ref, mutated in-render just above rather than through a setter, so it can't be listed as a dependency; resolutionKey is what makes this re-run whenever the actual resolved-ness of `value`'s ids changes, regardless of which path resolved them.
    [value, resolutionKey],
  );

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
