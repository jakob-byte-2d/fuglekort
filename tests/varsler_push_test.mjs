// Edge-funksjonen send-varsler (supabase/functions/send-varsler/index.ts) mot en falsk Supabase og en falsk
// push-tjeneste på localhost: nøklene lages og lagres, varslene krypteres (RFC 8291) så telefonen kan lese dem
// (dekryptert med http_ece), VAPID-signaturen (RFC 8292) stemmer, 410 meldes tilbake.
// Kjør (pakken må ligge ved siden av fila):  mkdir -p /tmp/wp && cd /tmp/wp && npm install http_ece
//        cp REPO/tests/varsler_push_test.mjs . && node --experimental-strip-types --no-warnings varsler_push_test.mjs REPO
import http from 'node:http';
import crypto from 'node:crypto';
import ece from 'http_ece';
let feil = 0; const sjekk = (navn, ok, info) => { console.log((ok ? '  OK   ' : '  FEIL ') + navn + (ok ? '' : '  ' + JSON.stringify(info))); if (!ok) feil++; };
// a fake Supabase (the RPCs) and a fake push service, on localhost
const mottatt = [], rpcKall = [];
let nokler = null; const ko = [];
const server = http.createServer((req, res) => {
  let b = []; req.on('data', d => b.push(d)); req.on('end', () => {
    const body = Buffer.concat(b);
    if (req.url.startsWith('/rest/v1/rpc/')) {
      const fn = req.url.split('/').pop(), j = body.length ? JSON.parse(body) : {};
      rpcKall.push({ fn, apikey: req.headers.apikey, auth: req.headers.authorization });
      res.setHeader('Content-Type', 'application/json');
      if (fn === 'varsler_nokler') { if (j.p_offentlig && !nokler) nokler = { offentlig: j.p_offentlig, privat: j.p_privat }; return res.end(nokler ? JSON.stringify(nokler) : 'null'); }
      if (fn === 'varsler_hent') { const u = ko.filter(v => !v.ferdig); return res.end(JSON.stringify(u)); }
      if (fn === 'varsler_ferdig') { j.p_svar.forEach(s => { const v = ko.find(x => x.id === s.id); v.ferdig = s.status; }); return res.end(''); }
    }
    if (req.url.startsWith('/push/')) {
      mottatt.push({ url: req.url, headers: req.headers, body });
      res.statusCode = req.url.includes('borte') ? 410 : 201; return res.end();
    }
    res.statusCode = 404; res.end();
  });
});
await new Promise(r => server.listen(8799, r));
globalThis.Deno = { env: { get: k => ({ SUPABASE_URL: 'http://localhost:8799', SUPABASE_SECRET_KEYS: JSON.stringify({ default: 'sb_secret_test' }) })[k] } };
const m = await import(process.argv[2] ? `${process.argv[2]}/supabase/functions/send-varsler/index.ts` : new URL('../supabase/functions/send-varsler/index.ts', import.meta.url));
// two phones: their keys as a browser makes them
const tlf = () => { const e = crypto.createECDH('prime256v1'); e.generateKeys(); const auth = crypto.randomBytes(16); return { e, p256dh: e.getPublicKey('base64url'), auth: auth.toString('base64url') }; };
const a = tlf(), b = tlf();
ko.push({ id: 1, endpoint: 'http://localhost:8799/push/a', p256dh: a.p256dh, auth: a.auth, tittel: 'Hagefugltellingen', tekst: 'Hagefugltellingen er i gang! Tell i én time og få 75 000 frø.', url: './?vis=telling', tag: 'telling', ttl: 21600 });
ko.push({ id: 2, endpoint: 'http://localhost:8799/push/borte', p256dh: b.p256dh, auth: b.auth, tittel: 'T', tekst: 't', url: './', tag: 'test', ttl: 600 });
const ut = await m.kjor();
sjekk('kjor: én sendt, én borte', ut.sendt === 1 && ut.borte === 1 && ut.feil === 0, ut);
sjekk('nøklene ble laget og lagret', nokler && nokler.offentlig && fraLengde(nokler.offentlig) === 65 && nokler.privat.kty === 'EC' && nokler.privat.d, nokler);
function fraLengde(s) { return Buffer.from(s, 'base64url').length; }
sjekk('den hemmelige nøkkelen i apikey, ikke som Bearer', rpcKall.every(k => k.apikey === 'sb_secret_test' && !k.auth), rpcKall.slice(0, 2));
sjekk('svarene meldt tilbake (201 og 410)', ko[0].ferdig === 201 && ko[1].ferdig === 410, ko.map(v => v.ferdig));
const p = mottatt.find(x => x.url === '/push/a');
sjekk('hodene: aes128gcm, TTL, Urgency', p && p.headers['content-encoding'] === 'aes128gcm' && p.headers.ttl === '21600' && p.headers.urgency === 'normal', p && p.headers);
// the phone decrypts (RFC 8291) with its own private key and auth secret
const klar = ece.decrypt(p.body, { version: 'aes128gcm', privateKey: a.e, authSecret: a.auth });
const json = JSON.parse(klar.toString('utf8'));
sjekk('telefonen dekrypterer innholdet', json.tittel === 'Hagefugltellingen' && json.tekst === 'Hagefugltellingen er i gang! Tell i én time og få 75 000 frø.' && json.url === './?vis=telling' && json.tag === 'telling', json);
// VAPID (RFC 8292): t = JWT signed with the private key, k = the public key
const auth = p.headers.authorization, mt = /^vapid t=([^,]+), k=(.+)$/.exec(auth);
sjekk('Authorization: vapid t=…, k=…', !!mt && mt[2] === nokler.offentlig, auth);
const [h, c, s] = mt[1].split('.'), claims = JSON.parse(Buffer.from(c, 'base64url'));
sjekk('JWT: aud er push-tjenesten, sub og exp innen 24 t', claims.aud === 'http://localhost:8799' && claims.sub === 'https://fuglekort.no' && claims.exp > Date.now() / 1000 && claims.exp < Date.now() / 1000 + 86400, claims);
const pub = await crypto.webcrypto.subtle.importKey('raw', Buffer.from(nokler.offentlig, 'base64url'), { name: 'ECDSA', namedCurve: 'P-256' }, false, ['verify']);
const ok = await crypto.webcrypto.subtle.verify({ name: 'ECDSA', hash: 'SHA-256' }, pub, Buffer.from(s, 'base64url'), Buffer.from(`${h}.${c}`));
sjekk('signaturen stemmer med den offentlige nøkkelen (ES256)', ok && JSON.parse(Buffer.from(h, 'base64url')).alg === 'ES256');
// a second run: the same keys, nothing more to send
const ut2 = await m.kjor();
const n1 = nokler.offentlig;
sjekk('andre gang: ingenting å sende, samme nøkler', ut2.sendt === 0 && ut2.borte === 0 && nokler.offentlig === n1, ut2);
// RFC 8291 appendix A test vector (the same salt and keys must give the same bytes)
const tv = {
  tekst: 'When I grow up, I want to be a watermelon',
  uaPub: 'BCVxsr7N_eNgVRqvHtD0zTZsEc6-VV-JvLexhqUzORcxaOzi6-AYWXvTBHm4bjyPjs7Vd8pZGH6SRpkNtoIAiw4',
  auth: 'BTBZMqHH6r4Tts7J_aSIgg',
  salt: 'DGv6ra1nlYgDCS1FRnbzlw',
};
const body = await m.krypter(tv.uaPub, tv.auth, new TextEncoder().encode(tv.tekst), new Uint8Array(Buffer.from(tv.salt, 'base64url')));
sjekk('test-vektoren: salt, postlengde 4096 og nøkkel-id på 65 byte', Buffer.from(body.slice(0, 16)).toString('base64url') === tv.salt && body[19] === 0 && body[18] === 16 && body[20] === 65 && body.length === 16 + 4 + 1 + 65 + tv.tekst.length + 1 + 16, body.length);
server.close();
console.log(feil ? `FEIL: ${feil}` : 'FEIL: ingen');
