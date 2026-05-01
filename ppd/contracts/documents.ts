export type PpdContentType = "html" | "pdf" | "image" | "form" | "other";

export type PpdDocumentRole =
  | "guidance"
  | "application"
  | "checklist"
  | "handout"
  | "faq"
  | "portal_reference"
  | "unknown";

export interface SourceLink {
  url: string;
  label: string;
  relation?: "same_site" | "download" | "external_reference" | "portal_action" | "contact" | "unknown";
  contentTypeHint?: PpdContentType;
}

export interface ExtractedField {
  id: string;
  label: string;
  fieldType: "text" | "number" | "date" | "checkbox" | "radio" | "select" | "signature" | "file" | "unknown";
  required: boolean;
  options?: string[];
  pageNumber?: number;
  evidenceText?: string;
}

export interface PageAnchor {
  id: string;
  label: string;
  pageNumber?: number;
  selector?: string;
  textOffset?: number;
}

export interface DocumentSection {
  id: string;
  heading: string;
  level: number;
  text: string;
  pageNumber?: number;
  anchorId?: string;
}

export interface DocumentOrderedStep {
  id: string;
  sequence: number;
  text: string;
  pageNumber?: number;
  anchorId?: string;
  evidenceSelector?: string;
}

export interface DocumentTable {
  id: string;
  caption?: string;
  headers: string[];
  rows: string[][];
  pageNumber?: number;
  anchorId?: string;
}

export interface ModifiedDateEvidence {
  dateText: string;
  evidenceText: string;
  evidenceSelector?: string;
}

export interface ScrapedDocument {
  id: string;
  sourceUrl: string;
  canonicalUrl: string;
  contentType: PpdContentType;
  title: string;
  fetchedAt: string;
  contentHash: string;
  text: string;
  links: SourceLink[];
  extractedFields?: ExtractedField[];
  pageAnchors?: PageAnchor[];
}

export interface NormalizedDocument extends ScrapedDocument {
  documentRole: PpdDocumentRole;
  normalizedAt: string;
  sourceFamily?: "portland_gov_ppd" | "portland_gov_devhub_guidance" | "devhub_public_portal" | "portlandoregon_legacy_reference" | "portland_maps_public_reference" | "unknown";
  sections: DocumentSection[];
  orderedSteps?: DocumentOrderedStep[];
  tables: DocumentTable[];
  modifiedDateEvidence?: ModifiedDateEvidence[];
  warnings: string[];
}

export function validateScrapedDocument(document: ScrapedDocument): string[] {
  const errors: string[] = [];
  if (!document.id.trim()) errors.push("id is required");
  if (!document.sourceUrl.startsWith("https://")) errors.push("sourceUrl must be HTTPS");
  if (!document.canonicalUrl.startsWith("https://")) errors.push("canonicalUrl must be HTTPS");
  if (!document.title.trim()) errors.push("title is required");
  if (!document.fetchedAt.trim()) errors.push("fetchedAt is required");
  if (!document.contentHash.trim()) errors.push("contentHash is required");
  if (!Array.isArray(document.links)) errors.push("links must be an array");
  return errors;
}

export function validateNormalizedDocument(document: NormalizedDocument): string[] {
  const errors = validateScrapedDocument(document);
  if (!document.normalizedAt.trim()) errors.push("normalizedAt is required");
  if (!Array.isArray(document.sections)) errors.push("sections must be an array");
  if (document.orderedSteps && !Array.isArray(document.orderedSteps)) errors.push("orderedSteps must be an array");
  if (!Array.isArray(document.tables)) errors.push("tables must be an array");
  if (document.modifiedDateEvidence && !Array.isArray(document.modifiedDateEvidence)) errors.push("modifiedDateEvidence must be an array");
  if (!Array.isArray(document.warnings)) errors.push("warnings must be an array");
  return errors;
}
