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
  activateTravail,
  createTravail,
  deactivateTravail,
  listTravaux,
  updateTravail,
  type TravailInput,
} from "../../services/travailService";
import type { Travail } from "../../types/referenceData";

export default function TravauxPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [search, setSearch] = useState("");
  const [showInactive, setShowInactive] = useState(false);
  const [editing, setEditing] = useState<Travail | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [confirmTarget, setConfirmTarget] = useState<Travail | null>(null);
  const [confirmErrorMessage, setConfirmErrorMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["travaux", page, pageSize, search, showInactive],
    queryFn: () => listTravaux({ page, page_size: pageSize, search: search || undefined, active_only: !showInactive }),
  });

  const { register, handleSubmit, reset, formState: { errors } } = useForm<TravailInput>();

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["travaux"] });

  const createMutation = useMutation({
    mutationFn: (input: TravailInput) => createTravail(input),
    onSuccess: () => {
      invalidate();
      setModalOpen(false);
    },
    onError: (err: unknown) => {
      const message = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setErrorMessage(message ?? "Failed to save travail.");
    },
  });

  const updateMutation = useMutation({
    mutationFn: (input: TravailInput) => updateTravail(editing!.id, input),
    onSuccess: () => {
      invalidate();
      setModalOpen(false);
    },
    onError: (err: unknown) => {
      const message = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setErrorMessage(message ?? "Failed to save travail.");
    },
  });

  const toggleActiveMutation = useMutation({
    mutationFn: (travail: Travail) => (travail.active ? deactivateTravail(travail.id) : activateTravail(travail.id)),
    onSuccess: () => {
      invalidate();
      setConfirmTarget(null);
      setConfirmErrorMessage(null);
    },
    onError: () => setConfirmErrorMessage("Failed to update the travail. Please try again."),
  });

  const openCreate = () => {
    setEditing(null);
    reset({ travail_code: "", travail_name: "", category: "" });
    setErrorMessage(null);
    setModalOpen(true);
  };

  const openEdit = (travail: Travail) => {
    setEditing(travail);
    reset({ travail_code: travail.travail_code, travail_name: travail.travail_name, category: travail.category ?? "" });
    setErrorMessage(null);
    setModalOpen(true);
  };

  const onSubmit = (values: TravailInput) => {
    if (editing) {
      updateMutation.mutate(values);
    } else {
      createMutation.mutate(values);
    }
  };

  const columns: DataTableColumn<Travail>[] = [
    { key: "code", label: "Code", render: (t) => t.travail_code },
    { key: "name", label: "Task Name", render: (t) => t.travail_name },
    { key: "category", label: "Category", render: (t) => t.category ?? "—" },
    { key: "status", label: "Status", render: (t) => (t.active ? "Active" : "Inactive") },
    {
      key: "actions",
      label: "Actions",
      align: "right",
      render: (t) => (
        <Stack direction="row" spacing={0.5} sx={{ justifyContent: "flex-end" }}>
          <Tooltip title="Edit">
            <IconButton size="small" onClick={() => openEdit(t)}>
              <EditIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title={t.active ? "Deactivate" : "Activate"}>
            <IconButton size="small" onClick={() => { setConfirmErrorMessage(null); setConfirmTarget(t); }}>
              {t.active ? <BlockIcon fontSize="small" /> : <CheckCircleIcon fontSize="small" />}
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
          Travaux Catalog
        </Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={openCreate}>
          New Travail
        </Button>
      </Stack>

      <Stack direction="row" spacing={2} sx={{ alignItems: "center", mb: 2 }}>
        <SearchBar value={search} onChange={(v) => { setSearch(v); setPage(1); }} placeholder="Search by code or name..." />
        <Stack direction="row" spacing={0.5} sx={{ alignItems: "center" }}>
          <Switch checked={showInactive} onChange={(e) => { setShowInactive(e.target.checked); setPage(1); }} size="small" />
          <Typography variant="body2">Show inactive</Typography>
        </Stack>
      </Stack>

      {isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load the travaux catalog. Please check your connection and try again.
        </Alert>
      )}

      <DataTable
        columns={columns}
        rows={data?.items ?? []}
        rowKey={(t) => t.id}
        loading={isLoading}
        emptyMessage="No travaux found."
        page={page}
        pageSize={pageSize}
        total={data?.total ?? 0}
        onPageChange={setPage}
        onPageSizeChange={(size) => { setPageSize(size); setPage(1); }}
      />

      <Modal open={modalOpen} title={editing ? "Edit Travail" : "New Travail"} onClose={() => setModalOpen(false)}>
        <Box component="form" onSubmit={handleSubmit(onSubmit)} noValidate sx={{ pt: 1 }}>
          <Stack spacing={2}>
            {errorMessage && <Alert severity="error">{errorMessage}</Alert>}
            <TextField
              label="Task Code"
              fullWidth
              autoFocus
              error={!!errors.travail_code}
              helperText={errors.travail_code?.message}
              {...register("travail_code", { required: "Task code is required" })}
            />
            <TextField
              label="Task Name"
              fullWidth
              error={!!errors.travail_name}
              helperText={errors.travail_name?.message}
              {...register("travail_name", { required: "Task name is required" })}
            />
            <TextField label="Category" fullWidth {...register("category")} />
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
        title={confirmTarget?.active ? "Deactivate Travail" : "Activate Travail"}
        message={
          confirmTarget?.active
            ? `Deactivate "${confirmTarget?.travail_name}"? It will no longer be selectable for new interventions.`
            : `Reactivate "${confirmTarget?.travail_name}"?`
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
