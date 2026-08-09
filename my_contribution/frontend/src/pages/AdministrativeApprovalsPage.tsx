import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, Box, Button, Stack, Typography } from "@mui/material";
import dayjs from "dayjs";
import DataTable, { type DataTableColumn } from "../components/DataTable";
import InterventionReviewViewer from "../components/InterventionReviewViewer";
import GenericCalendar, { type GenericCalendarEvent } from "../components/GenericCalendar";
import ViewModeToggle, { type ViewMode } from "../components/ViewModeToggle";
import { listClients } from "../services/clientService";
import {
  decideAdministrativeApproval,
  listAdministrativePending,
  type ApprovalDecision,
} from "../services/approvalService";
import { interventionEventColor } from "../utils/interventionColors";
import type { Intervention } from "../types/intervention";

export default function AdministrativeApprovalsPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [viewMode, setViewMode] = useState<ViewMode>("list");
  const [reviewingId, setReviewingId] = useState<number | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["approvals", "administrative-pending", page, pageSize],
    queryFn: () => listAdministrativePending({ page, page_size: pageSize }),
  });

  // Calendar mode needs the full queue, not just one paginated page — a
  // parallel fetch at the endpoint's current max page_size, list view and
  // its pagination stay untouched.
  const { data: calendarData } = useQuery({
    queryKey: ["approvals", "administrative-pending", "calendar"],
    queryFn: () => listAdministrativePending({ page: 1, page_size: 100 }),
    enabled: viewMode === "calendar",
  });

  const { data: clientsData } = useQuery({
    queryKey: ["clients", "lookup-all"],
    queryFn: () => listClients({ page_size: 100, active_only: true }),
  });
  const clientNameById = new Map((clientsData?.items ?? []).map((c) => [c.id, c.client_name]));

  const decideMutation = useMutation({
    mutationFn: (input: { decision: ApprovalDecision; comment: string }) =>
      decideAdministrativeApproval(reviewingId!, { decision: input.decision, comment: input.comment || null }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["approvals"] });
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      setReviewingId(null);
      setErrorMessage(null);
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setErrorMessage(detail ?? "Failed to record the decision.");
    },
  });

  const columns: DataTableColumn<Intervention>[] = [
    { key: "bi", label: "BI Number", render: (i) => i.bi_number },
    { key: "client", label: "Client", render: (i) => clientNameById.get(i.client_id) ?? `#${i.client_id}` },
    {
      key: "technical_approval",
      label: "Technical Approval",
      render: (i) => (i.technical_approval_date ? dayjs(i.technical_approval_date).format("MMM D, YYYY HH:mm") : "—"),
    },
    { key: "type", label: "Type", render: (i) => i.intervention_type },
    {
      key: "actions",
      label: "",
      align: "right",
      render: (i) => (
        <Button size="small" variant="outlined" onClick={() => setReviewingId(i.id)}>
          Review
        </Button>
      ),
    },
  ];

  const items = data?.items ?? [];
  const calendarItems = calendarData?.items ?? [];
  const datedItems = calendarItems.filter((i) => i.technical_approval_date);
  const undatedCount = calendarItems.length - datedItems.length;
  const calendarEvents: GenericCalendarEvent[] = datedItems.map((i) => ({
    id: i.id,
    date: i.technical_approval_date!,
    title: `${i.bi_number} — ${clientNameById.get(i.client_id) ?? "Client"}`,
    color: interventionEventColor(i.status),
    onClick: () => setReviewingId(i.id),
  }));

  return (
    <Box>
      <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center", mb: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>
          Administrative Approvals
        </Typography>
        <ViewModeToggle value={viewMode} onChange={setViewMode} />
      </Stack>

      {isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load the administrative approval queue. Please check your connection and try again.
        </Alert>
      )}

      {viewMode === "list" ? (
        <DataTable
          columns={columns}
          rows={items}
          rowKey={(i) => i.id}
          loading={isLoading}
          emptyMessage="No interventions pending administrative approval."
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
        <>
          {undatedCount > 0 && (
            <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 1 }}>
              {undatedCount} item(s) without a technical approval date are shown in List view only.
            </Typography>
          )}
          {datedItems.length === 0 ? (
            <Typography variant="body2" color="text.secondary" sx={{ py: 4, textAlign: "center" }}>
              No interventions pending administrative approval.
            </Typography>
          ) : (
            <GenericCalendar events={calendarEvents} />
          )}
        </>
      )}

      <InterventionReviewViewer
        interventionId={reviewingId}
        level="administrative"
        deciding={decideMutation.isPending}
        errorMessage={errorMessage}
        onClose={() => {
          setReviewingId(null);
          setErrorMessage(null);
        }}
        onDecide={(decision, comment) => decideMutation.mutate({ decision, comment })}
      />
    </Box>
  );
}
