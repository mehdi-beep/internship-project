export interface Notification {
  id: number;
  // Task 5: nullable — permanently deleting the recipient detaches (never
  // deletes) the notification; deleted_user_label carries their name
  // forward. In practice a deleted recipient can never authenticate to
  // fetch this again, so this field exists for completeness only.
  user_id: number | null;
  deleted_user_label?: string | null;
  title: string;
  message: string;
  related_intervention_id: number | null;
  related_planning_id: number | null;
  read: boolean;
  created_at: string;
}
