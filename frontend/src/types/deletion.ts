/** Task 5 — result of the pre-flight permanent-deletion safety check. */
export interface DeletionBlocker {
  /** Human-readable reason, e.g. "interventions performed at this site". */
  label: string;
  count: number;
}

export interface DeletionCheck {
  deletable: boolean;
  blockers: DeletionBlocker[];
}
