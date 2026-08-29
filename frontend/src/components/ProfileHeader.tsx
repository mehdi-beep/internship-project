import type { ReactNode } from "react";
import { Avatar, Box, Button, Chip, Stack, Typography } from "@mui/material";
import KeyIcon from "@mui/icons-material/KeyOutlined";

const ROLE_LABELS: Record<string, string> = {
  technician: "Technician",
  chef_technicien: "Chef des Techniciens",
  admin_supervisor: "Administration Supervisor",
  ceo: "CEO",
};

interface ProfileHeaderProps {
  firstName: string;
  lastName: string;
  role: string;
  email: string;
  phone?: string | null;
  /** Omitted entirely when undefined — chef/admin have no active/inactive concept today. */
  active?: boolean;
  /** The "department (if applicable)" slot — e.g. "Supervised by Chef des Techniciens (...)". */
  supervisingRole?: ReactNode;
  /** Task 8 — omitted entirely (not just disabled) when the caller has no
   * reset flow to offer, e.g. the technician profile body doesn't wire this
   * prop at all today; every role that does gets the exact same button and
   * flow, since self-service password reset applies equally to everyone. */
  onResetPasswordClick?: () => void;
}

export default function ProfileHeader({
  firstName,
  lastName,
  role,
  email,
  phone,
  active,
  supervisingRole,
  onResetPasswordClick,
}: ProfileHeaderProps) {
  return (
    <Stack spacing={1.5} sx={{ mb: 1 }}>
      <Stack direction="row" spacing={2} sx={{ alignItems: "center", justifyContent: "space-between", flexWrap: "wrap" }}>
        <Stack direction="row" spacing={2} sx={{ alignItems: "center" }}>
          <Avatar sx={{ width: 56, height: 56, fontSize: "1.5rem" }}>{firstName?.[0]}</Avatar>
          <Box>
            <Stack direction="row" spacing={1} sx={{ alignItems: "center", flexWrap: "wrap" }}>
              <Typography variant="h5" sx={{ fontWeight: 600 }}>
                {firstName} {lastName}
              </Typography>
              <Chip size="small" label={ROLE_LABELS[role] ?? role} />
              {active !== undefined && (
                <Chip size="small" color={active ? "success" : "default"} label={active ? "Active" : "Inactive"} />
              )}
            </Stack>
            <Typography variant="body2" color="text.secondary">
              {email}
              {phone ? ` · ${phone}` : ""}
            </Typography>
          </Box>
        </Stack>
        {onResetPasswordClick && (
          <Button variant="outlined" size="small" startIcon={<KeyIcon />} onClick={onResetPasswordClick} sx={{ textTransform: "none" }}>
            Reset Password
          </Button>
        )}
      </Stack>

      {supervisingRole && (
        <Box>
          <Typography variant="subtitle2" color="text.secondary">
            Department
          </Typography>
          <Typography variant="body2">{supervisingRole}</Typography>
        </Box>
      )}
    </Stack>
  );
}
