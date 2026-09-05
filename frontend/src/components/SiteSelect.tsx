import { Button, MenuItem, Stack, TextField, type TextFieldProps } from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { listSitesForClient } from "../services/clientService";

type SiteSelectProps = Omit<TextFieldProps, "select" | "children"> & {
  clientId: number | null;
};

export default function SiteSelect({ clientId, ...props }: SiteSelectProps) {
  const { data, isError, refetch, isFetching } = useQuery({
    queryKey: ["clients", clientId, "sites-select"],
    queryFn: () => listSitesForClient(clientId!, { page_size: 100 }),
    enabled: !!clientId,
    // Above the global default of 1 (App.tsx) — this drives a required form
    // field a user is actively trying to fill in, so it's worth trying a
    // couple more times against a flaky connection before giving up and
    // showing the manual retry button below.
    retry: 3,
  });

  // A field-level equivalent of QueryStateGate's error-with-retry pattern —
  // that component swaps out its whole children tree, which doesn't fit a
  // single form field that needs to stay a TextField, so this is inline
  // instead rather than forcing that component into a shape it wasn't built
  // for. Distinguishing "genuinely failed" from "still loading" matters
  // here specifically because this surfaced live as a silent, indefinite
  // hang on a flaky connection with no visible feedback at all.
  if (isError) {
    return (
      <Stack direction="row" spacing={1} alignItems="center">
        <TextField select label="Site" fullWidth disabled {...props} value="" />
        <Button size="small" onClick={() => refetch()} disabled={isFetching}>
          {isFetching ? "Retrying…" : "Retry"}
        </Button>
      </Stack>
    );
  }

  return (
    <TextField select label="Site" fullWidth disabled={!clientId} {...props}>
      {(data?.items ?? []).map((site) => (
        <MenuItem key={site.id} value={site.id}>
          {site.site_name} ({site.city})
        </MenuItem>
      ))}
    </TextField>
  );
}
