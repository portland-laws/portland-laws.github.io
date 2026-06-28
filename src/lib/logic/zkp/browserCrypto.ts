export interface BrowserCryptoDigest {
  digest(algorithm: 'SHA-256', data: Uint8Array): Promise<ArrayBuffer>;
}

export interface BrowserCryptoOptions {
  crypto?: BrowserCryptoDigest;
}

export function resolveBrowserCryptoDigest(
  options: BrowserCryptoOptions = {},
): BrowserCryptoDigest {
  if (options.crypto !== undefined) {
    return options.crypto;
  }
  const subtle = globalThis.crypto?.subtle;
  if (subtle === undefined) {
    throw new Error(
      'Web Crypto subtle.digest is required; no server crypto fallback is available.',
    );
  }
  return {
    digest: (algorithm, data) => subtle.digest(algorithm, data),
  };
}

export async function sha256Digest(
  data: Uint8Array,
  options: BrowserCryptoOptions = {},
): Promise<Uint8Array> {
  const digest = await resolveBrowserCryptoDigest(options).digest('SHA-256', data);
  return new Uint8Array(digest);
}

export async function sha256Hex(
  data: Uint8Array,
  options: BrowserCryptoOptions = {},
): Promise<string> {
  return bytesToHex(await sha256Digest(data, options));
}

export function bytesToHex(bytes: Uint8Array): string {
  return [...bytes].map((byte) => byte.toString(16).padStart(2, '0')).join('');
}
