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
import { useForm } from "react-hook-form";
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

const ROLE_LABELS: Record<UserRole, string> = {
  technician: "Technician",
  chef_technicien: "Chef des Techniciens",
  admin_supervisor: "Administration Supervisor",
  // Task 3 — surfaced here too (not just seeded once) so the Administrator
  // can create additional hallway-display accounts through the existing
  // Users CRUD if a second physical screen/location is ever added, rather
  // than needing a bespoke account-creation flow for one role.
  display: "Display (Hallway Calendar)",
};

type FormValues = UserCreateInput;

function extractErrorDetail(err: unknown, fallback: string): string {
  const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
  return detail ?? fallback;
}

export default function UsersPage() {
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

  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormValues>();

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

  const columns: DataTableColumn<AppUser>[] = [
    { key: "name", label: "Name", render: (u) => `${u.first_name} ${u.last_name}` },
    { key: "username", label: "Username", render: (u) => u.username },
    { key: "email", label: "Email", render: (u) => u.email },
    { key: "role", label: "Role", render: (u) => <Chip size="small" label={ROLE_LABELS[u.role]} /> },
    {
      key: "status",
      label: "Status",
      // Task 5 — inactive state must be unmistakable, not plain text.
      render: (u) => (
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
      render: (u) => (
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
              helperText={errors.email?.message}
              {...register("email", { required: "Email is required" })}
            />
            <TextField label="Phone" fullWidth {...register("phone")} />
            <TextField select label="Role" fullWidth defaultValue="technician" {...register("role", { required: true })}>
              {Object.entries(ROLE_LABELS).map(([value, label]) => (
                <MenuItem key={value} value={value}>
                  {label}
                </MenuItem>
              ))}
            </TextField>
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
