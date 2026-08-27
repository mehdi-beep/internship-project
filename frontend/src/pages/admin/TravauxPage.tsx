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
  checkTravailDeletable,
  deleteTravailPermanently,
  activateTravail,
  createTravail,
  deactivateTravail,
  listTravaux,
  listTravauxCategories,
  updateTravail,
  type TravailInput,
} from "../../services/travailService";
import type { Travail } from "../../types/referenceData";

// The database only ever stores travail_code as one plain string (e.g.
// "700-001-XX" or "700-AUDIT") — there is no 3-part structure on the backend
// at all. These three boxes are purely a data-entry convenience: joining
// drops any empty section instead of leaving a stray dash, so
// ["700", "AUDIT", ""] becomes "700-AUDIT", not "700-AUDIT-", and all three
// empty becomes "" (rejected by the existing required-field check below,
// same as an empty single text field always was).
function joinCodeSections(sections: [string, string, string]): string {
  return sections.filter((s) => s.trim() !== "").join("-");
}

// The inverse, used only when opening an EXISTING code for editing. Most of
// the 125 originally-seeded travaux have no dashes at all ("101"), and this
// splits exactly as far as the code's own dashes go — a code with fewer than
// 3 segments just leaves the remaining boxes empty, and re-saving without
// touching anything reproduces the exact same code (splitting an
// already-split code and rejoining it is a no-op).
function splitCodeIntoSections(code: string): [string, string, string] {
  const parts = code.split("-");
  return [parts[0] ?? "", parts[1] ?? "", parts[2] ?? ""];
}

