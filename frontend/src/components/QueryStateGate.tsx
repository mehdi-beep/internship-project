import type { ReactNode } from "react";
import { Alert, Box, Button, CircularProgress } from "@mui/material";
import { Navigate } from "react-router-dom";

interface QueryStateGateProps {
  isLoading: boolean;
  isError: boolean;
  error?: unknown;
  onRetry?: () => void;
  notFoundMessage?: string;
  children: ReactNode;
}

/**
 * Ch.99/101 — the standard loading/error tri-state for a page's primary query.
 * A 403 redirects to the shared Forbidden page; anything else (including a
 * 404, network drop, or 500) shows a clear message instead of leaving the
 * page stuck on a spinner forever, which is what `isLoading || !data` alone
 * does once a query settles into an error (isLoading becomes false, but data
 * never arrives, so a component gating on `!data` renders its "loading"
 * branch indefinitely with no way out).
 */
export default function QueryStateGate({
  isLoading,
  isError,
  error,
  onRetry,
  notFoundMessage = "The requested data could not be found.",
  children,
}: QueryStateGateProps) {
  if (isLoading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (isError) {
    const status = (error as { response?: { status?: number } })?.response?.status;
    if (status === 403) {
      return <Navigate to="/403" replace />;
    }
    const message =
      status === 404
        ? notFoundMessage
        : status && status >= 500
          ? "Server unavailable. Please try again later."
          : "Connection lost. Please check your network and try again.";
    return (
      <Alert
        severity="error"
        action={
          onRetry && (
            <Button color="inherit" size="small" onClick={onRetry}>
              Retry
            </Button>
          )
        }
      >
        {message}
      </Alert>
    );
  }

  return <>{children}</>;
}
