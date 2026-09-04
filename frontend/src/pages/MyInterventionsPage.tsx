import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Alert, Box, Button, FormControlLabel, MenuItem, Stack, Switch, Tab, Tabs, TextField, Typography } from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import dayjs from "dayjs";
import DataTable, { type DataTableColumn } from "../components/DataTable";
import SearchBar from "../components/SearchBar";
import StatusBadge from "../components/StatusBadge";
import GenericCalendar, { type GenericCalendarEvent } from "../components/GenericCalendar";
import ViewModeToggle, { type ViewMode } from "../components/ViewModeToggle";
import { listClients } from "../services/clientService";
import { listContracts } from "../services/contractService";
import { listInterventions } from "../services/interventionService";
import { listProjects } from "../services/projectService";
import { listSiteCities } from "../services/siteService";
import { listTechnicianOptions } from "../services/userService";
import { useAuth } from "../context/AuthContext";
import { interventionEventColor } from "../utils/interventionColors";
import type { InterventionStatus, InterventionType } from "../types/enums";
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

const TYPE_LABELS: Record<InterventionType, string> = {
  standard: "Standard",
  contract: "Contract",
  project: "Project",
  warranty: "Warranty",
};

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
  const [technicianFilter, setTechnicianFilter] = useState<number | "">("");
  const [cityFilter, setCityFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState<InterventionType | "">("");
  const [contractFilter, setContractFilter] = useState<number | "">("");
  const [projectFilter, setProjectFilter] = useState<number | "">("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [assistedOnly, setAssistedOnly] = useState(false);

  // The Technician filter only makes sense for Chef/Admin viewing everyone's
  // interventions — a technician's own list is already scoped to themselves
  // server-side (Ch.16), so narrowing "by technician" is meaningless there
  // (there's only ever one). Contract/Project, by contrast, apply to every
  // role: GET /contracts and GET /projects are T/C/A read endpoints (Rule 3
  // pattern), and a technician can create contract-/project-type interventions
  // themselves (InterventionFormPage), so filtering their own list down to
  // "just Contract X" is a legitimate narrowing of data they already see —
  // not a permission escalation — and stays available to every role.
  const isPrivilegedViewer = !isTechnician;

  const activeTab = TABS[tabIndex];
  // Both branches are server-side filters now — a single-status tab uses
  // `status`, a multi-status tab (e.g. "Submitted", which spans 4 lifecycle
  // statuses) uses `status_in`. Previously the multi-status case was
  // filtered client-side over an already-paginated page, which made the
  // visible row count and the pagination total disagree (a page could show
  // "1 of 20" while rendering only 1-3 rows, since most of that raw page
  // didn't belong to the group) — this was a real, reported pagination bug.
  const serverStatus = activeTab.statuses.length === 1 ? activeTab.statuses[0] : undefined;
  const serverStatusIn = activeTab.statuses.length > 1 ? activeTab.statuses : undefined;

  const { data, isLoading, isError } = useQuery({
    queryKey: [
      "interventions",
      page,
      pageSize,
      search,
      clientFilter,
      technicianFilter,
      cityFilter,
      typeFilter,
      contractFilter,
      projectFilter,
      dateFrom,
      dateTo,
      serverStatus,
      serverStatusIn,
      assistedOnly,
      user?.id,
    ],
    queryFn: () =>
      listInterventions({
        page,
        page_size: pageSize,
        search: search || undefined,
        client_id: clientFilter || undefined,
        technician_id: isPrivilegedViewer ? technicianFilter || undefined : undefined,
        city: cityFilter || undefined,
        intervention_type: typeFilter || undefined,
        contract_id: contractFilter || undefined,
        project_id: projectFilter || undefined,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        status: serverStatus,
        status_in: serverStatusIn,
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
    queryKey: [
      "interventions",
      "calendar",
      calendarRange,
      search,
      clientFilter,
      technicianFilter,
      cityFilter,
      typeFilter,
      contractFilter,
      projectFilter,
      serverStatus,
      serverStatusIn,
      assistedOnly,
      user?.id,
    ],
    queryFn: () =>
      listInterventions({
        page: 1,
        page_size: 100,
        search: search || undefined,
        client_id: clientFilter || undefined,
        technician_id: isPrivilegedViewer ? technicianFilter || undefined : undefined,
        city: cityFilter || undefined,
        intervention_type: typeFilter || undefined,
        contract_id: contractFilter || undefined,
        project_id: projectFilter || undefined,
        date_from: dateFrom || calendarRange.date_from,
        date_to: dateTo || calendarRange.date_to,
        status: serverStatus,
        status_in: serverStatusIn,
        colleague_technician_id: assistedOnly && isTechnician ? user?.id : undefined,
      }),
    enabled: viewMode === "calendar",
    // Without this, `calendarData` resets to undefined the instant
    // calendarRange changes (every prev/next/today click, since it's part of
    // the query key above) — calendarRows.length briefly reads 0, which
    // renders "No interventions found" and unmounts <GenericCalendar>,
    // destroying FullCalendar's own internal current-month pointer. Keeping
    // the previous page's data visible during the refetch avoids both the
    // false-empty flash and the resulting reset-to-today on remount.
    placeholderData: keepPreviousData,
  });

  const { data: clientsData } = useQuery({
    queryKey: ["clients", "lookup-all"],
    queryFn: () => listClients({ page_size: 100, active_only: true }),
  });
  const clientNameById = new Map((clientsData?.items ?? []).map((c) => [c.id, c.client_name]));

  const { data: technicianOptions } = useQuery({
    queryKey: ["users", "technician-options"],
    queryFn: listTechnicianOptions,
    enabled: isPrivilegedViewer,
  });

  const { data: cities } = useQuery({
    queryKey: ["sites", "cities"],
    queryFn: listSiteCities,
  });

  const { data: contractsData } = useQuery({
    queryKey: ["contracts", "lookup-all"],
    queryFn: () => listContracts({ page_size: 100 }),
  });

  const { data: projectsData } = useQuery({
    queryKey: ["projects", "lookup-all"],
    queryFn: () => listProjects({ page_size: 100 }),
  });

  // No client-side re-filtering by tab anymore — status/status_in above
  // already ask the server for exactly the rows this tab should show, so
  // `data.items`/`data.total` and what's actually rendered always agree.
  const rows = data?.items ?? [];
  const calendarRows = calendarData?.items ?? [];
  const calendarEvents: GenericCalendarEvent[] = calendarRows.map((i) => ({
    id: i.id,
    date: i.intervention_date,
    title: `${i.bi_number} — ${(i.client_id != null ? clientNameById.get(i.client_id) : undefined) ?? "Client"}`,
    color: interventionEventColor(i.status),
    onClick: () => navigate(`/interventions/${i.id}`),
  }));

  const columns: DataTableColumn<Intervention>[] = [
    { key: "bi", label: "BI Number", render: (i) => i.bi_number },
    { key: "client", label: "Client", render: (i) => (i.client_id != null ? clientNameById.get(i.client_id) : undefined) ?? `#${i.client_id}` },
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
          placeholder="Search by BI number, client, or site..."
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
        {isPrivilegedViewer && (
          <TextField
            select
            size="small"
            label="Technician"
            value={technicianFilter}
            onChange={(e) => {
              setTechnicianFilter(e.target.value ? Number(e.target.value) : "");
              setPage(1);
            }}
            sx={{ minWidth: 180 }}
          >
            <MenuItem value="">All</MenuItem>
            {(technicianOptions ?? []).map((t) => (
              <MenuItem key={t.id} value={t.id}>
                {t.first_name} {t.last_name}
              </MenuItem>
            ))}
          </TextField>
        )}
        <TextField
          select
          size="small"
          label="City"
          value={cityFilter}
          onChange={(e) => {
            setCityFilter(e.target.value);
            setPage(1);
          }}
          sx={{ minWidth: 160 }}
        >
          <MenuItem value="">All</MenuItem>
          {(cities ?? []).map((city) => (
            <MenuItem key={city} value={city}>
              {city}
            </MenuItem>
          ))}
        </TextField>
        <TextField
          select
          size="small"
          label="Type"
          value={typeFilter}
          onChange={(e) => {
            setTypeFilter(e.target.value as InterventionType | "");
            setPage(1);
          }}
          sx={{ minWidth: 150 }}
        >
          <MenuItem value="">All</MenuItem>
          {Object.entries(TYPE_LABELS).map(([value, label]) => (
            <MenuItem key={value} value={value}>
              {label}
            </MenuItem>
          ))}
        </TextField>
        <TextField
          select
          size="small"
          label="Contract"
          value={contractFilter}
          onChange={(e) => {
            setContractFilter(e.target.value ? Number(e.target.value) : "");
            setPage(1);
          }}
          sx={{ minWidth: 180 }}
        >
          <MenuItem value="">All</MenuItem>
          {(contractsData?.items ?? []).map((c) => (
            <MenuItem key={c.id} value={c.id}>
              {c.contract_name}
            </MenuItem>
          ))}
        </TextField>
        <TextField
          select
          size="small"
          label="Project"
          value={projectFilter}
          onChange={(e) => {
            setProjectFilter(e.target.value ? Number(e.target.value) : "");
            setPage(1);
          }}
          sx={{ minWidth: 180 }}
        >
          <MenuItem value="">All</MenuItem>
          {(projectsData?.items ?? []).map((p) => (
            <MenuItem key={p.id} value={p.id}>
              {p.project_name}
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
      ) : (
        // Always mounted once in calendar mode — previously this branched on
        // calendarRows.length === 0 to show a "No interventions found" message
        // instead, which unmounted <GenericCalendar> (and the FullCalendar
        // instance inside it) on every empty/in-flight result. Losing that
        // mount destroyed FullCalendar's own internal current-month pointer,
        // so navigating past an empty month reset the view to today on
        // remount instead of continuing to the next month. An empty events
        // array renders as a normal empty calendar grid, which is the
        // correct, expected behavior for "no interventions this period" —
        // no separate message needed.
        <GenericCalendar
          events={calendarEvents}
          onVisibleRangeChange={(range) => setCalendarRange({ date_from: range.start, date_to: range.end })}
        />
      )}
    </Box>
  );
}
