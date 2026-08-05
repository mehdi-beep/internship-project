import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  Box,
  Button,
  IconButton,
  Stack,
  Switch,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import EditIcon from "@mui/icons-material/EditOutlined";
import BlockIcon from "@mui/icons-material/BlockOutlined";
import CheckCircleIcon from "@mui/icons-material/CheckCircleOutlined";
import { useForm } from "react-hook-form";
import DataTable, { type DataTableColumn } from "../../components/DataTable";
import SearchBar from "../../components/SearchBar";
import Modal from "../../components/Modal";
import ConfirmationDialog from "../../components/ConfirmationDialog";
import {
  activateClient,
  createClient,
  deactivateClient,
  listClients,
  updateClient,
  type ClientInput,
} from "../../services/clientService";
import type { Client } from "../../types/referenceData";

export default function ClientsPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [search, setSearch] = useState("");
  const [showInactive, setShowInactive] = useState(false);
  const [editing, setEditing] = useState<Client | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [confirmTarget, setConfirmTarget] = useState<Client | null>(null);
  const [confirmErrorMessage, setConfirmErrorMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["clients", page, pageSize, search, showInactive],
    queryFn: () => listClients({ page, page_size: pageSize, search: search || undefined, active_only: !showInactive }),
  });

  const { register, handleSubmit, reset, formState: { errors } } = useForm<ClientInput>();

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["clients"] });

  const createMutation = useMutation({
    mutationFn: (input: ClientInput) => createClient(input),
    onSuccess: () => {
      invalidate();
      setModalOpen(false);
    },
    onError: () => setErrorMessage("Failed to save client."),
  });

  const updateMutation = useMutation({
    mutationFn: (input: ClientInput) => updateClient(editing!.id, input),
    onSuccess: () => {
      invalidate();
      setModalOpen(false);
    },
    onError: () => setErrorMessage("Failed to save client."),
  });

  const toggleActiveMutation = useMutation({
    mutationFn: (client: Client) => (client.active ? deactivateClient(client.id) : activateClient(client.id)),
    onSuccess: () => {
      invalidate();
      setConfirmTarget(null);
      setConfirmErrorMessage(null);
    },
    onError: () => setConfirmErrorMessage("Failed to update the client. Please try again."),
  });

  const openCreate = () => {
    setEditing(null);
    reset({ client_name: "", phone: "", email: "" });
    setErrorMessage(null);
    setModalOpen(true);
  };

  const openEdit = (client: Client) => {
    setEditing(client);
    reset({ client_name: client.client_name, phone: client.phone ?? "", email: client.email ?? "" });
    setErrorMessage(null);
    setModalOpen(true);
  };

  const onSubmit = (values: ClientInput) => {
    if (editing) {
      updateMutation.mutate(values);
    } else {
      createMutation.mutate(values);
    }
  };

  const columns: DataTableColumn<Client>[] = [
    { key: "name", label: "Client Name", render: (c) => c.client_name },
    { key: "phone", label: "Phone", render: (c) => c.phone ?? "—" },
    { key: "email", label: "Email", render: (c) => c.email ?? "—" },
    { key: "status", label: "Status", render: (c) => (c.active ? "Active" : "Inactive") },
    {
      key: "actions",
      label: "Actions",
      align: "right",
      render: (c) => (
        <Stack direction="row" spacing={0.5} sx={{ justifyContent: "flex-end" }}>
          <Tooltip title="Edit">
            <IconButton size="small" onClick={() => openEdit(c)}>
              <EditIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title={c.active ? "Deactivate" : "Activate"}>
            <IconButton size="small" onClick={() => { setConfirmErrorMessage(null); setConfirmTarget(c); }}>
              {c.active ? <BlockIcon fontSize="small" /> : <CheckCircleIcon fontSize="small" />}
            </IconButton>
          </Tooltip>
        </Stack>
      ),
    },
  ];

  return (
    <Box>
      <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center", mb: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>
          Clients
        </Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={openCreate}>
          New Client
        </Button>
      </Stack>

      <Stack direction="row" spacing={2} sx={{ alignItems: "center", mb: 2 }}>
        <SearchBar value={search} onChange={(v) => { setSearch(v); setPage(1); }} placeholder="Search clients..." />
        <Stack direction="row" spacing={0.5} sx={{ alignItems: "center" }}>
          <Switch checked={showInactive} onChange={(e) => { setShowInactive(e.target.checked); setPage(1); }} size="small" />
          <Typography variant="body2">Show inactive</Typography>
        </Stack>
      </Stack>

      {isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load clients. Please check your connection and try again.
        </Alert>
      )}

      <DataTable
        columns={columns}
        rows={data?.items ?? []}
        rowKey={(c) => c.id}
        loading={isLoading}
        emptyMessage="No clients found."
        page={page}
        pageSize={pageSize}
        total={data?.total ?? 0}
        onPageChange={setPage}
        onPageSizeChange={(size) => { setPageSize(size); setPage(1); }}
      />

      <Modal open={modalOpen} title={editing ? "Edit Client" : "New Client"} onClose={() => setModalOpen(false)}>
        <Box component="form" onSubmit={handleSubmit(onSubmit)} noValidate sx={{ pt: 1 }}>
          <Stack spacing={2}>
            {errorMessage && <Alert severity="error">{errorMessage}</Alert>}
            <TextField
              label="Client Name"
              fullWidth
              autoFocus
              error={!!errors.client_name}
              helperText={errors.client_name?.message}
              {...register("client_name", { required: "Client name is required" })}
            />
            <TextField label="Phone" fullWidth {...register("phone")} />
            <TextField label="Email" fullWidth type="email" {...register("email")} />
            <Stack direction="row" spacing={1} sx={{ justifyContent: "flex-end" }}>
              <Button onClick={() => setModalOpen(false)}>Cancel</Button>
              <Button type="submit" variant="contained" disabled={createMutation.isPending || updateMutation.isPending}>
                Save
              </Button>
            </Stack>
          </Stack>
        </Box>
      </Modal>

      <ConfirmationDialog
        open={!!confirmTarget}
        title={confirmTarget?.active ? "Deactivate Client" : "Activate Client"}
        message={
          confirmTarget?.active
            ? `Deactivate "${confirmTarget?.client_name}"? It will no longer appear as a selectable client.`
            : `Reactivate "${confirmTarget?.client_name}"?`
        }
        confirmLabel={confirmTarget?.active ? "Deactivate" : "Activate"}
        confirmColor={confirmTarget?.active ? "error" : "primary"}
        loading={toggleActiveMutation.isPending}
        errorMessage={confirmErrorMessage}
        onConfirm={() => confirmTarget && toggleActiveMutation.mutate(confirmTarget)}
        onCancel={() => { setConfirmTarget(null); setConfirmErrorMessage(null); }}
      />
    </Box>
  );
}
