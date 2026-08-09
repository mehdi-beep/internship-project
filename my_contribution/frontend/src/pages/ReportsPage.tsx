import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  MenuItem,
  Stack,
  Tab,
  Tabs,
  TextField,
  Typography,
} from "@mui/material";
import PictureAsPdfIcon from "@mui/icons-material/PictureAsPdfOutlined";
import DescriptionIcon from "@mui/icons-material/DescriptionOutlined";
import dayjs from "dayjs";
import DataTable, { type DataTableColumn } from "../components/DataTable";
import { listClients } from "../services/clientService";
import { listUsers } from "../services/userService";
import {
  downloadExport,
  fetchApprovalReport,
  fetchComparisonReport,
  fetchInterventionReport,
  fetchPlanningReport,
} from "../services/reportService";
import type { ApprovalReportRow, InterventionReportRow, PlanningReportRow } from "../types/report";

const INTERVENTION_REPORT_TYPES = [
  { key: "daily", label: "Daily" },
  { key: "weekly", label: "Weekly" },
  { key: "monthly", label: "Monthly" },
  { key: "yearly", label: "Yearly" },
  { key: "technician", label: "Technician" },
  { key: "client", label: "Client" },
  { key: "project", label: "Project" },
  { key: "contract", label: "Contract" },
];

