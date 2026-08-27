import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { DeletionCheck } from "../types/deletion";

interface UsePermanentDeleteOptions<T> {
  /** Query key to invalidate after a successful deletion. */
  invalidateKey: string;
  /** Pre-flight blocker check. */
  check: (id: number) => Promise<DeletionCheck>;
  /** The destructive call itself. */
  remove: (id: number) => Promise<void>;
  /** How to label the record in the dialog (must be typed to confirm). */
  getName: (entity: T) => string;
  /** How to identify the record. */
  getId: (entity: T) => number;
}

/**
 * Task 5 — shared state machine for the permanent-deletion flow, so all six
 * admin pages behave identically: open dialog → run the blocker check →
 * require typed confirmation → delete → invalidate the list.
 *
 * The blocker check runs as its own query (enabled only while the dialog is
 * open) so the Administrator sees *why* something can't be deleted before
 * committing to it, rather than only discovering it from a failed request.
 */
export function usePermanentDelete<T>({
  invalidateKey,
  check,
  remove,
  getName,
  getId,
}: UsePermanentDeleteOptions<T>) {
  const queryClient = useQueryClient();
  const [target, setTarget] = useState<T | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const { data: deletionCheck, isLoading: checkLoading } = useQuery({
    queryKey: [invalidateKey, "deletion-check", target ? getId(target) : null],
    queryFn: () => check(getId(target as T)),
    enabled: target !== null,
  });

  const mutation = useMutation({
    mutationFn: (entity: T) => remove(getId(entity)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [invalidateKey] });
      setTarget(null);
      setErrorMessage(null);
    },
    onError: (err: unknown) => {
      // The backend's 409 carries a specific explanation of what is blocking
      // the deletion — surface it verbatim rather than a generic message.
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setErrorMessage(detail ?? "Failed to delete. Please try again.");
    },
  });

  return {
    target,
    open: target !== null,
    name: target ? getName(target) : "",
    deletionCheck: target ? (deletionCheck ?? null) : null,
    checkLoading: target !== null && checkLoading,
    loading: mutation.isPending,
    errorMessage,
    start: (entity: T) => {
      setErrorMessage(null);
      setTarget(entity);
    },
    cancel: () => {
      setTarget(null);
      setErrorMessage(null);
    },
    confirm: () => {
      if (target) mutation.mutate(target);
    },
  };
}
