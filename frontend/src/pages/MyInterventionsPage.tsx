import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Alert, Box, Button, MenuItem, Stack, Tab, Tabs, TextField, Typography } from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import dayjs from "dayjs";
import DataTable, { type DataTableColumn } from "../components/DataTable";
import SearchBar from "../components/SearchBar";
import StatusBadge from "../components/StatusBadge";
import { listClients } from "../services/clientService";
import { listInterventions } from "../services/interventionService";
import { useAuth } from "../context/AuthContext";
import type { InterventionStatus } from "../types/enums";
import type { Intervention } from "../types/intervention";

// Ch.58 tabs. "Planned" maps to the planned lifecycle state; the remaining tabs
// group the approval states a technician cares about.
const TABS: { label: string; statuses: InterventionStatus[] }[] = [
  { label: "All", statuses: [] },
  { label: "Draft", statuses: ["draft"] },
  { label: "Planned", statuses: ["planned"] },
  { label: "Submitted", statuses: ["submitted", "pending_technical_approval", "technical_approved", "pending_administrative_approval"] },
  { label: "Rejected", statuses: ["rejected"] },
  { label: "Approved", statuses: ["fully_approved"] },
];

export default function MyInterventionsPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const isTechnician = user?.role === "technician";

  const [tabIndex, setTabIndex] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [search, setSearch] = useState("");
  const [clientFilter, setClientFilter] = useState<number | "">("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const activeTab = TABS[tabIndex];
  // The API filters one status at a time; multi-status tabs are filtered client-side
  // over the fetched page, so a single-status tab stays server-filtered and exact.
  const serverStatus = activeTab.statuses.length === 1 ? activeTab.statuses[0] : undefined;

  const { data, isLoading, isError } = useQuery({
    queryKey: ["interventions", page, pageSize, search, clientFilter, dateFrom, dateTo, serverStatus],
    queryFn: () =>
      listInterventions({
        page,
        page_size: pageSize,
        search: search || undefined,
        client_id: clientFilter || undefined,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        status: serverStatus,
      }),
  });

  const { data: clientsData } = useQuery({
    queryKey: ["clients", "lookup-all"],
    queryFn: () => listClients({ page_size: 100, active_only: true }),
  });
  const clientNameById = new Map((clientsData?.items ?? []).map((c) => [c.id, c.client_name]));

  const rows = (data?.items ?? []).filter((i) =>
    activeTab.statuses.length <= 1 ? true : activeTab.statuses.includes(i.status),
  );

  const columns: DataTableColumn<Intervention>[] = [
    { key: "bi", label: "BI Number", render: (i) => i.bi_number },
    { key: "client", label: "Client", render: (i) => clientNameById.get(i.client_id) ?? `#${i.client_id}` },
    { key: "date", label: "Date", render: (i) => dayjs(i.intervention_date).format("MMM D, YYYY") },
    { key: "type", label: "Type", render: (i) => i.intervention_type },
    { key: "status", label: "Status", render: (i) => <StatusBadge status={i.status} /> },
    {
      key: "actions",
      label: "",
      align: "right",
      render: (i) => (
        <Button size="small" onClick={() => navigate(`/interventions/${i.id}`)}>
          View
        </Button>
      ),
    },
  ];

  return (
    <Box>
      <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center", mb: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>
          {isTechnician ? "My Interventions" : "Interventions"}
        </Typography>
        {isTechnician && (
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => navigate("/interventions/new")}>
            New Intervention
          </Button>
        )}
      </Stack>

      <Tabs
        value={tabIndex}
        onChange={(_, v) => {
          setTabIndex(v);
          setPage(1);
        }}
        sx={{ mb: 2 }}
        variant="scrollable"
        scrollButtons="auto"
      >
        {TABS.map((t) => (
          <Tab key={t.label} label={t.label} />
        ))}
      </Tabs>

      <Stack direction="row" spacing={2} sx={{ alignItems: "center", mb: 2, flexWrap: "wrap", gap: 2 }}>
        <SearchBar
          value={search}
          onChange={(v) => {
            setSearch(v);
            setPage(1);
          }}
          placeholder="Search by BI number..."
        />
        <TextField
          select
          size="small"
          label="Client"
          value={clientFilter}
          onChange={(e) => {
            setClientFilter(e.target.value ? Number(e.target.value) : "");
            setPage(1);
          }}
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
          size="small"
          type="date"
          label="From"
          slotProps={{ inputLabel: { shrink: true } }}
          value={dateFrom}
          onChange={(e) => {
            setDateFrom(e.target.value);
            setPage(1);
          }}
        />
        <TextField
          size="small"
          type="date"
          label="To"
          slotProps={{ inputLabel: { shrink: true } }}
          value={dateTo}
          onChange={(e) => {
            setDateTo(e.target.value);
            setPage(1);
          }}
        />
      </Stack>

      {isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load interventions. Please check your connection and try again.
        </Alert>
      )}

      <DataTable
        columns={columns}
        rows={rows}
        rowKey={(i) => i.id}
        loading={isLoading}
        emptyMessage="No interventions found."
        page={page}
        pageSize={pageSize}
        total={data?.total ?? 0}
        onPageChange={setPage}
        onPageSizeChange={(size) => {
          setPageSize(size);
          setPage(1);
        }}
      />
    </Box>
  );
}
