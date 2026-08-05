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
import { Controller, useForm } from "react-hook-form";
import DataTable, { type DataTableColumn } from "../../components/DataTable";
import SearchBar from "../../components/SearchBar";
import Modal from "../../components/Modal";
import ConfirmationDialog from "../../components/ConfirmationDialog";
import ClientSelect from "../../components/ClientSelect";
import { listClients } from "../../services/clientService";
import { archiveContract, createContract, listContracts, type ContractInput } from "../../services/contractService";
import type { Contract, ContractStatus } from "../../types/referenceData";

export default function ContractsPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [search, setSearch] = useState("");
  const [clientFilter, setClientFilter] = useState<number | "">("");
  const [statusFilter, setStatusFilter] = useState<ContractStatus | "">("");
  const [modalOpen, setModalOpen] = useState(false);
  const [confirmTarget, setConfirmTarget] = useState<Contract | null>(null);
  const [confirmErrorMessage, setConfirmErrorMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["contracts", page, pageSize, search, clientFilter, statusFilter],
    queryFn: () =>
      listContracts({
        page,
        page_size: pageSize,
        search: search || undefined,
        client_id: clientFilter || undefined,
        status: statusFilter || undefined,
      }),
  });

  const { data: clientsData } = useQuery({
    queryKey: ["clients", "lookup-all"],
    queryFn: () => listClients({ page_size: 100, active_only: true }),
  });
  const clientNameById = new Map((clientsData?.items ?? []).map((c) => [c.id, c.client_name]));

  const { register, handleSubmit, reset, control, formState: { errors } } = useForm<ContractInput>();

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["contracts"] });

  const createMutation = useMutation({
    mutationFn: (input: ContractInput) => createContract(input),
    onSuccess: () => {
      invalidate();
      setModalOpen(false);
    },
    onError: () => setErrorMessage("Failed to save contract."),
  });

  const archiveMutation = useMutation({
    mutationFn: (contract: Contract) => archiveContract(contract.id),
    onSuccess: () => {
      invalidate();
      setConfirmTarget(null);
      setConfirmErrorMessage(null);
    },
    onError: () => setConfirmErrorMessage("Failed to archive the contract. Please try again."),
  });

  const openCreate = () => {
    reset({ client_id: 0, contract_name: "", start_date: "", end_date: "" });
    setErrorMessage(null);
    setModalOpen(true);
  };

  const columns: DataTableColumn<Contract>[] = [
    { key: "name", label: "Contract Name", render: (c) => c.contract_name },
    { key: "client", label: "Client", render: (c) => clientNameById.get(c.client_id) ?? `#${c.client_id}` },
    { key: "start", label: "Start Date", render: (c) => c.start_date },
    { key: "end", label: "End Date", render: (c) => c.end_date ?? "—" },
    {
      key: "status",
      label: "Status",
      render: (c) => (
        <Chip size="small" label={c.status} color={c.status === "active" ? "success" : "default"} />
      ),
    },
    {
      key: "actions",
      label: "Actions",
      align: "right",
      render: (c) =>
        c.status === "active" ? (
          <Tooltip title="Archive">
            <IconButton size="small" onClick={() => { setConfirmErrorMessage(null); setConfirmTarget(c); }}>
              <ArchiveIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        ) : (
          "—"
        ),
    },
  ];

  return (
    <Box>
      <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center", mb: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>
          Contracts
        </Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={openCreate}>
          New Contract
        </Button>
      </Stack>

      <Stack direction="row" spacing={2} sx={{ alignItems: "center", mb: 2, flexWrap: "wrap" }}>
        <SearchBar value={search} onChange={(v) => { setSearch(v); setPage(1); }} placeholder="Search contracts..." />
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
          onChange={(e) => { setStatusFilter(e.target.value as ContractStatus | ""); setPage(1); }}
          sx={{ minWidth: 140 }}
        >
          <MenuItem value="">All</MenuItem>
          <MenuItem value="active">Active</MenuItem>
          <MenuItem value="archived">Archived</MenuItem>
        </TextField>
      </Stack>

      {isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load contracts. Please check your connection and try again.
        </Alert>
      )}

      <DataTable
        columns={columns}
        rows={data?.items ?? []}
        rowKey={(c) => c.id}
        loading={isLoading}
        emptyMessage="No contracts found."
        page={page}
        pageSize={pageSize}
        total={data?.total ?? 0}
        onPageChange={setPage}
        onPageSizeChange={(size) => { setPageSize(size); setPage(1); }}
      />

      <Modal open={modalOpen} title="New Contract" onClose={() => setModalOpen(false)}>
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
              label="Contract Name"
              fullWidth
              error={!!errors.contract_name}
              helperText={errors.contract_name?.message}
              {...register("contract_name", { required: "Contract name is required" })}
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
        title="Archive Contract"
        message={`Archive "${confirmTarget?.contract_name}"? It will no longer be selectable for new interventions.`}
        confirmLabel="Archive"
        confirmColor="error"
        loading={archiveMutation.isPending}
        errorMessage={confirmErrorMessage}
        onConfirm={() => confirmTarget && archiveMutation.mutate(confirmTarget)}
        onCancel={() => { setConfirmTarget(null); setConfirmErrorMessage(null); }}
      />
    </Box>
  );
}
