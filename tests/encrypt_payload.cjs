const fs = require('node:fs');
const vm = require('node:vm');
const { webcrypto } = require('node:crypto');
(async () => {
  const input = JSON.parse(fs.readFileSync(0, 'utf8'));
  const context = vm.createContext({ crypto: webcrypto, TextEncoder, Uint8Array, Date, Error });
  const source = fs.readFileSync('tgcloud/lib/payload.js', 'utf8');
  const module = new vm.SourceTextModule(source, { context });
  await module.link(() => { throw new Error('Unexpected dependency'); });
  await module.evaluate();
  process.stdout.write(await module.namespace.encryptPayload(input.request, input.key));
})().catch(() => { process.stderr.write('Encryption failed\n'); process.exitCode = 1; });
