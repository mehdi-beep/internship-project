import { MenuItem, TextField, type TextFieldProps } from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { listClients } from "../services/clientService";

type ClientSelectProps = Omit<TextFieldProps, "select" | "children">;

export default function ClientSelect(props: ClientSelectProps) {
  const { data } = useQuery({
    queryKey: ["clients", "select-all"],
    queryFn: () => listClients({ page_size: 100, active_only: true }),
  });

  return (
    <TextField select label="Client" fullWidth {...props}>
      {(data?.items ?? []).map((client) => (
        <MenuItem key={client.id} value={client.id}>
          {client.client_name}
        </MenuItem>
      ))}
    </TextField>
  );
}
