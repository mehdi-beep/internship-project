import { useEffect, useState } from "react";
import { apiClient } from "../api/client";

/** Fetches an attachment through the authenticated axios client and exposes it as an object URL. */
export function useAuthenticatedPreview(attachmentId: number): string | null {
  const [url, setUrl] = useState<string | null>(null);

  useEffect(() => {
    let objectUrl: string | null = null;
    let cancelled = false;

    apiClient
      .get(`/attachments/${attachmentId}/download`, { responseType: "blob" })
      .then((res) => {
        if (cancelled) return;
        objectUrl = URL.createObjectURL(res.data as Blob);
        setUrl(objectUrl);
      })
      .catch(() => setUrl(null));

    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [attachmentId]);

  return url;
}
