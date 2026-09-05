import { useEffect, useState } from "react";
import {
  Alert,
  AlertTitle,
  Box,
  Button,
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

interface CeoSelfDeleteDialogProps {
  open: boolean;
  username: string;
  onCancel: () => void;
}

/**
 * The CEO account is unconditionally protected from permanent deletion —
 * deletion_service.ensure_deletable hard-blocks it server-side, so this
 * dialog can never actually succeed and deliberately has no onConfirm/
 * submit path at all. Its purpose is entirely explanatory: walk a CEO who
 * clicks "Delete permanently" on their own row through why that's
 * disallowed, in three deliberate steps rather than one shared generic
 * dialog's single "type the name" flow (which — see PermanentDeleteDialog's
 * own fix — previously had no idea this row was hard-blocked at all and
 * would visually arm its button regardless).
 */
export default function CeoSelfDeleteDialog({ open, username, onCancel }: CeoSelfDeleteDialogProps) {
  const [step, setStep] = useState(1);
  const [typed, setTyped] = useState("");

  useEffect(() => {
    if (open) {
      setStep(1);
      setTyped("");
    }
  }, [open]);

  const nameMatches = typed.trim() === username.trim();

  return (
    <Dialog open={open} onClose={onCancel} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ display: "flex", alignItems: "center", gap: 1, color: "error.main" }}>
        <DeleteForeverIcon color="error" />
        Delete your CEO account
      </DialogTitle>
      <DialogContent>
        <Stack spacing={2}>
          {step === 1 && (
            <Alert severity="warning" icon={<WarningAmberIcon />}>
              <AlertTitle>Step 1 of 3 — you are about to delete your own account</AlertTitle>
              You are logged in as <strong>{username}</strong>, the CEO account. There is exactly one CEO
              account in this system, and you are it.
            </Alert>
          )}

          {step === 2 && (
            <Alert severity="warning" icon={<WarningAmberIcon />}>
              <AlertTitle>Step 2 of 3 — what deleting the CEO account actually means</AlertTitle>
              <Typography variant="body2" sx={{ mb: 1 }}>
                Only the CEO account can create, edit, deactivate, or permanently delete an Administrator, or
                create a new CEO account. If this account is deleted, nobody in the system retains that
                power — an Administrator cannot grant it back, and a new CEO account cannot be created by
                anyone, since creating one already requires being the CEO.
              </Typography>
              <Typography variant="body2">
                This is not reversible through the application. Recovering from it would require direct
                database access outside this system.
              </Typography>
            </Alert>
          )}

          {step === 3 && (
            <>
              <Alert severity="error" icon={<WarningAmberIcon />}>
                <AlertTitle>Step 3 of 3 — this is the point of no return</AlertTitle>
                For the reasons above, the CEO account cannot actually be deleted from here. This step exists
                to be explicit about that rather than let the action fail silently.
              </Alert>
              <Box>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  Type <strong>{username}</strong> to see the final result:
                </Typography>
                <TextField
                  fullWidth
                  size="small"
                  value={typed}
                  onChange={(e) => setTyped(e.target.value)}
                  placeholder={username}
                  autoComplete="off"
                />
              </Box>
              {nameMatches && (
                <Alert severity="error">
                  <AlertTitle>Blocked</AlertTitle>
                  The CEO account cannot be permanently deleted, including by itself. This protection cannot
                  be bypassed from the application.
                </Alert>
              )}
            </>
          )}
        </Stack>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={onCancel}>Cancel</Button>
        {step < 3 ? (
          <Button onClick={() => setStep(step + 1)} color="warning" variant="contained">
            I understand, continue
          </Button>
        ) : (
          <Button disabled color="error" variant="contained" startIcon={<DeleteForeverIcon />}>
            Delete permanently
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
}
