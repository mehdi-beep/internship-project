import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  Box,
  Button,
  Chip,
  IconButton,
  MenuItem,
  Stack,
  Switch,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import EditIcon from "@mui/icons-material/EditOutlined";
import BlockIcon from "@mui/icons-material/BlockOutlined";
import CheckCircleIcon from "@mui/icons-material/CheckCircleOutlined";
import DeleteForeverIcon from "@mui/icons-material/DeleteForever";
import KeyIcon from "@mui/icons-material/KeyOutlined";
import { Controller, useForm } from "react-hook-form";
import DataTable, { type DataTableColumn } from "../../components/DataTable";
import SearchBar from "../../components/SearchBar";
import Modal from "../../components/Modal";
import ConfirmationDialog from "../../components/ConfirmationDialog";
import PermanentDeleteDialog from "../../components/PermanentDeleteDialog";
import { usePermanentDelete } from "../../hooks/usePermanentDelete";
import {
  checkUserDeletable,
  deleteUserPermanently,
  activateUser,
  createUser,
  deactivateUser,
  listUsers,
  resetPassword,
  updateUser,
  type UserCreateInput,
  type UserUpdateInput,
} from "../../services/userService";
import type { UserRole } from "../../types/enums";
import type { AppUser } from "../../types/referenceData";
import { useAuth } from "../../context/AuthContext";

const ROLE_LABELS: Record<UserRole, string> = {
  technician: "Technician",
  chef_technicien: "Chef des Techniciens",
  admin_supervisor: "Administration Supervisor",
  // Task 3 — surfaced here too (not just seeded once) so the Administrator
  // can create additional hallway-display accounts through the existing
  // Users CRUD if a second physical screen/location is ever added, rather
  // than needing a bespoke account-creation flow for one role.
  display: "Display (Hallway Calendar)",
  // Task 7 — the single protected owner account. Present here purely for
  // display (the CEO row's own chip, and so this Record stays exhaustively
  // typed) — "ceo" is deliberately never offered as a selectable option in
  // the create/edit role dropdown below (see roleOptionsFor / ROLE_OPTIONS),
  // since a second CEO can never be created through this form or any other.
  ceo: "CEO",
};

// The roles a given viewer is allowed to ASSIGN through the create/edit
// form's Role dropdown — distinct from ROLE_LABELS above, which covers every
// role that can ever be DISPLAYED (e.g. an existing CEO/Admin row still
// needs a label even though nobody can newly assign those roles from here).
// "ceo" is never offered as something to newly assign to someone else — the
// one CEO account is seeded, not created via this form, and the backend's
// own _ensure_single_ceo would refuse a second one regardless.
// "admin_supervisor" is offered only when the current viewer IS the CEO,
// matching the backend's _ensure_can_manage_role wall exactly (a regular
// Admin attempting to POST a new admin_supervisor account would get 403 from
// the API even if this dropdown somehow still showed the option, so hiding
// it here is a genuine UX match for the real rule, not the rule itself).
//
// `currentRole` (the account actually being edited, undefined when creating)
// is always included even if it wouldn't normally be offered — this is what
// lets a CEO open their OWN account for editing (e.g. to fix a typo in their
// name) without the Role field rendering blank/invalid because "ceo" isn't
// in the base list. It does not make "ceo" newly assignable to anyone else;
// selecting a DIFFERENT role for an existing CEO would still need to pass
// the backend's own checks same as any other change.
function roleOptionsFor(viewerRole: UserRole, currentRole?: UserRole): UserRole[] {
  const base: UserRole[] = ["technician", "chef_technicien", "display"];
  const options = viewerRole === "ceo" ? [...base, "admin_supervisor" as UserRole] : base;
  if (currentRole && !options.includes(currentRole)) {
    options.push(currentRole);
  }
  return options;
}

// The frontend mirror of the backend's real wall
// (user_service._ensure_can_manage_role): true whenever `viewerRole` is not
// CEO and `targetRole` is CEO or Admin. This is purely a UX affordance — a
// regular Admin blocked here would ALSO be blocked by the API itself if they
// somehow bypassed this (403), so hiding the actions here just avoids
// showing controls that would only ever fail.
function isRestrictedFor(viewerRole: UserRole, targetRole: UserRole): boolean {
  return viewerRole !== "ceo" && (targetRole === "admin_supervisor" || targetRole === "ceo");
}

type FormValues = UserCreateInput;

function extractErrorDetail(err: unknown, fallback: string): string {
  const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
  return detail ?? fallback;
}

