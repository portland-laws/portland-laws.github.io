export function normalizeWhitespace(value: string): string {
  return value.trim().replace(/\s+/g, ' ');
}

export function normalizePredicateName(value: string): string {
  const normalized = value
    .trim()
    .replace(/([a-z0-9])([A-Z])/g, '$1_$2')
    .replace(/[^A-Za-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .toLowerCase();

  if (!normalized) {
    return 'unknown';
  }

  if (/^[0-9]/.test(normalized)) {
    return `p_${normalized}`;
  }

  return normalized;
}

export function normalizePortlandIdentifier(value: string): string {
  const normalized = normalizeWhitespace(value)
    .replace(/^pcc\s+/i, 'Portland City Code ')
    .replace(/^portland\s+code\s+/i, 'Portland City Code ')
    .replace(/^portland\s+city\s+code\s+/i, 'Portland City Code ')
    .replace(/\s+/g, ' ');

  const citation = normalized.match(/(\d+)\.(\d+)\.(\d+)/);
  if (!citation) {
    return normalized;
  }

  return `Portland City Code ${citation[1]}.${citation[2]}.${citation[3]}`;
}

export function portlandIdentifierToObjectId(value: string): string {
  const identifier = normalizePortlandIdentifier(value);
  const citation = identifier.match(/(\d+)\.(\d+)\.(\d+)/);
  if (!citation) {
    return normalizePredicateName(identifier);
  }
  return `portland_city_code_${citation[1]}_${citation[2]}_${citation[3]}`;
}

export function objectIdToPortlandIdentifier(value: string): string | null {
  const match = value.match(/portland_city_code_(\d+)_(\d+)_(\d+)/i);
  if (!match) {
    return null;
  }
  return `Portland City Code ${match[1]}.${match[2]}.${match[3]}`;
}

