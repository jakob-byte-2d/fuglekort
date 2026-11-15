// Hagefugler: sender varslene som ligger i køen (varsel_ko) til telefonene, med Web Push (RFC 8291 og 8292).
// Ingen biblioteker: bare WebCrypto og fetch. Lager nøkkelparet (VAPID) første gang og lagrer det i varsel_nokler.
// Kalles av databasen (varsel_send, hvert tiende minutt når noe venter, og ved testvarsler). Slå av «Verify JWT».
// Funksjonen sender bare det som alt ligger i køen, så det gjør ikke noe om andre kaller den.

const enc = new TextEncoder();
const b64u = (b: ArrayBuffer | Uint8Array) => btoa(String.fromCharCode(...new Uint8Array(b))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
const fraB64u = (s: string) => Uint8Array.from(atob(s.replace(/-/g, '+').replace(/_/g, '/') + '='.repeat((4 - (s.length % 4)) % 4)), c => c.charCodeAt(0));
const slaSammen = (...d: Uint8Array[]) => { const u = new Uint8Array(d.reduce((a, x) => a + x.length, 0)); let i = 0; for (const x of d) { u.set(x, i); i += x.length; } return u; };

async function hkdf(salt: Uint8Array, ikm: Uint8Array, info: Uint8Array, lengde: number) {
  const k = await crypto.subtle.importKey('raw', ikm, 'HKDF', false, ['deriveBits']);
  return new Uint8Array(await crypto.subtle.deriveBits({ name: 'HKDF', hash: 'SHA-256', salt, info }, k, lengde * 8));
}

// RFC 8291: innholdet kryptert til telefonens nøkkel (p256dh) og hemmelighet (auth), aes128gcm, én post
export async function krypter(p256dh: string, auth: string, tekst: Uint8Array, salt = crypto.getRandomValues(new Uint8Array(16))) {
  const uaOff = fraB64u(p256dh), hemmelig = fraB64u(auth);
  const ua = await crypto.subtle.importKey('raw', uaOff, { name: 'ECDH', namedCurve: 'P-256' }, false, []);
  const as = await crypto.subtle.generateKey({ name: 'ECDH', namedCurve: 'P-256' }, true, ['deriveBits']);
  const asOff = new Uint8Array(await crypto.subtle.exportKey('raw', as.publicKey));
  const delt = new Uint8Array(await crypto.subtle.deriveBits({ name: 'ECDH', public: ua }, as.privateKey, 256));
  const ikm = await hkdf(hemmelig, delt, slaSammen(enc.encode('WebPush: info\0'), uaOff, asOff), 32);
  const cek = await hkdf(salt, ikm, enc.encode('Content-Encoding: aes128gcm\0'), 16);
  const nonce = await hkdf(salt, ikm, enc.encode('Content-Encoding: nonce\0'), 12);
  const ak = await crypto.subtle.importKey('raw', cek, 'AES-GCM', false, ['encrypt']);
  const kryptert = new Uint8Array(await crypto.subtle.encrypt({ name: 'AES-GCM', iv: nonce }, ak, slaSammen(tekst, new Uint8Array([2]))));
  const rs = new Uint8Array([0, 0, 16, 0]);                                          // postlengde 4096
  return slaSammen(salt, rs, new Uint8Array([asOff.length]), asOff, kryptert);
}

// RFC 8292: VAPID, en JWT signert med den private nøkkelen, til push-tjenesten for adressen
export async function vapid(endpoint: string, privat: CryptoKey, offentlig: string, sub = 'https://fuglekort.no') {
  const h = b64u(enc.encode(JSON.stringify({ typ: 'JWT', alg: 'ES256' })));
  const c = b64u(enc.encode(JSON.stringify({ aud: new URL(endpoint).origin, exp: Math.floor(Date.now() / 1000) + 12 * 3600, sub })));
  const sig = await crypto.subtle.sign({ name: 'ECDSA', hash: 'SHA-256' }, privat, enc.encode(`${h}.${c}`));
  return `vapid t=${h}.${c}.${b64u(sig)}, k=${offentlig}`;
}

export async function lagNokler() {
  const k = await crypto.subtle.generateKey({ name: 'ECDSA', namedCurve: 'P-256' }, true, ['sign', 'verify']);
  return { offentlig: b64u(await crypto.subtle.exportKey('raw', k.publicKey)), privat: await crypto.subtle.exportKey('jwk', k.privateKey) };
}

// ett varsel: { tittel, tekst, url, tag } som JSON, til appens service worker (push-hendelsen)
export async function sendEtt(v: any, privat: CryptoKey, offentlig: string) {
  const data = await krypter(v.p256dh, v.auth, enc.encode(JSON.stringify({ tittel: v.tittel, tekst: v.tekst, url: v.url, tag: v.tag })));
  const r = await fetch(v.endpoint, {
    method: 'POST', body: data,
    headers: { Authorization: await vapid(v.endpoint, privat, offentlig), TTL: String(v.ttl || 86400), 'Content-Encoding': 'aes128gcm',
               'Content-Type': 'application/octet-stream', Urgency: 'normal' },
  });
  await r.body?.cancel();
  return r.status;
}

const env = (k: string) => (globalThis as any).Deno?.env.get(k);
function hemmeligNokkel() {
  const s = env('SUPABASE_SECRET_KEYS');
  if (s) { try { const j = JSON.parse(s); return j.default || Object.values(j)[0]; } catch (_) { /* den gamle */ } }
  return env('SUPABASE_SERVICE_ROLE_KEY');
}
async function rpc(fn: string, data: unknown = {}) {
  const nokkel = hemmeligNokkel();
  const r = await fetch(`${env('SUPABASE_URL')}/rest/v1/rpc/${fn}`, {
    method: 'POST', body: JSON.stringify(data),
    headers: { apikey: nokkel, ...(nokkel.startsWith('eyJ') ? { Authorization: `Bearer ${nokkel}` } : {}), 'Content-Type': 'application/json' },
  });
  if (!r.ok) throw new Error(`${fn}: ${r.status} ${await r.text()}`);
  const t = await r.text(); return t ? JSON.parse(t) : null;
}

export async function kjor() {
  let n = await rpc('varsler_nokler');
  if (!n) { const ny = await lagNokler(); n = await rpc('varsler_nokler', { p_offentlig: ny.offentlig, p_privat: ny.privat }); }
  const privat = await crypto.subtle.importKey('jwk', n.privat, { name: 'ECDSA', namedCurve: 'P-256' }, false, ['sign']);
  const ut = { sendt: 0, borte: 0, feil: 0 }, slutt = Date.now() + 100000;
  while (Date.now() < slutt) {
    const ko = await rpc('varsler_hent', { p_antall: 200 });
    if (!ko || !ko.length) break;
    const svar: { id: number; status: number }[] = [];
    for (let i = 0; i < ko.length; i += 20) {                                           // tjue om gangen
      await Promise.all(ko.slice(i, i + 20).map(async (v: any) => {
        let status = 0;
        try { status = await sendEtt(v, privat, n.offentlig); } catch (_) { status = 0; }
        svar.push({ id: v.id, status });
        if (status >= 200 && status < 300) ut.sendt++; else if (status === 404 || status === 410) ut.borte++; else ut.feil++;
      }));
    }
    await rpc('varsler_ferdig', { p_svar: svar });
  }
  return ut;
}

if ((globalThis as any).Deno?.serve) {
  (globalThis as any).Deno.serve(async () => {
    try { return Response.json({ ok: true, ...(await kjor()) }); }
    catch (e) { console.error(e); return Response.json({ ok: false, feil: String(e) }, { status: 500 }); }
  });
}
