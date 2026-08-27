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
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import ArchiveIcon from "@mui/icons-material/ArchiveOutlined";
import DeleteForeverIcon from "@mui/icons-material/DeleteForever";
import { Controller, useForm } from "react-hook-form";
import DataTable, { type DataTableColumn } from "../../components/DataTable";
import SearchBar from "../../components/SearchBar";
import Modal from "../../components/Modal";
import ConfirmationDialog from "../../components/ConfirmationDialog";
import PermanentDeleteDialog from "../../components/PermanentDeleteDialog";
import { usePermanentDelete } from "../../hooks/usePermanentDelete";
import ClientSelect from "../../components/ClientSelect";
import { listClients } from "../../services/clientService";
import { checkProjectDeletable, deleteProjectPermanently, archiveProject, createProject, listProjects, type ProjectInput } from "../../services/projectService";
import type { Project, ProjectStatus } from "../../types/referenceData";

export default function ProjectsPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [search, setSearch] = useState("");
  const [clientFilter, setClientFilter] = useState<number | "">("");
  const [statusFilter, setStatusFilter] = useState<ProjectStatus | "">("");
  const [startDateFrom, setStartDateFrom] = useState("");
  const [startDateTo, setStartDateTo] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [confirmTarget, setConfirmTarget] = useState<Project | null>(null);
  const [confirmErrorMessage, setConfirmErrorMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["projects", page, pageSize, search, clientFilter, statusFilter, startDateFrom, startDateTo],
    queryFn: () =>
      listProjects({
        page,
        page_size: pageSize,
        search: search || undefined,
        client_id: clientFilter || undefined,
        status: statusFilter || undefined,
        start_date_from: startDateFrom || undefined,
        start_date_to: startDateTo || undefined,
      }),
  });

  const { data: clientsData } = useQuery({
    queryKey: ["clients", "lookup-all"],
    queryFn: () => listClients({ page_size: 100, active_only: true }),
  });
  const clientNameById = new Map((clientsData?.items ?? []).map((c) => [c.id, c.client_name]));

  const { register, handleSubmit, reset, control, formState: { errors } } = useForm<ProjectInput>();

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["projects"] });

  const createMutation = useMutation({
    mutationFn: (input: ProjectInput) => createProject(input),
    onSuccess: () => {
      invalidate();
      setModalOpen(false);
    },
    onError: () => setErrorMessage("Failed to save project."),
  });

  const archiveMutation = useMutation({
    mutationFn: (project: Project) => archiveProject(project.id),
    onSuccess: () => {
      invalidate();
      setConfirmTarget(null);
      setConfirmErrorMessage(null);
    },
    onError: () => setConfirmErrorMessage("Failed to archive the project. Please try again."),
  });

  const openCreate = () => {
    reset({ client_id: 0, project_name: "", start_date: "", end_date: "" });
    setErrorMessage(null);
    setModalOpen(true);
  };

  // Task 5 — permanent deletion, deliberately separate from the
  // deactivate/archive flow (different dialog, icon and colour).
  const permanentDelete = usePermanentDelete<Project>({
    invalidateKey: "projects",
    check: checkProjectDeletable,
    remove: deleteProjectPermanently,
    getName: (p) => p.project_name,
    getId: (p) => p.id,
  });

  const columns: DataTableColumn<Project>[] = [
    { key: "name", label: "Project Name", render: (p) => p.project_name },
    { key: "client", label: "Client", render: (p) => clientNameById.get(p.client_id) ?? `#${p.client_id}` },
    { key: "start", label: "Start Date", render: (p) => p.start_date },
    { key: "end", label: "End Date", render: (p) => p.end_date ?? "—" },
    {
      key: "status",
      label: "Status",
      render: (p) => (
        <Chip size="small" label={p.status} color={p.status === "active" ? "success" : "default"} />
      ),
    },
    {
      key: "actions",
      label: "Actions",
      align: "right",
      render: (p) => (
        <Stack direction="row" spacing={0.5} sx={{ justifyContent: "flex-end" }}>
          {p.status === "active" && (
            <Tooltip title="Archive (keeps history)">
              <IconButton size="small" onClick={() => { setConfirmErrorMessage(null); setConfirmTarget(p); }}>
                <ArchiveIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          <Tooltip title="Delete permanently">
            <IconButton size="small" color="error" onClick={() => permanentDelete.start(p)}>
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
          Projects
        </Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={openCreate}>
          New Project
        </Button>
      </Stack>

      <Stack direction="row" spacing={2} sx={{ alignItems: "center", mb: 2, flexWrap: "wrap" }}>
        <SearchBar value={search} onChange={(v) => { setSearch(v); setPage(1); }} placeholder="Search projects..." />
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
        <TextField
          select
          size="small"
          label="Status"
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value as ProjectStatus | ""); setPage(1); }}
          sx={{ minWidth: 140 }}
        >
          <MenuItem value="">All</MenuItem>
          <MenuItem value="active">Active</MenuItem>
          <MenuItem value="archived">Archived</MenuItem>
        </TextField>
        <TextField
          size="small"
          type="date"
          label="Start From"
          slotProps={{ inputLabel: { shrink: true } }}
          value={startDateFrom}
          onChange={(e) => { setStartDateFrom(e.target.value); setPage(1); }}
        />
        <TextField
          size="small"
          type="date"
          label="Start To"
          slotProps={{ inputLabel: { shrink: true } }}
          value={startDateTo}
          onChange={(e) => { setStartDateTo(e.target.value); setPage(1); }}
        />
      </Stack>

      {isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load projects. Please check your connection and try again.
        </Alert>
      )}

      <DataTable
        columns={columns}
        rows={data?.items ?? []}
        rowKey={(p) => p.id}
        loading={isLoading}
        emptyMessage="No projects found."
        page={page}
        pageSize={pageSize}
        total={data?.total ?? 0}
        onPageChange={setPage}
        onPageSizeChange={(size) => { setPageSize(size); setPage(1); }}
      />

      <Modal open={modalOpen} title="New Project" onClose={() => setModalOpen(false)}>
        <Box component="form" onSubmit={handleSubmit((values) => createMutation.mutate(values))} noValidate sx={{ pt: 1 }}>
          <Stack spacing={2}>
            {errorMessage && <Alert severity="error">{errorMessage}</Alert>}
            <Controller
              name="client_id"
              control={control}
              rules={{ required: true, validate: (v) => v > 0 }}
              render={({ field }) => (
                <ClientSelect {...field} error={!!errors.client_id} helperText={errors.client_id ? "Client is required" : undefined} />
              )}
            />
            <TextField
              label="Project Name"
              fullWidth
              error={!!errors.project_name}
              helperText={errors.project_name?.message}
              {...register("project_name", { required: "Project name is required" })}
            />
            <TextField
              label="Start Date"
              type="date"
              fullWidth
              slotProps={{ inputLabel: { shrink: true } }}
              error={!!errors.start_date}
              helperText={errors.start_date?.message}
              {...register("start_date", { required: "Start date is required" })}
            />
            <TextField
              label="End Date"
              type="date"
              fullWidth
              slotProps={{ inputLabel: { shrink: true } }}
              {...register("end_date")}
            />
            <Stack direction="row" spacing={1} sx={{ justifyContent: "flex-end" }}>
              <Button onClick={() => setModalOpen(false)}>Cancel</Button>
              <Button type="submit" variant="contained" disabled={createMutation.isPending}>
                Save
              </Button>
            </Stack>
          </Stack>
        </Box>
      </Modal>

      <ConfirmationDialog
        open={!!confirmTarget}
        title="Archive Project"
        message={`Archive "${confirmTarget?.project_name}"? It will no longer be selectable for new interventions.`}
        confirmLabel="Archive"
        confirmColor="error"
        loading={archiveMutation.isPending}
        errorMessage={confirmErrorMessage}
        onConfirm={() => confirmTarget && archiveMutation.mutate(confirmTarget)}
        onCancel={() => { setConfirmTarget(null); setConfirmErrorMessage(null); }}
      />

      <PermanentDeleteDialog
        open={permanentDelete.open}
        entityNoun="project"
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
