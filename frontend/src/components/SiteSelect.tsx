import { MenuItem, TextField, type TextFieldProps } from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { listSitesForClient } from "../services/clientService";

type SiteSelectProps = Omit<TextFieldProps, "select" | "children"> & {
  clientId: number | null;
};

export default function SiteSelect({ clientId, ...props }: SiteSelectProps) {
  const { data } = useQuery({
    queryKey: ["clients", clientId, "sites-select"],
    queryFn: () => listSitesForClient(clientId!, { page_size: 100 }),
    enabled: !!clientId,
  });

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
