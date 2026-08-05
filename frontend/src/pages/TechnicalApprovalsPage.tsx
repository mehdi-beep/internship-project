import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, Box, Button, Stack, Typography } from "@mui/material";
import dayjs from "dayjs";
import DataTable, { type DataTableColumn } from "../components/DataTable";
import ApprovalReviewDialog from "../components/ApprovalReviewDialog";
import { listClients } from "../services/clientService";
import {
  decideTechnicalApproval,
  listTechnicalPending,
  type ApprovalDecision,
} from "../services/approvalService";
import type { Intervention } from "../types/intervention";

export default function TechnicalApprovalsPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [reviewingId, setReviewingId] = useState<number | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["approvals", "technical-pending", page, pageSize],
    queryFn: () => listTechnicalPending({ page, page_size: pageSize }),
  });

  const { data: clientsData } = useQuery({
    queryKey: ["clients", "lookup-all"],
    queryFn: () => listClients({ page_size: 100, active_only: true }),
  });
  const clientNameById = new Map((clientsData?.items ?? []).map((c) => [c.id, c.client_name]));

  const decideMutation = useMutation({
    mutationFn: (input: { decision: ApprovalDecision; comment: string }) =>
      decideTechnicalApproval(reviewingId!, { decision: input.decision, comment: input.comment || null }),
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
      key: "submitted",
      label: "Submission Date",
      render: (i) => (i.submission_date ? dayjs(i.submission_date).format("MMM D, YYYY HH:mm") : "—"),
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

  return (
    <Box>
      <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center", mb: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>
          Technical Approvals
        </Typography>
      </Stack>

      {isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load the technical approval queue. Please check your connection and try again.
        </Alert>
      )}

      <DataTable
        columns={columns}
        rows={data?.items ?? []}
        rowKey={(i) => i.id}
        loading={isLoading}
        emptyMessage="No interventions pending technical approval."
        page={page}
        pageSize={pageSize}
        total={data?.total ?? 0}
        onPageChange={setPage}
        onPageSizeChange={(size) => {
          setPageSize(size);
          setPage(1);
        }}
      />

      <ApprovalReviewDialog
        interventionId={reviewingId}
        level="technical"
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
