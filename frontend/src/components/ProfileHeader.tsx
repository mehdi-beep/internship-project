import type { ReactNode } from "react";
import { Avatar, Box, Chip, Stack, Typography } from "@mui/material";

const ROLE_LABELS: Record<string, string> = {
  technician: "Technician",
  chef_technicien: "Chef des Techniciens",
  admin_supervisor: "Administration Supervisor",
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
}

export default function ProfileHeader({
  firstName,
  lastName,
  role,
  email,
  phone,
  active,
  supervisingRole,
}: ProfileHeaderProps) {
  return (
    <Stack spacing={1.5} sx={{ mb: 1 }}>
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
