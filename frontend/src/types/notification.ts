export interface Notification {
  id: number;
  user_id: number;
  title: string;
  message: string;
  related_intervention_id: number | null;
  read: boolean;
  created_at: string;
}