export default function TravauxPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [showInactive, setShowInactive] = useState(false);
  const [editing, setEditing] = useState<Travail | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [confirmTarget, setConfirmTarget] = useState<Travail | null>(null);
  const [confirmErrorMessage, setConfirmErrorMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  // The 3 code-section boxes in the New/Edit Travail form. Kept as plain
  // component state rather than react-hook-form fields since they don't map
  // to 3 real backend values — they're a data-entry convenience for the one
  // real field the API actually expects, travail_code, which is derived from
  // them (joinCodeSections) right before the request is sent.
  const [codeSections, setCodeSections] = useState<[string, string, string]>(["", "", ""]);
  const [codeSectionsTouched, setCodeSectionsTouched] = useState(false);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["travaux", page, pageSize, search, categoryFilter, showInactive],
    queryFn: () =>
      listTravaux({
        page,
        page_size: pageSize,
        search: search || undefined,
        category: categoryFilter || undefined,
        active_only: !showInactive,
      }),
  });

  const { data: categories } = useQuery({
    queryKey: ["travaux", "categories"],
    queryFn: listTravauxCategories,
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
    setCodeSections(["", "", ""]);
    setCodeSectionsTouched(false);
    reset({ travail_code: "", travail_name: "", category: "" });
    setErrorMessage(null);
    setModalOpen(true);
  };

  const openEdit = (travail: Travail) => {
    setEditing(travail);
    // Re-splitting an already-split code and rejoining it reproduces the
    // exact same string, so opening an existing travail — even one of the
    // 125 originally-seeded codes with no dashes at all, like "101" — never
    // changes its code just by being viewed.
    setCodeSections(splitCodeIntoSections(travail.travail_code));
    setCodeSectionsTouched(false);
    reset({ travail_code: travail.travail_code, travail_name: travail.travail_name, category: travail.category ?? "" });
    setErrorMessage(null);
    setModalOpen(true);
  };

  const updateCodeSection = (index: 0 | 1 | 2, value: string) => {
    setCodeSectionsTouched(true);
    setCodeSections((prev) => {
      const next: [string, string, string] = [...prev];
      next[index] = value;
      return next;
    });
  };

  const joinedCode = joinCodeSections(codeSections);
  const codeIsEmpty = codeSectionsTouched && joinedCode.trim() === "";

  const onSubmit = (values: TravailInput) => {
    const payload = { ...values, travail_code: joinedCode };
    if (editing) {
      updateMutation.mutate(payload);
    } else {
      createMutation.mutate(payload);
    }
  };

  // Task 5 — permanent deletion, deliberately separate from the
  // deactivate/archive flow (different dialog, icon and colour).
  const permanentDelete = usePermanentDelete<Travail>({
    invalidateKey: "travaux",
    check: checkTravailDeletable,
    remove: deleteTravailPermanently,
    getName: (t) => t.travail_name,
    getId: (t) => t.id,
  });

  const columns: DataTableColumn<Travail>[] = [
    { key: "code", label: "Code", render: (t) => t.travail_code },
    { key: "name", label: "Task Name", render: (t) => t.travail_name },
    { key: "category", label: "Category", render: (t) => t.category ?? "—" },
    {
      key: "status",
      label: "Status",
      // Task 5 — inactive state must be unmistakable, not plain text.
      render: (t) => (
        <Chip
          size="small"
          label={t.active ? "Active" : "Inactive"}
          color={t.active ? "success" : "default"}
          variant={t.active ? "filled" : "outlined"}
        />
      ),
    },
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
          <Tooltip title={t.active ? "Deactivate (keeps history)" : "Activate"}>
            <IconButton size="small" onClick={() => { setConfirmErrorMessage(null); setConfirmTarget(t); }}>
              {t.active ? <BlockIcon fontSize="small" /> : <CheckCircleIcon fontSize="small" />}
            </IconButton>
          </Tooltip>
          <Tooltip title="Delete permanently">
            <IconButton size="small" color="error" onClick={() => permanentDelete.start(t)}>
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
          Travaux Catalog
        </Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={openCreate}>
          New Travail
        </Button>
      </Stack>

      <Stack direction="row" spacing={2} sx={{ alignItems: "center", mb: 2, flexWrap: "wrap" }}>
        <SearchBar value={search} onChange={(v) => { setSearch(v); setPage(1); }} placeholder="Search by code or name..." />
        <TextField
          select
          size="small"
          label="Category"
          value={categoryFilter}
          onChange={(e) => { setCategoryFilter(e.target.value); setPage(1); }}
          sx={{ minWidth: 180 }}
        >
          <MenuItem value="">All</MenuItem>
          {(categories ?? []).map((category) => (
            <MenuItem key={category} value={category}>
              {category}
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
            <Box>
              <Typography variant="body2" sx={{ mb: 1 }}>
                Task Code
              </Typography>
              <Stack direction="row" spacing={1} sx={{ alignItems: "flex-start" }}>
                <TextField
                  size="small"
                  placeholder="700"
                  autoFocus
                  error={codeIsEmpty}
                  value={codeSections[0]}
                  onChange={(e) => updateCodeSection(0, e.target.value)}
                  sx={{ flex: 1 }}
                />
                <Typography sx={{ pt: 1, color: "text.secondary" }}>—</Typography>
                <TextField
                  size="small"
                  placeholder="001"
                  error={codeIsEmpty}
                  value={codeSections[1]}
                  onChange={(e) => updateCodeSection(1, e.target.value)}
                  sx={{ flex: 1 }}
                />
                <Typography sx={{ pt: 1, color: "text.secondary" }}>—</Typography>
                <TextField
                  size="small"
                  placeholder="XX"
                  error={codeIsEmpty}
                  value={codeSections[2]}
                  onChange={(e) => updateCodeSection(2, e.target.value)}
                  sx={{ flex: 1 }}
                />
              </Stack>
              <Typography
                variant="caption"
                color={codeIsEmpty ? "error" : "text.secondary"}
                sx={{ display: "block", mt: 0.5 }}
              >
                {codeIsEmpty
                  ? "At least one section is required."
                  : joinedCode
                    ? `Will be saved as: ${joinedCode}`
                    : "Any section can be left empty — leave the middle or last box blank for a code like \"700-AUDIT\"."}
              </Typography>
            </Box>
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
              <Button
                type="submit"
                variant="contained"
                onClick={() => setCodeSectionsTouched(true)}
                disabled={joinedCode.trim() === "" || createMutation.isPending || updateMutation.isPending}
              >
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
        // Task 5 — amber, not red: red is reserved for permanent deletion.
        confirmColor={confirmTarget?.active ? "warning" : "primary"}
        loading={toggleActiveMutation.isPending}
        errorMessage={confirmErrorMessage}
        onConfirm={() => confirmTarget && toggleActiveMutation.mutate(confirmTarget)}
        onCancel={() => { setConfirmTarget(null); setConfirmErrorMessage(null); }}
      />

      <PermanentDeleteDialog
        open={permanentDelete.open}
        entityNoun="travail"
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
