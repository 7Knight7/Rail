import { apiRequest, getCsrfToken } from "./client";

export interface UploadResponse {
  id: string;
  filename: string;
  original_filename: string;
  size: number;
  content_type: string | null;
  uploaded_at: string;
  uploaded_by: string;
}

export async function uploadDatasetFile(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const headers: Record<string, string> = {};
  const csrfToken = getCsrfToken();
  if (csrfToken) {
    headers["X-CSRF-Token"] = csrfToken;
  }

  const response = await fetch("/api/v1/uploads", {
    method: "POST",
    credentials: "include",
    headers,
    body: formData,
  });

  if (!response.ok) {
    let message = "Upload failed";
    try {
      const errorData = await response.json();
      message = errorData.detail || message;
    } catch {
      message = await response.text();
    }
    throw new Error(message);
  }

  return response.json() as Promise<UploadResponse>;
}
