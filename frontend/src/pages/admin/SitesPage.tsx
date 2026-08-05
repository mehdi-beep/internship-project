import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  Box,
  Button,
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
import { Controller, useForm } from "react-hook-form";
import DataTable, { type DataTableColumn } from "../../components/DataTable";
import SearchBar from "../../components/SearchBar";
import Modal from "../../components/Modal";
import ConfirmationDialog from "../../components/ConfirmationDialog";
import ClientSelect from "../../components/ClientSelect";
import { listClients } from "../../services/clientService";
import {
  activateSite,
  createSite,
  deactivateSite,
  listSites,
  updateSite,
  type SiteInput,
} from "../../services/siteService";
import type { ClientSite } from "../../types/referenceData";

export default function SitesPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [search, setSearch] = useState("");
  const [clientFilter, setClientFilter] = useState<number | "">("");
  const [showInactive, setShowInactive] = useState(false);
  const [editing, setEditing] = useState<ClientSite | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [confirmTarget, setConfirmTarget] = useState<ClientSite | null>(null);
  const [confirmErrorMessage, setConfirmErrorMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["sites", page, pageSize, search, clientFilter, showInactive],
    queryFn: () =>
      listSites({
        page,
        page_size: pageSize,
        search: search || undefined,
        client_id: clientFilter || undefined,
        active_only: !showInactive,
      }),
  });

  const { data: clientsData } = useQuery({
    queryKey: ["clients", "lookup-all"],
    queryFn: () => listClients({ page_size: 100, active_only: true }),
  });
  const clientNameById = new Map((clientsData?.items ?? []).map((c) => [c.id, c.client_name]));

  const { register, handleSubmit, reset, control, formState: { errors } } = useForm<SiteInput>();

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["sites"] });

  const createMutation = useMutation({
    mutationFn: (input: SiteInput) => createSite(input),
    onSuccess: () => {
      invalidate();
      setModalOpen(false);
    },
    onError: () => setErrorMessage("Failed to save site."),
  });

  const updateMutation = useMutation({
    mutationFn: (input: SiteInput) => updateSite(editing!.id, input),
    onSuccess: () => {
      invalidate();
      setModalOpen(false);
    },
    onError: () => setErrorMessage("Failed to save site."),
  });

  const toggleActiveMutation = useMutation({
    mutationFn: (site: ClientSite) => (site.active ? deactivateSite(site.id) : activateSite(site.id)),
    onSuccess: () => {
      invalidate();
      setConfirmTarget(null);
      setConfirmErrorMessage(null);
    },
    onError: () => setConfirmErrorMessage("Failed to update the site. Please try again."),
  });

  const openCreate = () => {
    setEditing(null);
    reset({ client_id: 0, site_name: "", city: "", address: "" });
    setErrorMessage(null);
    setModalOpen(true);
  };

  const openEdit = (site: ClientSite) => {
    setEditing(site);
    reset({ client_id: site.client_id, site_name: site.site_name, city: site.city, address: site.address ?? "" });
    setErrorMessage(null);
    setModalOpen(true);
  };

  const onSubmit = (values: SiteInput) => {
    if (editing) {
      updateMutation.mutate(values);
    } else {
      createMutation.mutate(values);
    }
  };

  const columns: DataTableColumn<ClientSite>[] = [
    { key: "site_name", label: "Site Name", render: (s) => s.site_name },
    { key: "client", label: "Client", render: (s) => clientNameById.get(s.client_id) ?? `#${s.client_id}` },
    { key: "city", label: "City", render: (s) => s.city },
    { key: "address", label: "Address", render: (s) => s.address ?? "—" },
    { key: "status", label: "Status", render: (s) => (s.active ? "Active" : "Inactive") },
    {
      key: "actions",
      label: "Actions",
      align: "right",
      render: (s) => (
        <Stack direction="row" spacing={0.5} sx={{ justifyContent: "flex-end" }}>
          <Tooltip title="Edit">
            <IconButton size="small" onClick={() => openEdit(s)}>
              <EditIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title={s.active ? "Deactivate" : "Activate"}>
            <IconButton size="small" onClick={() => { setConfirmErrorMessage(null); setConfirmTarget(s); }}>
              {s.active ? <BlockIcon fontSize="small" /> : <CheckCircleIcon fontSize="small" />}
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
          Client Sites
        </Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={openCreate}>
          New Site
        </Button>
      </Stack>

      <Stack direction="row" spacing={2} sx={{ alignItems: "center", mb: 2, flexWrap: "wrap" }}>
        <SearchBar value={search} onChange={(v) => { setSearch(v); setPage(1); }} placeholder="Search sites..." />
        <TextField
          select
          size="small"
          label="Client"
          value={clientFilter}
          onChange={(e) => { setClientFilter(e.target.value ? Number(e.target.value) : ""); setPage(1); }}
          sx={{ minWidth: 200 }}
        >
          <MenuItem value="">All</MenuItem>
          {(clientsData?.items ?? []).map((c) => (
            <MenuItem key={c.id} value={c.id}>
              {c.client_name}
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
          Failed to load client sites. Please check your connection and try again.
        </Alert>
      )}

      <DataTable
        columns={columns}
        rows={data?.items ?? []}
        rowKey={(s) => s.id}
        loading={isLoading}
        emptyMessage="No client sites found."
        page={page}
        pageSize={pageSize}
        total={data?.total ?? 0}
        onPageChange={setPage}
        onPageSizeChange={(size) => { setPageSize(size); setPage(1); }}
      />

      <Modal open={modalOpen} title={editing ? "Edit Site" : "New Site"} onClose={() => setModalOpen(false)}>
        <Box component="form" onSubmit={handleSubmit(onSubmit)} noValidate sx={{ pt: 1 }}>
          <Stack spacing={2}>
            {errorMessage && <Alert severity="error">{errorMessage}</Alert>}
            <Controller
              name="client_id"
              control={control}
              rules={{ required: true, validate: (v) => v > 0 }}
              render={({ field }) => (
                <ClientSelect
                  {...field}
                  disabled={!!editing}
                  error={!!errors.client_id}
                  helperText={editing ? "Client cannot be changed after creation." : errors.client_id ? "Client is required" : undefined}
                />
              )}
            />
            <TextField
              label="Site Name"
              fullWidth
              error={!!errors.site_name}
              helperText={errors.site_name?.message}
              {...register("site_name", { required: "Site name is required" })}
            />
            <TextField
              label="City"
              fullWidth
              error={!!errors.city}
              helperText={errors.city?.message}
              {...register("city", { required: "City is required" })}
            />
            <TextField label="Address" fullWidth {...register("address")} />
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
        title={confirmTarget?.active ? "Deactivate Site" : "Activate Site"}
        message={
          confirmTarget?.active
            ? `Deactivate "${confirmTarget?.site_name}"? It will no longer be selectable for new interventions.`
            : `Reactivate "${confirmTarget?.site_name}"?`
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
