import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  Box,
  Button,
  Chip,
  IconButton,
  MenuItem,
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
import DeleteForeverIcon from "@mui/icons-material/DeleteForever";
import { useForm } from "react-hook-form";
import DataTable, { type DataTableColumn } from "../../components/DataTable";
import SearchBar from "../../components/SearchBar";
import Modal from "../../components/Modal";
import ConfirmationDialog from "../../components/ConfirmationDialog";
import PermanentDeleteDialog from "../../components/PermanentDeleteDialog";
import { usePermanentDelete } from "../../hooks/usePermanentDelete";
import {
  activateClient,
  checkClientDeletable,
  createClient,
  deactivateClient,
  deleteClientPermanently,
  listClients,
  updateClient,
  type ClientInput,
} from "../../services/clientService";
import { listSiteCities } from "../../services/siteService";
import type { Client } from "../../types/referenceData";

export default function ClientsPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [search, setSearch] = useState("");
  const [cityFilter, setCityFilter] = useState("");
  const [showInactive, setShowInactive] = useState(false);
  const [editing, setEditing] = useState<Client | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [confirmTarget, setConfirmTarget] = useState<Client | null>(null);
  const [confirmErrorMessage, setConfirmErrorMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["clients", page, pageSize, search, cityFilter, showInactive],
    queryFn: () =>
      listClients({
        page,
        page_size: pageSize,
        search: search || undefined,
        city: cityFilter || undefined,
        active_only: !showInactive,
      }),
  });

  const { data: cities } = useQuery({
    queryKey: ["sites", "cities"],
    queryFn: listSiteCities,
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

  // Task 5 — permanent deletion, kept deliberately separate from the
  // deactivate flow above (different dialog, different icon, different colour).
  const permanentDelete = usePermanentDelete<Client>({
    invalidateKey: "clients",
    check: checkClientDeletable,
    remove: deleteClientPermanently,
    getName: (c) => c.client_name,
    getId: (c) => c.id,
  });

  const columns: DataTableColumn<Client>[] = [
    { key: "name", label: "Client Name", render: (c) => c.client_name },
    { key: "phone", label: "Phone", render: (c) => c.phone ?? "—" },
    { key: "email", label: "Email", render: (c) => c.email ?? "—" },
    {
      key: "status",
      label: "Status",
      // Task 5 — inactive state must be unmistakable, not plain text.
      render: (c) => (
        <Chip
          size="small"
          label={c.active ? "Active" : "Inactive"}
          color={c.active ? "success" : "default"}
          variant={c.active ? "filled" : "outlined"}
        />
      ),
    },
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
          <Tooltip title={c.active ? "Deactivate (keeps history)" : "Activate"}>
            <IconButton size="small" onClick={() => { setConfirmErrorMessage(null); setConfirmTarget(c); }}>
              {c.active ? <BlockIcon fontSize="small" /> : <CheckCircleIcon fontSize="small" />}
            </IconButton>
          </Tooltip>
          <Tooltip title="Delete permanently">
            <IconButton size="small" color="error" onClick={() => permanentDelete.start(c)}>
              <DeleteForeverIcon fontSize="small" />
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

      <Stack direction="row" spacing={2} sx={{ alignItems: "center", mb: 2, flexWrap: "wrap" }}>
        <SearchBar value={search} onChange={(v) => { setSearch(v); setPage(1); }} placeholder="Search clients..." />
        <TextField
          select
          size="small"
          label="City"
          value={cityFilter}
          onChange={(e) => { setCityFilter(e.target.value); setPage(1); }}
          sx={{ minWidth: 160 }}
        >
          <MenuItem value="">All</MenuItem>
          {(cities ?? []).map((city) => (
            <MenuItem key={city} value={city}>
              {city}
            </MenuItem>
          ))}
        </TextField>
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
            ? `Deactivate "${confirmTarget?.client_name}"? It will be hidden from active views and can no longer be selected, but the client and all its history are kept and it can be reactivated at any time.`
            : `Reactivate "${confirmTarget?.client_name}"?`
        }
        confirmLabel={confirmTarget?.active ? "Deactivate" : "Activate"}
        // Task 5 — deliberately "warning" (amber), not "error" (red): red is
        // reserved for permanent deletion so the two are never confusable.
        confirmColor={confirmTarget?.active ? "warning" : "primary"}
        loading={toggleActiveMutation.isPending}
        errorMessage={confirmErrorMessage}
        onConfirm={() => confirmTarget && toggleActiveMutation.mutate(confirmTarget)}
        onCancel={() => { setConfirmTarget(null); setConfirmErrorMessage(null); }}
      />

      <PermanentDeleteDialog
        open={permanentDelete.open}
        entityNoun="client"
        entityName={permanentDelete.name}
        check={permanentDelete.deletionCheck}
        checkLoading={permanentDelete.checkLoading}
        loading={permanentDelete.loading}
        errorMessage={permanentDelete.errorMessage}
        onConfirm={permanentDelete.confirm}
        onCancel={permanentDelete.cancel}
      />
    </Box>
  );
}
