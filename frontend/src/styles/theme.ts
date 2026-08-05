import { createTheme } from "@mui/material/styles";
import type { InterventionStatus, Priority } from "../types/enums";

export const statusColors: Record<InterventionStatus, string> = {
  draft: "#9e9e9e",
  planned: "#1976d2",
  in_progress: "#4fc3f7",
  submitted: "#ff9800",
  pending_technical_approval: "#fbc02d",
  technical_approved: "#8bc34a",
  pending_administrative_approval: "#9c27b0",
  fully_approved: "#2e7d32",
  rejected: "#d32f2f",
};

export const priorityColors: Record<Priority, string> = {
  normal: "#1976d2",
  high: "#ff9800",
  urgent: "#c62828",
};

export const theme = createTheme({
  palette: {
    mode: "light",
    primary: {
      main: "#1e3a5f",
    },
    secondary: {
      main: "#0097a7",
    },
    background: {
      default: "#f4f6f8",
      paper: "#ffffff",
    },
    error: { main: "#d32f2f" },
    warning: { main: "#ed6c02" },
    success: { main: "#2e7d32" },
  },
  typography: {
    fontFamily: ['"Inter"', "Roboto", '"Helvetica Neue"', "Arial", "sans-serif"].join(","),
    h1: { fontWeight: 600 },
    h2: { fontWeight: 600 },
    h3: { fontWeight: 600 },
    h4: { fontWeight: 600 },
    h5: { fontWeight: 600 },
    h6: { fontWeight: 600 },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      defaultProps: { disableElevation: true },
      styleOverrides: { root: { textTransform: "none", fontWeight: 500 } },
    },
    MuiCard: {
      styleOverrides: { root: { borderRadius: 12 } },
    },
    MuiAppBar: {
      styleOverrides: { root: { boxShadow: "none", borderBottom: "1px solid #e0e0e0" } },
    },
  },
});
