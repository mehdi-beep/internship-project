import { useEffect, useState } from "react";
import {
  Alert,
  AlertTitle,
  Box,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";
import DeleteForeverIcon from "@mui/icons-material/DeleteForever";
import dayjs from "dayjs";
import type { DemoDataStatus } from "../types/intervention";

const CONFIRM_PHRASE = "DELETE DEMO DATA";

interface DeleteDemoDataDialogProps {
  open: boolean;
  status: DemoDataStatus | null;
  statusLoading: boolean;
  loading?: boolean;
  errorMessage?: string | null;
  onConfirm: () => void;
  onCancel: () => void;
}

/**
 * CEO-only, one-time, irreversible cleanup of pre-cutoff seeded/demo
 * interventions (see backend/app/services/demo_cleanup_service.py). This
 * deletes potentially hundreds of records across five tables at once — more
 * than any single-entity PermanentDeleteDialog ever touches — so this uses
 * MORE friction than that dialog's own "type the name" flow: a two-step
 * sequential walkthrough (mirroring CeoSelfDeleteDialog's step gating) before
 * the typed-phrase confirmation is even shown, rather than presenting it
 * immediately.
 *
 * Once the operation has already run (status.already_deleted), there is no
 * confirm path at all — same shape as CeoSelfDeleteDialog's permanently-
 * blocked step 3, which this mirrors directly: explain why, show the
 * disabled result, no button that could ever succeed.
 */
export default function DeleteDemoDataDialog({
  open,
  status,
  statusLoading,
  loading = false,
  errorMessage,
  onConfirm,
  onCancel,
}: DeleteDemoDataDialogProps) {
  const [step, setStep] = useState(1);
  const [typed, setTyped] = useState("");

  useEffect(() => {
    if (open) {
      setStep(1);
      setTyped("");
    }
  }, [open]);

  const alreadyDeleted = status?.already_deleted === true;
  const phraseMatches = typed.trim() === CONFIRM_PHRASE;
  const canDelete = !statusLoading && !alreadyDeleted && phraseMatches && !loading;

  return (
    <Dialog open={open} onClose={loading ? undefined : onCancel} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ display: "flex", alignItems: "center", gap: 1, color: "error.main" }}>
        <DeleteForeverIcon color="error" />
        Delete all demo data
      </DialogTitle>
      <DialogContent>
        <Stack spacing={2}>
          {statusLoading && (
            <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
              <CircularProgress size={18} />
              <Typography variant="body2">Checking how many demo interventions exist…</Typography>
            </Stack>
          )}

          {!statusLoading && alreadyDeleted && (
            <Alert severity="error">
              <AlertTitle>Already completed</AlertTitle>
              Demo intervention cleanup was already performed on{" "}
              <strong>{status?.deleted_at ? dayjs(status.deleted_at).format("MMM D, YYYY [at] HH:mm") : "an earlier date"}</strong>.
              This is a one-time action and cannot be run again — every intervention created since then is
              real data and can never be deleted by this or any other feature.
            </Alert>
          )}

          {!statusLoading && !alreadyDeleted && step === 1 && (
            <Alert severity="warning" icon={<WarningAmberIcon />}>
              <AlertTitle>Step 1 of 2 — what this deletes</AlertTitle>
              This will permanently delete everything created before this feature shipped, treated as
              seeded demo data:
              <Box component="ul" sx={{ mt: 1, mb: 1, pl: 2.5 }}>
                <li>{status?.eligible_count ?? 0} intervention(s), with all of their approval history,
                  attachments (including the uploaded files themselves), and audit trail entries</li>
                <li>{status?.eligible_client_count ?? 0} client(s)</li>
                <li>{status?.eligible_client_site_count ?? 0} client site(s)</li>
                <li>{status?.eligible_contract_count ?? 0} contract(s)</li>
                <li>{status?.eligible_project_count ?? 0} project(s)</li>
                <li>{status?.eligible_legacy_travail_count ?? 0} legacy placeholder travail entry/entries</li>
              </Box>
              Notifications and planning entries that referenced any of these are kept, only with that
              reference cleared. <strong>The real travaux catalog and every user account are never touched
              by this action</strong> — only the legacy placeholder travaux (identified by having a
              category set) are removed; no user is ever deleted here.
            </Alert>
          )}

          {!statusLoading && !alreadyDeleted && step === 2 && (
            <>
              <Alert severity="error" icon={<WarningAmberIcon />}>
                <AlertTitle>Step 2 of 2 — this cannot be undone</AlertTitle>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  There is no confirmation after this. Once deleted, these records and their history are
                  gone from the database permanently — this is not a deactivation and cannot be reversed
                  from the application.
                </Typography>
                <Typography variant="body2">
                  This action only ever applies to the fixed set of records that existed before this
                  feature shipped. Nothing created afterward can be reached by this or any other deletion
                  path, for any role — the real travaux catalog and every user account are excluded from
                  this action entirely, regardless of when they were created.
                </Typography>
              </Alert>
              <Box>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  Type <strong>{CONFIRM_PHRASE}</strong> to confirm:
                </Typography>
                <TextField
                  fullWidth
                  size="small"
                  value={typed}
                  onChange={(e) => setTyped(e.target.value)}
                  placeholder={CONFIRM_PHRASE}
                  autoComplete="off"
                  disabled={loading}
                />
              </Box>
            </>
          )}

          {errorMessage && <Alert severity="error">{errorMessage}</Alert>}
        </Stack>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={onCancel} disabled={loading}>
          Cancel
        </Button>
        {!alreadyDeleted && step < 2 ? (
          <Button
            onClick={() => setStep(step + 1)}
            color="warning"
            variant="contained"
            disabled={statusLoading}
          >
            I understand, continue
          </Button>
        ) : (
          !alreadyDeleted && (
            <Button
              onClick={onConfirm}
              color="error"
              variant="contained"
              startIcon={<DeleteForeverIcon />}
              disabled={!canDelete}
            >
              Delete permanently
            </Button>
          )
        )}
      </DialogActions>
    </Dialog>
  );
}