export default function ReportsPage() {
  const [tab, setTab] = useState<"interventions" | "approval" | "planning" | "comparison">("interventions");
  const [reportType, setReportType] = useState("monthly");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [technicianId, setTechnicianId] = useState<number | "">("");
  const [clientId, setClientId] = useState<number | "">("");

  const [periodAFrom, setPeriodAFrom] = useState(dayjs().subtract(1, "month").startOf("month").format("YYYY-MM-DD"));
  const [periodATo, setPeriodATo] = useState(dayjs().subtract(1, "month").endOf("month").format("YYYY-MM-DD"));
  const [periodBFrom, setPeriodBFrom] = useState(dayjs().startOf("month").format("YYYY-MM-DD"));
  const [periodBTo, setPeriodBTo] = useState(dayjs().format("YYYY-MM-DD"));

  const { data: techniciansPage } = useQuery({
    queryKey: ["users", "technicians-select"],
    queryFn: () => listUsers({ role: "technician", page_size: 100 }),
  });
  const { data: clientsData } = useQuery({
    queryKey: ["clients", "lookup-all"],
    queryFn: () => listClients({ page_size: 100, active_only: true }),
  });

  const interventionFilters = {
    type: reportType,
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
    technician_id: technicianId || undefined,
    client_id: clientId || undefined,
  };

  const { data: interventionReport, isLoading: interventionLoading, isError: interventionError } = useQuery({
    queryKey: ["reports", "interventions", interventionFilters],
    queryFn: () => fetchInterventionReport(interventionFilters),
    enabled: tab === "interventions",
  });

  const { data: approvalReport, isLoading: approvalLoading, isError: approvalError } = useQuery({
    queryKey: ["reports", "approval", dateFrom, dateTo],
    queryFn: () => fetchApprovalReport({ date_from: dateFrom || undefined, date_to: dateTo || undefined }),
    enabled: tab === "approval",
  });

  const { data: planningReport, isLoading: planningLoading, isError: planningError } = useQuery({
    queryKey: ["reports", "planning", dateFrom, dateTo],
    queryFn: () => fetchPlanningReport({ date_from: dateFrom || undefined, date_to: dateTo || undefined }),
    enabled: tab === "planning",
  });

  const comparisonFilters = {
    period_a_from: periodAFrom,
    period_a_to: periodATo,
    period_b_from: periodBFrom,
    period_b_to: periodBTo,
    technician_id: technicianId || undefined,
    client_id: clientId || undefined,
  };
  const { data: comparisonReport, isLoading: comparisonLoading, isError: comparisonError } = useQuery({
    queryKey: ["reports", "comparison", comparisonFilters],
    queryFn: () => fetchComparisonReport(comparisonFilters),
    enabled: tab === "comparison",
  });

  const handleExport = (format: "pdf" | "xlsx") => {
    if (tab === "interventions") {
      downloadExport("pdf" === format ? "pdf" : "xlsx", { report: "interventions", ...interventionFilters }, `report.${format}`);
    } else if (tab === "approval") {
      downloadExport(format, { report: "approval", date_from: dateFrom || undefined, date_to: dateTo || undefined }, `approval_report.${format}`);
    } else if (tab === "planning") {
      downloadExport(format, { report: "planning", date_from: dateFrom || undefined, date_to: dateTo || undefined }, `planning_report.${format}`);
    }
  };

  const interventionColumns: DataTableColumn<InterventionReportRow>[] = [
    { key: "bi", label: "BI Number", render: (r) => r.bi_number },
    { key: "date", label: "Date", render: (r) => dayjs(r.intervention_date).format("MMM D, YYYY") },
    { key: "technician", label: "Technician", render: (r) => r.technician_name },
    { key: "client", label: "Client", render: (r) => r.client_name },
    { key: "type", label: "Type", render: (r) => r.intervention_type },
    { key: "status", label: "Status", render: (r) => r.status.replaceAll("_", " ") },
    { key: "duration", label: "Duration (min)", render: (r) => r.net_duration_minutes },
    { key: "points", label: "Points", render: (r) => r.points_earned },
  ];

  const approvalColumns: DataTableColumn<ApprovalReportRow>[] = [
    { key: "bi", label: "BI Number", render: (r) => r.bi_number },
    { key: "level", label: "Level", render: (r) => r.approval_level },
    { key: "approver", label: "Approver", render: (r) => r.approver_name },
    { key: "decision", label: "Decision", render: (r) => <Chip size="small" label={r.decision} color={r.decision === "approved" ? "success" : "error"} /> },
    { key: "date", label: "Date", render: (r) => dayjs(r.approval_date).format("MMM D, YYYY HH:mm") },
    { key: "comment", label: "Comment", render: (r) => r.comment ?? "—" },
  ];

  const planningColumns: DataTableColumn<PlanningReportRow>[] = [
    { key: "technician", label: "Technician", render: (r) => r.technician_name },
    { key: "client", label: "Client", render: (r) => r.client_name },
    { key: "site", label: "Site", render: (r) => r.site_name },
    { key: "date", label: "Date", render: (r) => dayjs(r.planned_date).format("MMM D, YYYY") },
    { key: "priority", label: "Priority", render: (r) => r.priority },
    { key: "status", label: "Status", render: (r) => r.status },
  ];

  return (
    <Box>
      <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center", mb: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>
          Reports
        </Typography>
        {tab !== "comparison" && (
          <Stack direction="row" spacing={1}>
            <Button startIcon={<PictureAsPdfIcon />} variant="outlined" onClick={() => handleExport("pdf")}>
              Export PDF
            </Button>
            <Button startIcon={<DescriptionIcon />} variant="outlined" onClick={() => handleExport("xlsx")}>
              Export Excel
            </Button>
          </Stack>
        )}
      </Stack>

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab value="interventions" label="Interventions" />
        <Tab value="approval" label="Approval" />
        <Tab value="planning" label="Planning" />
        <Tab value="comparison" label="Historical Comparison" />
      </Tabs>

      {tab === "interventions" && (
        <>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Browse and export activity by day, week, month, year, technician, client, project, or contract.
          </Typography>
          <Stack direction="row" spacing={2} sx={{ mb: 2, flexWrap: "wrap", gap: 2 }}>
            <TextField select size="small" label="Report Type" value={reportType} onChange={(e) => setReportType(e.target.value)} sx={{ minWidth: 160 }}>
              {INTERVENTION_REPORT_TYPES.map((t) => (
                <MenuItem key={t.key} value={t.key}>
                  {t.label}
                </MenuItem>
              ))}
            </TextField>
            <TextField size="small" type="date" label="From" slotProps={{ inputLabel: { shrink: true } }} value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
            <TextField size="small" type="date" label="To" slotProps={{ inputLabel: { shrink: true } }} value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
            <TextField select size="small" label="Technician" value={technicianId} onChange={(e) => setTechnicianId(e.target.value ? Number(e.target.value) : "")} sx={{ minWidth: 180 }}>
              <MenuItem value="">All</MenuItem>
              {(techniciansPage?.items ?? []).map((t) => (
                <MenuItem key={t.id} value={t.id}>
                  {t.first_name} {t.last_name}
                </MenuItem>
              ))}
            </TextField>
            <TextField select size="small" label="Client" value={clientId} onChange={(e) => setClientId(e.target.value ? Number(e.target.value) : "")} sx={{ minWidth: 180 }}>
              <MenuItem value="">All</MenuItem>
              {(clientsData?.items ?? []).map((c) => (
                <MenuItem key={c.id} value={c.id}>
                  {c.client_name}
                </MenuItem>
              ))}
            </TextField>
          </Stack>

          {interventionError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              Failed to load this report. Please check your connection and try again.
            </Alert>
          )}

          {interventionReport && (
            <Stack direction="row" spacing={2} sx={{ mb: 2, flexWrap: "wrap" }}>
              <Chip label={`${interventionReport.summary.total_interventions} interventions`} />
              <Chip label={`${(interventionReport.summary.total_duration_minutes / 60).toFixed(1)}h total`} />
              <Chip label={`${interventionReport.summary.total_points} points`} />
              <Chip label={`${interventionReport.summary.fully_approved_count} approved`} color="success" />
              <Chip label={`${interventionReport.summary.rejected_count} rejected`} color="error" />
            </Stack>
          )}

          <DataTable
            columns={interventionColumns}
            rows={interventionReport?.rows ?? []}
            rowKey={(r) => r.bi_number}
            loading={interventionLoading}
            emptyMessage="No interventions match the current filters."
            page={1}
            pageSize={interventionReport?.rows.length || 20}
            total={interventionReport?.rows.length ?? 0}
            onPageChange={() => {}}
            onPageSizeChange={() => {}}
          />
        </>
      )}

      {tab === "approval" && (
        <>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Every technical and administrative approval decision, with approver, date, and outcome.
          </Typography>
          <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
            <TextField size="small" type="date" label="From" slotProps={{ inputLabel: { shrink: true } }} value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
            <TextField size="small" type="date" label="To" slotProps={{ inputLabel: { shrink: true } }} value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
          </Stack>
          {approvalError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              Failed to load this report. Please check your connection and try again.
            </Alert>
          )}

          {approvalReport && (
            <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
              <Chip label={`${approvalReport.total_approved} approved`} color="success" />
              <Chip label={`${approvalReport.total_rejected} rejected`} color="error" />
            </Stack>
          )}
          <DataTable
            columns={approvalColumns}
            rows={approvalReport?.rows ?? []}
            rowKey={(r) => `${r.bi_number}-${r.approval_level}-${r.approval_date}`}
            loading={approvalLoading}
            emptyMessage="No approval decisions match the current filters."
            page={1}
            pageSize={approvalReport?.rows.length || 20}
            total={approvalReport?.rows.length ?? 0}
            onPageChange={() => {}}
            onPageSizeChange={() => {}}
          />
        </>
      )}

      {tab === "planning" && (
        <>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Scheduled interventions across the selected date range, including cancelled entries.
          </Typography>
          <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
            <TextField size="small" type="date" label="From" slotProps={{ inputLabel: { shrink: true } }} value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
            <TextField size="small" type="date" label="To" slotProps={{ inputLabel: { shrink: true } }} value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
          </Stack>
          {planningError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              Failed to load this report. Please check your connection and try again.
            </Alert>
          )}

          {planningReport && (
            <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
              <Chip label={`${planningReport.total_planned} planned`} />
              <Chip label={`${planningReport.total_cancelled} cancelled`} color="default" />
            </Stack>
          )}
          <DataTable
            columns={planningColumns}
            rows={planningReport?.rows ?? []}
            rowKey={(r) => `${r.technician_name}-${r.client_name}-${r.site_name}-${r.planned_date}`}
            loading={planningLoading}
            emptyMessage="No planning entries match the current filters."
            page={1}
            pageSize={planningReport?.rows.length || 20}
            total={planningReport?.rows.length ?? 0}
            onPageChange={() => {}}
            onPageSizeChange={() => {}}
          />
        </>
      )}

      {tab === "comparison" && (
        <Box>
          <Alert severity="info" sx={{ mb: 2 }}>
            Compare two periods side-by-side — e.g. current month vs previous month, or filter by a
            technician/client to compare their activity across periods.
          </Alert>

          {comparisonError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              Failed to load the comparison. Please check your connection and try again.
            </Alert>
          )}
          <Stack direction="row" spacing={2} sx={{ mb: 2, flexWrap: "wrap", gap: 2 }}>
            <TextField select size="small" label="Technician" value={technicianId} onChange={(e) => setTechnicianId(e.target.value ? Number(e.target.value) : "")} sx={{ minWidth: 180 }}>
              <MenuItem value="">All</MenuItem>
              {(techniciansPage?.items ?? []).map((t) => (
                <MenuItem key={t.id} value={t.id}>
                  {t.first_name} {t.last_name}
                </MenuItem>
              ))}
            </TextField>
            <TextField select size="small" label="Client" value={clientId} onChange={(e) => setClientId(e.target.value ? Number(e.target.value) : "")} sx={{ minWidth: 180 }}>
              <MenuItem value="">All</MenuItem>
              {(clientsData?.items ?? []).map((c) => (
                <MenuItem key={c.id} value={c.id}>
                  {c.client_name}
                </MenuItem>
              ))}
            </TextField>
          </Stack>

          <Stack direction="row" spacing={3} sx={{ flexWrap: "wrap" }}>
            <Card variant="outlined" sx={{ flex: 1, minWidth: 320 }}>
              <CardContent>
                <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>
                  Period A
                </Typography>
                <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
                  <TextField size="small" type="date" label="From" slotProps={{ inputLabel: { shrink: true } }} value={periodAFrom} onChange={(e) => setPeriodAFrom(e.target.value)} />
                  <TextField size="small" type="date" label="To" slotProps={{ inputLabel: { shrink: true } }} value={periodATo} onChange={(e) => setPeriodATo(e.target.value)} />
                </Stack>
                {comparisonReport && !comparisonLoading && (
                  <Stack spacing={0.5}>
                    <Typography variant="h4" sx={{ fontWeight: 600 }}>
                      {comparisonReport.period_a.total_interventions}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      interventions
                    </Typography>
                    <Typography variant="body2">{(comparisonReport.period_a.total_duration_minutes / 60).toFixed(1)}h total duration</Typography>
                    <Typography variant="body2">{comparisonReport.period_a.total_points} points</Typography>
                    <Typography variant="body2" color="success.main">
                      {comparisonReport.period_a.fully_approved_count} approved
                    </Typography>
                    <Typography variant="body2" color="error.main">
                      {comparisonReport.period_a.rejected_count} rejected
                    </Typography>
                  </Stack>
                )}
              </CardContent>
            </Card>
            <Card variant="outlined" sx={{ flex: 1, minWidth: 320 }}>
              <CardContent>
                <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>
                  Period B
                </Typography>
                <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
                  <TextField size="small" type="date" label="From" slotProps={{ inputLabel: { shrink: true } }} value={periodBFrom} onChange={(e) => setPeriodBFrom(e.target.value)} />
                  <TextField size="small" type="date" label="To" slotProps={{ inputLabel: { shrink: true } }} value={periodBTo} onChange={(e) => setPeriodBTo(e.target.value)} />
                </Stack>
                {comparisonReport && !comparisonLoading && (
                  <Stack spacing={0.5}>
                    <Typography variant="h4" sx={{ fontWeight: 600 }}>
                      {comparisonReport.period_b.total_interventions}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      interventions
                    </Typography>
                    <Typography variant="body2">{(comparisonReport.period_b.total_duration_minutes / 60).toFixed(1)}h total duration</Typography>
                    <Typography variant="body2">{comparisonReport.period_b.total_points} points</Typography>
                    <Typography variant="body2" color="success.main">
                      {comparisonReport.period_b.fully_approved_count} approved
                    </Typography>
                    <Typography variant="body2" color="error.main">
                      {comparisonReport.period_b.rejected_count} rejected
                    </Typography>
                  </Stack>
                )}
              </CardContent>
            </Card>
          </Stack>
        </Box>
      )}
    </Box>
  );
}