export default function UsersPage() {
  const { user: currentUser } = useAuth();
  // Falls back to "admin_supervisor" only in the type-theoretic case where
  // this page renders before the auth context has resolved a user at all —
  // it's already route-guarded to admin_supervisor/ceo, so in practice this
  // is always one of those two by the time a real person sees this page.
  const viewerRole: UserRole = currentUser?.role ?? "admin_supervisor";

  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState<UserRole | "">("");
  const [showInactive, setShowInactive] = useState(false);
  const [editing, setEditing] = useState<AppUser | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [confirmTarget, setConfirmTarget] = useState<AppUser | null>(null);
  const [confirmErrorMessage, setConfirmErrorMessage] = useState<string | null>(null);
  const [resetTarget, setResetTarget] = useState<AppUser | null>(null);
  const [resetErrorMessage, setResetErrorMessage] = useState<string | null>(null);
  const [newPassword, setNewPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["users", page, pageSize, search, roleFilter, showInactive],
    queryFn: () =>
      listUsers({
        page,
        page_size: pageSize,
        search: search || undefined,
        role: roleFilter || undefined,
        active_only: !showInactive,
      }),
  });

  const { register, control, handleSubmit, reset, watch, formState: { errors } } = useForm<FormValues>();
  // A Display account is a TV/kiosk login, not a real person (see
  // app/models/role.py's RoleName.DISPLAY doc comment) — no email needed.
  // Every other role still requires one, matching the backend's own
  // _require_email_unless_display validator in app/schemas/user.py.
  const selectedRole = watch("role");
  const emailRequiredForRole = selectedRole !== "display";

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["users"] });

  const createMutation = useMutation({
    mutationFn: (input: UserCreateInput) => createUser(input),
    onSuccess: () => {
      invalidate();
      setModalOpen(false);
    },
    onError: (err: unknown) => setErrorMessage(extractErrorDetail(err, "Failed to create user.")),
  });

  const updateMutation = useMutation({
    mutationFn: (input: UserUpdateInput) => updateUser(editing!.id, input),
    onSuccess: () => {
      invalidate();
      setModalOpen(false);
    },
    onError: (err: unknown) => setErrorMessage(extractErrorDetail(err, "Failed to update user.")),
  });

  const toggleActiveMutation = useMutation({
    mutationFn: (user: AppUser) => (user.active ? deactivateUser(user.id) : activateUser(user.id)),
    onSuccess: () => {
      invalidate();
      setConfirmTarget(null);
      setConfirmErrorMessage(null);
    },
    onError: () => setConfirmErrorMessage("Failed to update the user. Please try again."),
  });

  const resetPasswordMutation = useMutation({
    mutationFn: () => resetPassword(resetTarget!.id, newPassword),
    onSuccess: () => {
      setResetTarget(null);
      setNewPassword("");
      setResetErrorMessage(null);
    },
    onError: () => setResetErrorMessage("Failed to reset the password. Please try again."),
  });

  const openCreate = () => {
    setEditing(null);
    reset({ first_name: "", last_name: "", username: "", email: "", phone: "", role: "technician", password: "" });
    setErrorMessage(null);
    setModalOpen(true);
  };

  const openEdit = (user: AppUser) => {
    setEditing(user);
    reset({
      first_name: user.first_name,
      last_name: user.last_name,
      username: user.username,
      email: user.email,
      phone: user.phone ?? "",
      role: user.role,
      password: "",
    });
    setErrorMessage(null);
    setModalOpen(true);
  };

  const onSubmit = (values: FormValues) => {
    if (editing) {
      updateMutation.mutate({
        first_name: values.first_name,
        last_name: values.last_name,
        email: values.email,
        phone: values.phone,
        role: values.role,
      });
    } else {
      createMutation.mutate(values);
    }
  };

  // Task 5 — permanent deletion, deliberately separate from the
  // deactivate/archive flow (different dialog, icon and colour).
  const permanentDelete = usePermanentDelete<AppUser>({
    invalidateKey: "users",
    check: checkUserDeletable,
    remove: deleteUserPermanently,
    getName: (u) => `${u.first_name} ${u.last_name}`,
    getId: (u) => u.id,
  });

  // Task 7 — an Admin viewing the CEO's or another Admin's row: per explicit
  // instruction, Name/Username/Role stay visible (so the row is still
  // identifiable) but Email/Status/every action button show a plain
  // "Restricted" label instead of the real value or a clickable control.
  // The CEO viewing this same page sees every row completely normally — the
  // wall only ever applies to a non-CEO viewer looking at a CEO/Admin row.
  const columns: DataTableColumn<AppUser>[] = [
    { key: "name", label: "Name", render: (u) => `${u.first_name} ${u.last_name}` },
    { key: "username", label: "Username", render: (u) => u.username },
    {
      key: "email",
      label: "Email",
      render: (u) => (isRestrictedFor(viewerRole, u.role) ? <Typography color="text.disabled">Restricted</Typography> : u.email),
    },
    { key: "role", label: "Role", render: (u) => <Chip size="small" label={ROLE_LABELS[u.role]} /> },
    {
      key: "status",
      label: "Status",
      // Task 5 — inactive state must be unmistakable, not plain text.
      render: (u) =>
        isRestrictedFor(viewerRole, u.role) ? (
          <Typography color="text.disabled">Restricted</Typography>
        ) : (
          <Chip
            size="small"
            label={u.active ? "Active" : "Inactive"}
            color={u.active ? "success" : "default"}
            variant={u.active ? "filled" : "outlined"}
          />
        ),
    },
    {
      key: "actions",
      label: "Actions",
      align: "right",
      render: (u) =>
        isRestrictedFor(viewerRole, u.role) ? (
          <Typography color="text.disabled" sx={{ textAlign: "right", pr: 1 }}>
            Restricted
          </Typography>
        ) : (
          <Stack direction="row" spacing={0.5} sx={{ justifyContent: "flex-end" }}>
            <Tooltip title="Edit">
              <IconButton size="small" onClick={() => openEdit(u)}>
                <EditIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            <Tooltip title="Reset Password">
              <IconButton size="small" onClick={() => { setResetTarget(u); setNewPassword(""); setResetErrorMessage(null); }}>
                <KeyIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            <Tooltip title={u.active ? "Deactivate (keeps history)" : "Activate"}>
              <IconButton size="small" onClick={() => { setConfirmErrorMessage(null); setConfirmTarget(u); }}>
                {u.active ? <BlockIcon fontSize="small" /> : <CheckCircleIcon fontSize="small" />}
              </IconButton>
            </Tooltip>
            <Tooltip title="Delete permanently">
              <IconButton size="small" color="error" onClick={() => permanentDelete.start(u)}>
                <DeleteForeverIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Stack>
        ),
    },
  ];

  const roleOptions = roleOptionsFor(viewerRole, editing?.role);

  return (
    <Box>
      <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center", mb: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>
          Users
        </Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={openCreate}>
          New User
        </Button>
      </Stack>

      <Stack direction="row" spacing={2} sx={{ alignItems: "center", mb: 2, flexWrap: "wrap" }}>
        <SearchBar value={search} onChange={(v) => { setSearch(v); setPage(1); }} placeholder="Search users..." />
        <TextField
          select
          size="small"
          label="Role"
          value={roleFilter}
          onChange={(e) => { setRoleFilter(e.target.value as UserRole | ""); setPage(1); }}
          sx={{ minWidth: 200 }}
        >
          <MenuItem value="">All roles</MenuItem>
          {Object.entries(ROLE_LABELS).map(([value, label]) => (
            <MenuItem key={value} value={value}>
              {label}
            </MenuItem>
          ))}
        </TextField>
        <Stack direction="row" spacing={0.5} sx={{ alignItems: "center" }}>
          <Switch checked={showInactive} onChange={(e) => { setShowInactive(e.target.checked); setPage(1); }} size="small" />
          <Typography variant="body2">Show inactive</Typography>
        </Stack>
      </Stack>

      {isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load users. Please check your connection and try again.
        </Alert>
      )}

      <DataTable
        columns={columns}
        rows={data?.items ?? []}
        rowKey={(u) => u.id}
        loading={isLoading}
        emptyMessage="No users found."
        page={page}
        pageSize={pageSize}
        total={data?.total ?? 0}
        onPageChange={setPage}
        onPageSizeChange={(size) => { setPageSize(size); setPage(1); }}
      />

      <Modal open={modalOpen} title={editing ? "Edit User" : "New User"} onClose={() => setModalOpen(false)}>
        <Box component="form" onSubmit={handleSubmit(onSubmit)} noValidate sx={{ pt: 1 }}>
          <Stack spacing={2}>
            {errorMessage && <Alert severity="error">{errorMessage}</Alert>}
            <Stack direction="row" spacing={2}>
              <TextField
                label="First Name"
                fullWidth
                autoFocus
                error={!!errors.first_name}
                helperText={errors.first_name?.message}
                {...register("first_name", { required: "First name is required" })}
              />
              <TextField
                label="Last Name"
                fullWidth
                error={!!errors.last_name}
                helperText={errors.last_name?.message}
                {...register("last_name", { required: "Last name is required" })}
              />
            </Stack>
            <TextField
              label="Username"
              fullWidth
              disabled={!!editing}
              error={!!errors.username}
              helperText={editing ? "Username cannot be changed." : errors.username?.message}
              {...register("username", { required: !editing && "Username is required" })}
            />
            <TextField
              label="Email"
              fullWidth
              type="email"
              error={!!errors.email}
              helperText={errors.email?.message ?? (emailRequiredForRole ? undefined : "Optional for Display accounts")}
              {...register("email", { required: emailRequiredForRole && "Email is required" })}
            />
            <TextField label="Phone" fullWidth {...register("phone")} />
            {/* A Controller, not register(), and deliberately no
                defaultValue: MUI's Select needs an explicit `value` prop to
                reliably repaint its visible selection when that value
                changes programmatically (via reset()) rather than through a
                user click — register()'s plain ref-based binding updates
                the underlying form state correctly but doesn't reliably
                force MUI's Select to visually reflect it. This was the
                second half of the same original bug: editing any user
                always showed "Technician" in the dropdown regardless of
                their real role. The first half (a stale defaultValue
                permanently overriding the field) is fixed by removing
                defaultValue entirely; this second half (the visible
                dropdown not repainting even once the correct value reaches
                the form) needed the field to become properly controlled,
                the same pattern already used for the equivalent Technician
                dropdown in PlanningPage.tsx. */}
            <Controller
              name="role"
              control={control}
              rules={{ required: true }}
              render={({ field }) => (
                <TextField select label="Role" fullWidth {...field}>
                  {roleOptions.map((value) => (
                    <MenuItem key={value} value={value}>
                      {ROLE_LABELS[value]}
                    </MenuItem>
                  ))}
                </TextField>
              )}
            />
            {!editing && (
              <TextField
                label="Password"
                type="password"
                fullWidth
                error={!!errors.password}
                helperText={errors.password?.message ?? "Minimum 8 characters."}
                {...register("password", { required: "Password is required", minLength: { value: 8, message: "Minimum 8 characters" } })}
              />
            )}
            <Stack direction="row" spacing={1} sx={{ justifyContent: "flex-end" }}>
              <Button onClick={() => setModalOpen(false)}>Cancel</Button>
              <Button type="submit" variant="contained" disabled={createMutation.isPending || updateMutation.isPending}>
                Save
              </Button>
            </Stack>
          </Stack>
        </Box>
      </Modal>

      <Modal
        open={!!resetTarget}
        title={`Reset Password — ${resetTarget?.username ?? ""}`}
        onClose={() => { setResetTarget(null); setResetErrorMessage(null); }}
      >
        <Stack spacing={2} sx={{ pt: 1 }}>
          {resetErrorMessage && <Alert severity="error">{resetErrorMessage}</Alert>}
          <TextField
            label="New Password"
            type="password"
            fullWidth
            autoFocus
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            helperText="Minimum 8 characters."
          />
          <Stack direction="row" spacing={1} sx={{ justifyContent: "flex-end" }}>
            <Button onClick={() => { setResetTarget(null); setResetErrorMessage(null); }}>Cancel</Button>
            <Button
              variant="contained"
              disabled={newPassword.length < 8 || resetPasswordMutation.isPending}
              onClick={() => resetPasswordMutation.mutate()}
            >
              Reset Password
            </Button>
          </Stack>
        </Stack>
      </Modal>

      <ConfirmationDialog
        open={!!confirmTarget}
        title={confirmTarget?.active ? "Deactivate User" : "Activate User"}
        message={
          confirmTarget?.active
            ? `Deactivate "${confirmTarget?.first_name} ${confirmTarget?.last_name}"? They will no longer be able to log in.`
            : `Reactivate "${confirmTarget?.first_name} ${confirmTarget?.last_name}"?`
        }
        confirmLabel={confirmTarget?.active ? "Deactivate" : "Activate"}
        // Task 5 — amber, not red: red is reserved for permanent deletion.
        confirmColor={confirmTarget?.active ? "warning" : "primary"}
        loading={toggleActiveMutation.isPending}
        errorMessage={confirmErrorMessage}
        onConfirm={() => confirmTarget && toggleActiveMutation.mutate(confirmTarget)}
        onCancel={() => { setConfirmTarget(null); setConfirmErrorMessage(null); }}
      />

      <PermanentDeleteDialog
        open={permanentDelete.open}
        entityNoun="user"
        entityName={permanentDelete.name}
        check={permanentDelete.deletionCheck}
        checkLoading={permanentDelete.checkLoading}
        loading={permanentDelete.loading}
        errorMessage={permanentDelete.errorMessage}
        onConfirm={permanentDelete.confirm}
        onCancel={permanentDelete.cancel}
      />
    </Box>
  );
}
