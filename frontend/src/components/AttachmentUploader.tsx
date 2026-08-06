import { useRef, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardActions,
  CardContent,
  CircularProgress,
  Stack,
  Typography,
} from "@mui/material";
import PhotoCameraIcon from "@mui/icons-material/PhotoCameraOutlined";
import UploadFileIcon from "@mui/icons-material/UploadFileOutlined";
import DeleteIcon from "@mui/icons-material/DeleteOutlined";
import PictureAsPdfIcon from "@mui/icons-material/PictureAsPdfOutlined";
import { useAuthenticatedPreview } from "../hooks/useAuthenticatedPreview";
import type { Attachment } from "../types/intervention";

const ACCEPTED = "image/jpeg,image/png,application/pdf";
const MAX_BYTES = 10 * 1024 * 1024;

interface AttachmentUploaderProps {
  attachments: Attachment[];
  onUpload: (file: File) => Promise<void>;
  onDelete: (attachmentId: number) => Promise<void>;
  readOnly?: boolean;
  /** Opens the full-screen review viewer at this attachment's index when the thumbnail is clicked. */
  onImageClick?: (attachmentIndex: number) => void;
}

function AttachmentCard({
  attachment,
  onDelete,
  readOnly,
  onClick,
}: {
  attachment: Attachment;
  onDelete: (id: number) => Promise<void>;
  readOnly: boolean;
  onClick?: () => void;
}) {
  const previewUrl = useAuthenticatedPreview(attachment.id);
  const isPdf = attachment.content_type === "application/pdf";

  return (
    <Card variant="outlined" sx={{ width: 200 }}>
      <Box
        onClick={onClick}
        sx={{
          height: 140,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          bgcolor: "action.hover",
          overflow: "hidden",
          cursor: onClick ? "pointer" : "default",
        }}
      >
        {isPdf ? (
          <PictureAsPdfIcon sx={{ fontSize: 48, color: "text.secondary" }} />
        ) : previewUrl ? (
          <Box component="img" src={previewUrl} alt={attachment.file_name} sx={{ maxWidth: "100%", maxHeight: "100%" }} />
        ) : (
          <CircularProgress size={24} />
        )}
      </Box>
      <CardContent sx={{ py: 1 }}>
        <Typography variant="caption" noWrap title={attachment.file_name} sx={{ display: "block" }}>
          {attachment.file_name}
        </Typography>
      </CardContent>
      {!readOnly && (
        <CardActions sx={{ pt: 0 }}>
          <Button size="small" color="error" startIcon={<DeleteIcon />} onClick={() => onDelete(attachment.id)}>
            Delete
          </Button>
        </CardActions>
      )}
    </Card>
  );
}

export default function AttachmentUploader({
  attachments,
  onUpload,
  onDelete,
  readOnly = false,
  onImageClick,
}: AttachmentUploaderProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const file = files[0];
    setError(null);

    if (!ACCEPTED.split(",").includes(file.type)) {
      setError("Unsupported file type. Allowed formats: JPG, JPEG, PNG, PDF.");
      return;
    }
    if (file.size > MAX_BYTES) {
      setError("File exceeds the maximum allowed size of 10 MB.");
      return;
    }

    setBusy(true);
    try {
      await onUpload(file);
    } catch {
      setError("Upload failed. Please try again.");
    } finally {
      setBusy(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
      if (cameraInputRef.current) cameraInputRef.current.value = "";
    }
  };

  return (
    <Stack spacing={2}>
      {error && <Alert severity="error">{error}</Alert>}

      {!readOnly && (
        <Stack direction="row" spacing={1}>
          <Button
            variant="outlined"
            startIcon={<PhotoCameraIcon />}
            disabled={busy}
            onClick={() => cameraInputRef.current?.click()}
          >
            Take Photo
          </Button>
          <Button
            variant="outlined"
            startIcon={<UploadFileIcon />}
            disabled={busy}
            onClick={() => fileInputRef.current?.click()}
          >
            Upload Image
          </Button>
          {busy && <CircularProgress size={24} sx={{ alignSelf: "center" }} />}
          <input
            ref={cameraInputRef}
            type="file"
            accept="image/*"
            capture="environment"
            hidden
            onChange={(e) => handleFiles(e.target.files)}
          />
          <input
            ref={fileInputRef}
            type="file"
            accept={ACCEPTED}
            hidden
            onChange={(e) => handleFiles(e.target.files)}
          />
        </Stack>
      )}

      {attachments.length === 0 ? (
        <Typography variant="body2" color="text.secondary">
          No attachments yet. At least one image of the signed paper BI is required before submitting.
        </Typography>
      ) : (
        <Stack direction="row" spacing={2} sx={{ flexWrap: "wrap", gap: 2 }}>
          {attachments.map((attachment, index) => (
            <AttachmentCard
              key={attachment.id}
              attachment={attachment}
              onDelete={onDelete}
              readOnly={readOnly}
              onClick={onImageClick ? () => onImageClick(index) : undefined}
            />
          ))}
        </Stack>
      )}
    </Stack>
  );
}
