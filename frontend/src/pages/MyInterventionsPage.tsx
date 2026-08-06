import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Alert, Box, Button, FormControlLabel, MenuItem, Stack, Switch, Tab, Tabs, TextField, Typography } from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import dayjs from "dayjs";
import DataTable, { type DataTableColumn } from "../components/DataTable";
import SearchBar from "../components/SearchBar";
import StatusBadge from "../components/StatusBadge";
import GenericCalendar, { type GenericCalendarEvent } from "../components/GenericCalendar";
import ViewModeToggle, { type ViewMode } from "../components/ViewModeToggle";
import { listClients } from "../services/clientService";
import { listInterventions } from "../services/interventionService";
import { useAuth } from "../context/AuthContext";
import { interventionEventColor } from "../utils/interventionColors";
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
  const [viewMode, setViewMode] = useState<ViewMode>("list");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [search, setSearch] = useState("");
  const [clientFilter, setClientFilter] = useState<number | "">("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [assistedOnly, setAssistedOnly] = useState(false);

  const activeTab = TABS[tabIndex];
  // The API filters one status at a time; multi-status tabs are filtered client-side
  // over the fetched page, so a single-status tab stays server-filtered and exact.
  const serverStatus = activeTab.statuses.length === 1 ? activeTab.statuses[0] : undefined;

  const { data, isLoading, isError } = useQuery({
    queryKey: ["interventions", page, pageSize, search, clientFilter, dateFrom, dateTo, serverStatus, assistedOnly, user?.id],
    queryFn: () =>
      listInterventions({
        page,
        page_size: pageSize,
        search: search || undefined,
        client_id: clientFilter || undefined,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        status: serverStatus,
        colleague_technician_id: assistedOnly && isTechnician ? user?.id : undefined,
      }),
  });

  // Calendar mode needs a much wider window than the paginated List view can
  // provide (20 rows would only ever show a handful of scattered events) — a
  // separate, parallel fetch at the interventions endpoint's max page_size,
  // leaving the List query above (and its pagination) completely untouched.
  // The fetched range tracks whatever month(s) FullCalendar is currently
  // showing (via onVisibleRangeChange), so navigating prev/next/today
  // actually loads that period's data instead of silently staying empty
  // outside the initial default window.
  const [calendarRange, setCalendarRange] = useState(() => ({
    date_from: dayjs().startOf("month").subtract(1, "month").format("YYYY-MM-DD"),
    date_to: dayjs().endOf("month").add(1, "month").format("YYYY-MM-DD"),
  }));
  const { data: calendarData } = useQuery({
    queryKey: ["interventions", "calendar", calendarRange, search, clientFilter, serverStatus, assistedOnly, user?.id],
    queryFn: () =>
      listInterventions({
        page: 1,
        page_size: 100,
        search: search || undefined,
        client_id: clientFilter || undefined,
        date_from: dateFrom || calendarRange.date_from,
        date_to: dateTo || calendarRange.date_to,
        status: serverStatus,
        colleague_technician_id: assistedOnly && isTechnician ? user?.id : undefined,
      }),
    enabled: viewMode === "calendar",
  });

  const { data: clientsData } = useQuery({
    queryKey: ["clients", "lookup-all"],
    queryFn: () => listClients({ page_size: 100, active_only: true }),
  });
  const clientNameById = new Map((clientsData?.items ?? []).map((c) => [c.id, c.client_name]));

  const rows = (data?.items ?? []).filter((i) =>
    activeTab.statuses.length <= 1 ? true : activeTab.statuses.includes(i.status),
  );

  const calendarRows = (calendarData?.items ?? []).filter((i) =>
    activeTab.statuses.length <= 1 ? true : activeTab.statuses.includes(i.status),
  );
  const calendarEvents: GenericCalendarEvent[] = calendarRows.map((i) => ({
    id: i.id,
    date: i.intervention_date,
    title: `${i.bi_number} — ${clientNameById.get(i.client_id) ?? "Client"}`,
    color: interventionEventColor(i.status),
    onClick: () => navigate(`/interventions/${i.id}`),
  }));

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
        <Stack direction="row" spacing={1.5} sx={{ alignItems: "center" }}>
          <ViewModeToggle value={viewMode} onChange={setViewMode} />
          {isTechnician && (
            <Button variant="contained" startIcon={<AddIcon />} onClick={() => navigate("/interventions/new")}>
              New Intervention
            </Button>
          )}
        </Stack>
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
        {isTechnician && (
          <FormControlLabel
            control={
              <Switch
                checked={assistedOnly}
                onChange={(e) => {
                  setAssistedOnly(e.target.checked);
                  setPage(1);
                }}
              />
            }
            label="Include interventions I assisted on"
          />
        )}
      </Stack>

      {isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load interventions. Please check your connection and try again.
        </Alert>
      )}

      {viewMode === "list" ? (
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
      ) : calendarRows.length === 0 ? (
        <Typography variant="body2" color="text.secondary" sx={{ py: 4, textAlign: "center" }}>
          No interventions found.
        </Typography>
      ) : (
        <GenericCalendar
          events={calendarEvents}
          onVisibleRangeChange={(range) => setCalendarRange({ date_from: range.start, date_to: range.end })}
        />
      )}
    </Box>
  );
}
