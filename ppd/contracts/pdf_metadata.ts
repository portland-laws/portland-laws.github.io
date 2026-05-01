export type PdfFieldKind = "text" | "checkbox" | "radio" | "select" | "signature" | "date" | "money" | "unknown";

export interface PdfPageText {
  id: string;
  pageNumber: number;
  text: string;
  textHash: string;
}

export interface PdfFormField {
  id: string;
  label: string;
  kind: PdfFieldKind;
  pageNumber: number;
  required: boolean;
  evidenceText: string;
  options?: string[];
}

export interface PdfCheckboxHint {
  id: string;
  label: string;
  pageNumber: number;
  checkedByDefault?: boolean;
  evidenceText: string;
}

export interface PdfSignatureHint {
  id: string;
  label: string;
  pageNumber: number;
  required: boolean;
  signerRole: string;
  evidenceText: string;
}

export interface PdfFeeTableHint {
  id: string;
  pageNumber: number;
  caption: string;
  headers: string[];
  rowCount: number;
  evidenceText: string;
}

export interface PdfNormalizedDocumentMetadata {
  documentId: string;
  sourceUrl: string;
  canonicalUrl: string;
  title: string;
  pageCount: number;
  capturedAt: string;
  extractionMode: "fixture_only";
  pageText: PdfPageText[];
  formFields: PdfFormField[];
  checkboxHints: PdfCheckboxHint[];
  signatureHints: PdfSignatureHint[];
  feeTableHints: PdfFeeTableHint[];
  warnings: string[];
  liveDownloadPerformed: boolean;
}

export function validatePdfNormalizedDocumentMetadata(document: PdfNormalizedDocumentMetadata): string[] {
  const errors: string[] = [];
  if (!document.documentId.trim()) errors.push("documentId is required");
  if (!document.sourceUrl.startsWith("https://")) errors.push("sourceUrl must be HTTPS");
  if (!document.canonicalUrl.startsWith("https://")) errors.push("canonicalUrl must be HTTPS");
  if (!document.title.trim()) errors.push("title is required");
  if (document.pageCount < 1) errors.push("pageCount must be positive");
  if (!document.capturedAt.endsWith("Z")) errors.push("capturedAt must end in Z");
  if (document.extractionMode !== "fixture_only") errors.push("extractionMode must be fixture_only");
  if (document.liveDownloadPerformed) errors.push("fixture metadata must not perform live downloads");
  return errors;
}
