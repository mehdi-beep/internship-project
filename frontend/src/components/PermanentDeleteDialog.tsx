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
  List,
  ListItem,
  ListItemText,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";
import DeleteForeverIcon from "@mui/icons-material/DeleteForever";
import type { DeletionCheck } from "../types/deletion";

interface PermanentDeleteDialogProps {
  open: boolean;
  /** What is being deleted, e.g. "client" — used throughout the copy. */
  entityNoun: string;
  /** The record's display name. The Administrator must type it to confirm. */
  entityName: string;
  /** Pre-flight blocker check; null while still loading. */
  check: DeletionCheck | null;
  checkLoading: boolean;
  loading?: boolean;
  errorMessage?: string | null;
  onConfirm: () => void;
  onCancel: () => void;
}

/**
 * Task 5 — the destructive counterpart to ConfirmationDialog, deliberately
 * distinct from it so "Deactivate" and "Delete permanently" can never be
 * mistaken for one another:
 *
 *  - explicit red "PERMANENT DELETION" warning panel
 *  - lists exactly what will lose its link to this record, so the
 *    Administrator sees the consequences before confirming
 *  - requires typing the record's name to arm the button (no accidental
 *    double-click deletion)
 */
export default function PermanentDeleteDialog({
  open,
  entityNoun,
  entityName,
  check,
  checkLoading,
  loading = false,
  errorMessage,
  onConfirm,
  onCancel,
}: PermanentDeleteDialogProps) {
  const [typed, setTyped] = useState("");

  // Reset the typed confirmation whenever the dialog is reopened, so a
  // previous entry can never carry over and pre-arm the button.
  useEffect(() => {
    if (open) setTyped("");
  }, [open, entityName]);

  // No entity is hard-blocked from permanent deletion any more — every
  // reference is detached (never destroyed), and for a User specifically
  // their name is frozen onto each referencing row before the link is
  // cleared. `blockers` here is purely informational: what will lose its
  // link to this record, always alongside the confirm flow below, never in
  // place of it.
  const impacts = check?.blockers ?? [];
  const nameMatches = typed.trim() === entityName.trim();
  const canDelete = !checkLoading && nameMatches && !loading;

  return (
    <Dialog open={open} onClose={loading ? undefined : onCancel} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ display: "flex", alignItems: "center", gap: 1, color: "error.main" }}>
        <DeleteForeverIcon color="error" />
        Delete {entityNoun} permanently
      </DialogTitle>
      <DialogContent>
        <Stack spacing={2}>
          {checkLoading && (
            <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
              <CircularProgress size={18} />
              <Typography variant="body2">Checking whether this {entityNoun} can be safely deleted…</Typography>
            </Stack>
          )}

          {!checkLoading && impacts.length > 0 && (
            <Alert severity="warning" icon={<WarningAmberIcon />}>
              <AlertTitle>These records will lose their link to this {entityNoun}</AlertTitle>
              <Typography variant="body2" sx={{ mb: 1 }}>
                They are <strong>not deleted</strong> — every intervention, planning entry, approval and audit
                entry keeps all of its own data and history.{" "}
                {entityNoun === "user"
                  ? "Wherever this person's name was shown, it stays visible as a plain label instead of a live account."
                  : `They will simply no longer show this ${entityNoun}.`}
              </Typography>
              <List dense disablePadding>
                {impacts.map((b) => (
                  <ListItem key={b.label} disablePadding sx={{ pl: 1 }}>
                    <ListItemText primary={`• ${b.count} ${b.label}`} />
                  </ListItem>
                ))}
              </List>
            </Alert>
          )}

          {!checkLoading && (
            <>
              <Alert severity="warning" icon={<WarningAmberIcon />}>
                <AlertTitle>This cannot be undone</AlertTitle>
                This will permanently remove the {entityNoun} <strong>{entityName}</strong> from the database.
                Unlike deactivation, the record is destroyed and cannot be restored.
              </Alert>
              <Box>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  Type <strong>{entityName}</strong> to confirm:
                </Typography>
                <TextField
                  fullWidth
                  size="small"
                  value={typed}
                  onChange={(e) => setTyped(e.target.value)}
                  placeholder={entityName}
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
        <Button
          onClick={onConfirm}
          color="error"
          variant="contained"
          startIcon={<DeleteForeverIcon />}
          disabled={!canDelete}
        >
          Delete permanently
        </Button>
      </DialogActions>
    </Dialog>
  );
}
