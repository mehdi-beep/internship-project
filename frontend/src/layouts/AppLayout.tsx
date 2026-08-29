import { useState, type ReactNode } from "react";
import {
  AppBar,
  Avatar,
  Badge,
  Box,
  Chip,
  Divider,
  Drawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  IconButton,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import DashboardIcon from "@mui/icons-material/DashboardOutlined";
import AssignmentIcon from "@mui/icons-material/AssignmentOutlined";
import EventNoteIcon from "@mui/icons-material/EventNoteOutlined";
import FactCheckIcon from "@mui/icons-material/FactCheckOutlined";
import GroupIcon from "@mui/icons-material/GroupOutlined";
import BusinessIcon from "@mui/icons-material/BusinessOutlined";
import DescriptionIcon from "@mui/icons-material/DescriptionOutlined";
import BuildIcon from "@mui/icons-material/BuildOutlined";
import MilitaryTechIcon from "@mui/icons-material/MilitaryTechOutlined";
import BarChartIcon from "@mui/icons-material/BarChartOutlined";
import NotificationsIcon from "@mui/icons-material/NotificationsOutlined";
import LogoutIcon from "@mui/icons-material/LogoutOutlined";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useNotificationPollingContext } from "../context/NotificationPollingContext";
import type { UserRole } from "../types/enums";

const DRAWER_WIDTH = 240;
// Ch.104 — tablet gets a collapsed, icon-only rail rather than the full labeled sidebar.
const RAIL_WIDTH = 72;

const ROLE_LABELS: Record<string, string> = {
  technician: "Technician",
  chef_technicien: "Chef des Techniciens",
  admin_supervisor: "Administration Supervisor",
  display: "Display",
  ceo: "CEO",
};

interface NavItem {
  label: string;
  icon: ReactNode;
  path: string;
}

const ADMIN_SUPERVISOR_NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", icon: <DashboardIcon />, path: "/dashboard" },
  { label: "Planning", icon: <EventNoteIcon />, path: "/planning" },
  { label: "Interventions", icon: <AssignmentIcon />, path: "/interventions" },
  { label: "Administrative Approvals", icon: <FactCheckIcon />, path: "/approvals/administrative" },
  { label: "Users", icon: <GroupIcon />, path: "/admin/users" },
  { label: "Clients", icon: <BusinessIcon />, path: "/admin/clients" },
  { label: "Client Sites", icon: <BusinessIcon />, path: "/admin/sites" },
  { label: "Contracts", icon: <DescriptionIcon />, path: "/admin/contracts" },
  { label: "Projects", icon: <DescriptionIcon />, path: "/admin/projects" },
  { label: "Travaux", icon: <BuildIcon />, path: "/admin/travaux" },
  { label: "Point Management", icon: <MilitaryTechIcon />, path: "/admin/point-rules" },
  { label: "Reports", icon: <BarChartIcon />, path: "/reports" },
  { label: "Notifications", icon: <NotificationsIcon />, path: "/notifications" },
];

const NAV_ITEMS_BY_ROLE: Record<UserRole, NavItem[]> = {
  technician: [
    { label: "Dashboard", icon: <DashboardIcon />, path: "/dashboard" },
    { label: "My Interventions", icon: <AssignmentIcon />, path: "/interventions" },
    { label: "Notifications", icon: <NotificationsIcon />, path: "/notifications" },
  ],
  chef_technicien: [
    { label: "Dashboard", icon: <DashboardIcon />, path: "/dashboard" },
    { label: "Planning", icon: <EventNoteIcon />, path: "/planning" },
    { label: "Interventions", icon: <AssignmentIcon />, path: "/interventions" },
    { label: "Technical Approvals", icon: <FactCheckIcon />, path: "/approvals/technical" },
    { label: "Reports", icon: <BarChartIcon />, path: "/reports" },
    { label: "Notifications", icon: <NotificationsIcon />, path: "/notifications" },
  ],
  admin_supervisor: ADMIN_SUPERVISOR_NAV_ITEMS,
  // Task 7 — the CEO sees exactly what an Administrator sees: every backend
  // require_roles("admin_supervisor", ...) call was widened to also accept
  // "ceo" (see backend/app/api/*.py), so every one of these routes is
  // genuinely reachable, not just visually shown. The one place CEO differs
  // from Admin is inside the Users page itself (managing another Admin or
  // the CEO account is CEO-exclusive) — see UsersPage.tsx.
  ceo: ADMIN_SUPERVISOR_NAV_ITEMS,
  // The display role never actually renders AppLayout — its one page
  // (DisplayCalendarPage) is deliberately layout-free (no sidebar/top bar,
  // per "occupy the available screen efficiently") and routed outside
  // ProtectedRoute+AppLayout entirely. Present here only so this Record
  // stays exhaustively typed over every UserRole; empty by design.
  display: [],
};

