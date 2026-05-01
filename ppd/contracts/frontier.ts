export type FrontierContentType =
  | "html"
  | "pdf"
  | "image"
  | "downloadable_document"
  | "external_site"
  | "mailto"
  | "phone"
  | "portal_action"
  | "other";

export type FrontierLinkRelation =
  | "same_site"
  | "download"
  | "external_reference"
  | "contact"
  | "portal_action"
  | "unknown";

export type SkippedUrlReason =
  | "duplicate_url"
  | "disallowed_domain"
  | "unsupported_scheme"
  | "fragment_only"
  | "private_or_authenticated"
  | "non_public_action"
  | "content_type_unsupported"
  | "robots_not_prechecked"
  | "malformed_url";

export interface DiscoveredFrontierLink {
  id: string;
  sourceUrl: string;
  rawHref: string;
  normalizedUrl: string;
  label: string;
  contentType: FrontierContentType;
  relation: FrontierLinkRelation;
  allowedDomain: boolean;
  crawlCandidate: boolean;
  evidenceSelector?: string;
}

export interface SkippedFrontierUrl {
  id: string;
  sourceUrl: string;
  rawHref: string;
  normalizedUrl: string;
  reason: SkippedUrlReason;
  contentType: FrontierContentType;
  label?: string;
  evidenceSelector?: string;
  note?: string;
}

export interface FrontierExpansionSummary {
  totalLinksSeen: number;
  discoveredCount: number;
  skippedCount: number;
  crawlCandidateCount: number;
  contentTypeCounts: Record<string, number>;
  skippedReasonCounts: Partial<Record<SkippedUrlReason, number>>;
}

export interface FrontierExpansion {
  fixtureId: string;
  sourceDocumentId: string;
  sourceUrl: string;
  expandedAt: string;
  allowedDomains: string[];
  discoveredLinks: DiscoveredFrontierLink[];
  skippedUrls: SkippedFrontierUrl[];
  summary: FrontierExpansionSummary;
}

export function validateFrontierExpansion(expansion: FrontierExpansion): string[] {
  const errors: string[] = [];
  if (!expansion.fixtureId.trim()) errors.push("fixtureId is required");
  if (!expansion.sourceDocumentId.trim()) errors.push("sourceDocumentId is required");
  if (!expansion.sourceUrl.startsWith("https://")) errors.push("sourceUrl must be HTTPS");
  if (!expansion.expandedAt.endsWith("Z")) errors.push("expandedAt must end in Z");
  if (!Array.isArray(expansion.allowedDomains) || expansion.allowedDomains.length === 0) {
    errors.push("at least one allowedDomain is required");
  }

  const discoveredIds = new Set<string>();
  for (const link of expansion.discoveredLinks || []) {
    if (!link.id.trim()) errors.push("discovered link id is required");
    if (discoveredIds.has(link.id)) errors.push(`duplicate discovered link id ${link.id}`);
    discoveredIds.add(link.id);
    if (!link.sourceUrl.startsWith("https://")) errors.push(`discovered link ${link.id} sourceUrl must be HTTPS`);
    if (!link.rawHref.trim()) errors.push(`discovered link ${link.id} rawHref is required`);
    if (!link.normalizedUrl.trim()) errors.push(`discovered link ${link.id} normalizedUrl is required`);
    if (!link.label.trim()) errors.push(`discovered link ${link.id} label is required`);
    if (link.crawlCandidate && !link.allowedDomain) {
      errors.push(`discovered link ${link.id} cannot be a crawl candidate outside allowed domains`);
    }
    if (["mailto", "phone", "external_site"].includes(link.contentType) && link.crawlCandidate) {
      errors.push(`discovered link ${link.id} contact/external links are not crawl candidates`);
    }
  }

  const skippedIds = new Set<string>();
  for (const skipped of expansion.skippedUrls || []) {
    if (!skipped.id.trim()) errors.push("skipped URL id is required");
    if (skippedIds.has(skipped.id)) errors.push(`duplicate skipped URL id ${skipped.id}`);
    skippedIds.add(skipped.id);
    if (!skipped.sourceUrl.startsWith("https://")) errors.push(`skipped URL ${skipped.id} sourceUrl must be HTTPS`);
    if (!skipped.rawHref.trim()) errors.push(`skipped URL ${skipped.id} rawHref is required`);
    if (!skipped.normalizedUrl.trim()) errors.push(`skipped URL ${skipped.id} normalizedUrl is required`);
    if (skipped.reason === "disallowed_domain" && skipped.contentType !== "external_site") {
      errors.push(`skipped URL ${skipped.id} disallowed-domain skips should be classified as external_site`);
    }
    if (skipped.reason === "private_or_authenticated" && skipped.contentType !== "portal_action") {
      errors.push(`skipped URL ${skipped.id} private/authenticated skips should be classified as portal_action`);
    }
  }

  const summary = expansion.summary;
  if (!summary) {
    errors.push("summary is required");
  } else {
    if (summary.totalLinksSeen !== summary.discoveredCount + summary.skippedCount) {
      errors.push("totalLinksSeen must equal discoveredCount plus skippedCount");
    }
    if (summary.discoveredCount !== expansion.discoveredLinks.length) {
      errors.push("summary discoveredCount does not match discoveredLinks");
    }
    if (summary.skippedCount !== expansion.skippedUrls.length) {
      errors.push("summary skippedCount does not match skippedUrls");
    }
    const crawlCandidateCount = expansion.discoveredLinks.filter((link) => link.crawlCandidate).length;
    if (summary.crawlCandidateCount !== crawlCandidateCount) {
      errors.push("summary crawlCandidateCount does not match discoveredLinks");
    }
  }
  return errors;
}
