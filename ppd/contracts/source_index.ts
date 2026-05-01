export type CrawlStatus = "fetched" | "not_modified" | "skipped" | "failed";

export type SourcePageType =
  | "guidance"
  | "form_index"
  | "faq"
  | "portal_reference"
  | "public_search_reference"
  | "pdf"
  | "other";

export interface RedirectHop {
  fromUrl: string;
  toUrl: string;
  statusCode: 301 | 302 | 303 | 307 | 308;
  observedAt: string;
}

export interface SourceIndexRecord {
  id: string;
  sourceUrl: string;
  canonicalUrl: string;
  title: string;
  bureau: string;
  pageType: SourcePageType;
  contentType: string;
  firstSeenAt: string;
  lastSeenAt: string;
  crawlStatus: CrawlStatus;
  redirects: RedirectHop[];
  fetchedAt?: string;
  httpStatus?: number;
  etag?: string;
  lastModified?: string;
  contentHash?: string;
  skipReason?: string;
  failureReason?: string;
}

const REDIRECT_CODES = new Set([301, 302, 303, 307, 308]);
const HASH_RE = /^sha256:[0-9a-f]{64}$/;

export function validateSourceIndexRecord(record: SourceIndexRecord): string[] {
  const errors: string[] = [];
  if (!record.id.trim()) errors.push("id is required");
  if (!record.sourceUrl.startsWith("https://")) errors.push("sourceUrl must be HTTPS");
  if (!record.canonicalUrl.startsWith("https://")) errors.push("canonicalUrl must be HTTPS");
  if (!record.title.trim()) errors.push("title is required");
  if (!record.bureau.trim()) errors.push("bureau is required");
  if (!record.contentType.includes("/")) errors.push("contentType must be MIME-like");
  if (!record.firstSeenAt.endsWith("Z")) errors.push("firstSeenAt must end in Z");
  if (!record.lastSeenAt.endsWith("Z")) errors.push("lastSeenAt must end in Z");
  if (record.fetchedAt && !record.fetchedAt.endsWith("Z")) errors.push("fetchedAt must end in Z");

  for (const redirect of record.redirects || []) {
    if (!redirect.fromUrl.startsWith("https://")) errors.push("redirect fromUrl must be HTTPS");
    if (!redirect.toUrl.startsWith("https://")) errors.push("redirect toUrl must be HTTPS");
    if (!REDIRECT_CODES.has(redirect.statusCode)) errors.push("redirect statusCode must be an HTTP redirect code");
    if (!redirect.observedAt.endsWith("Z")) errors.push("redirect observedAt must end in Z");
  }

  if (record.redirects.length > 0) {
    if (record.redirects[0].fromUrl !== record.sourceUrl) errors.push("first redirect must start at sourceUrl");
    if (record.redirects[record.redirects.length - 1].toUrl !== record.canonicalUrl) {
      errors.push("last redirect must end at canonicalUrl");
    }
  } else if (record.sourceUrl !== record.canonicalUrl) {
    errors.push("redirects are required when sourceUrl differs from canonicalUrl");
  }

  if (record.crawlStatus === "fetched" || record.crawlStatus === "not_modified") {
    if (!record.fetchedAt) errors.push(`${record.crawlStatus} records require fetchedAt`);
    if (record.httpStatus !== 200 && record.httpStatus !== 304) {
      errors.push(`${record.crawlStatus} records require httpStatus 200 or 304`);
    }
    if (!record.contentHash || !HASH_RE.test(record.contentHash)) {
      errors.push(`${record.crawlStatus} records require sha256 contentHash`);
    }
  }
  if (record.crawlStatus === "not_modified" && record.httpStatus !== 304) {
    errors.push("not_modified records require httpStatus 304");
  }
  if (record.crawlStatus === "skipped" && !record.skipReason?.trim()) errors.push("skipped records require skipReason");
  if (record.crawlStatus === "failed" && !record.failureReason?.trim()) errors.push("failed records require failureReason");
  return errors;
}