export default function AppLayout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const { unreadCount } = useNotificationPollingContext();
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  // Ch.104 breakpoints: Desktop = full sidebar, Tablet = collapsed rail, Mobile = drawer.
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));
  const isTablet = useMediaQuery(theme.breakpoints.between("sm", "md"));
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  const navItems = user ? NAV_ITEMS_BY_ROLE[user.role] : [];
  const currentWidth = isTablet ? RAIL_WIDTH : DRAWER_WIDTH;

  const handleNavigate = (path: string) => {
    navigate(path);
    if (isMobile) setMobileOpen(false);
  };

  const navList = (
    <Box sx={{ overflow: "auto" }}>
      <List>
        {navItems.map((item) => (
          <ListItemButton
            key={item.label}
            selected={location.pathname === item.path}
            onClick={() => handleNavigate(item.path)}
            sx={isTablet ? { justifyContent: "center", px: 1 } : undefined}
            title={isTablet ? item.label : undefined}
          >
            <ListItemIcon sx={isTablet ? { minWidth: 0, justifyContent: "center" } : undefined}>
              {item.path === "/notifications" && unreadCount > 0 ? (
                <Badge badgeContent={unreadCount} color="error" max={99}>
                  {item.icon}
                </Badge>
              ) : (
                item.icon
              )}
            </ListItemIcon>
            {!isTablet && <ListItemText primary={item.label} />}
          </ListItemButton>
        ))}
      </List>
      <Divider />
    </Box>
  );

  return (
    <Box sx={{ display: "flex", minHeight: "100vh" }}>
      <AppBar position="fixed" color="inherit" sx={{ zIndex: (t) => t.zIndex.drawer + 1, bgcolor: "background.paper" }}>
        <Toolbar sx={{ justifyContent: "space-between" }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            {isMobile && (
              <IconButton
                edge="start"
                aria-label="Open navigation menu"
                onClick={() => setMobileOpen(true)}
              >
                <MenuIcon />
              </IconButton>
            )}
            <Typography variant="h6" sx={{ fontWeight: 700 }} color="primary.main">
              BIMS
            </Typography>
          </Box>
          <Box sx={{ display: "flex", alignItems: "center", gap: { xs: 1, sm: 2 } }}>
            {user && !isMobile && <Chip size="small" label={ROLE_LABELS[user.role] ?? user.role} />}
            {!isMobile && (
              <Typography variant="body2">
                {user?.first_name} {user?.last_name}
              </Typography>
            )}
            <IconButton onClick={() => navigate("/profile")} size="small" aria-label="View profile">
              <Avatar sx={{ width: 32, height: 32 }}>{user?.first_name?.[0]}</Avatar>
            </IconButton>
            <IconButton onClick={handleLogout} size="small" aria-label="Logout">
              <LogoutIcon fontSize="small" />
            </IconButton>
          </Box>
        </Toolbar>
      </AppBar>

      {isMobile ? (
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={() => setMobileOpen(false)}
          ModalProps={{ keepMounted: true }}
          sx={{ [`& .MuiDrawer-paper`]: { width: DRAWER_WIDTH, boxSizing: "border-box" } }}
        >
          <Toolbar />
          {navList}
        </Drawer>
      ) : (
        <Drawer
          variant="permanent"
          sx={{
            width: currentWidth,
            flexShrink: 0,
            [`& .MuiDrawer-paper`]: { width: currentWidth, boxSizing: "border-box", overflowX: "hidden" },
          }}
        >
          <Toolbar />
          {navList}
        </Drawer>
      )}

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: { xs: 2, sm: 3 },
          bgcolor: "background.default",
          minWidth: 0,
          width: { xs: "100%", sm: `calc(100% - ${currentWidth}px)` },
        }}
      >
        <Toolbar />
        {children}
      </Box>
    </Box>
  );
}
