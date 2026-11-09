export function base64url(bytes) {
  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_';
  let value = '';
  for (let i = 0; i < bytes.length; i += 3) {
    const n = (bytes[i] << 16) | ((bytes[i + 1] || 0) << 8) | (bytes[i + 2] || 0);
    value += alphabet[(n >>> 18) & 63] + alphabet[(n >>> 12) & 63];
    if (i + 1 < bytes.length) value += alphabet[(n >>> 6) & 63];
    if (i + 2 < bytes.length) value += alphabet[n & 63];
  }
  return value;
}

export async function encryptPayload(request, publicJwk) {
  if (!globalThis.crypto?.subtle || !publicJwk || publicJwk.kty !== 'RSA' || publicJwk.d) throw new Error('Transporte privado indisponível.');
  const bytes = new TextEncoder();
  const rsa = await crypto.subtle.importKey('jwk', publicJwk, { name: 'RSA-OAEP', hash: 'SHA-256' }, false, ['encrypt']);
  if (rsa.algorithm.modulusLength < 2048) throw new Error('Chave de transporte inválida.');
  const aes = await crypto.subtle.generateKey({ name: 'AES-GCM', length: 256 }, true, ['encrypt']);
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const rawKey = await crypto.subtle.exportKey('raw', aes);
  const wrapped = await crypto.subtle.encrypt({ name: 'RSA-OAEP' }, rsa, rawKey);
  const plaintext = bytes.encode(JSON.stringify({ ...request, issued_at: Math.floor(Date.now() / 1000) }));
  const encrypted = await crypto.subtle.encrypt({ name: 'AES-GCM', iv, additionalData: bytes.encode('IC-dispatch-v1'), tagLength: 128 }, aes, plaintext);
  return JSON.stringify({ v: 1, key: base64url(new Uint8Array(wrapped)), iv: base64url(iv), data: base64url(new Uint8Array(encrypted)) });
}
