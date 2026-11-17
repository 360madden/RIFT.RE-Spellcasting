// Offline-only cast evidence model. This module never accesses a RIFT process or network.
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const kinds = new Set(['input_attempt', 'castbar_start', 'castbar_end', 'effect', 'interrupt', 'queue_setting']);
export function classifyCastEvidence(events, identity) {
  if (!Array.isArray(events)) throw new TypeError('events must be an array');
  const validIdentity = identity && typeof identity.casterId === 'string' && identity.casterId &&
    typeof identity.abilityId === 'string' && identity.abilityId;
  if ((!validIdentity && (identity != null || events.some(e => e?.kind !== 'queue_setting')))) {
    throw new TypeError('exact casterId and abilityId required for cast events');
  }
  const lastTime = new Map();
  const seen = new Set();
  const observed = new Set();
  const provenance = [];
  const queueModes = [];
  for (const event of events) {
    if (!event || !kinds.has(event.kind) || typeof event.id !== 'string' || !event.id ||
        !Number.isFinite(event.time) || event.time < 0 ||
        typeof event.clockDomain !== 'string' || !event.clockDomain ||
        typeof event.sourceId !== 'string' || !event.sourceId) {
      throw new TypeError('event missing valid kind, id, monotonic time, clockDomain or sourceId');
    }
    if (seen.has(event.id)) throw new Error('duplicate event id ' + event.id);
    seen.add(event.id);
    const prev = lastTime.get(event.clockDomain);
    if (prev !== undefined && event.time < prev) {
      throw new Error('out-of-order time within ' + event.clockDomain);
    }
    lastTime.set(event.clockDomain, event.time);
    if (event.kind === 'queue_setting') {
      if (!['Full', 'Short', 'None'].includes(event.mode)) throw new TypeError('invalid queue mode label');
      queueModes.push({ mode: event.mode, eventId: event.id, sourceId: event.sourceId });
      continue;
    }
    if (event.casterId !== identity.casterId || event.abilityId !== identity.abilityId) continue;
    if (event.kind === 'effect' && identity.targetId !== undefined && event.targetId !== identity.targetId) continue;
    observed.add(event.kind);
    provenance.push({ kind: event.kind, eventId: event.id, sourceId: event.sourceId,
      clockDomain: event.clockDomain, time: event.time });
  }
  return {
    identity: validIdentity ? { ...identity } : null,
    observed: {
      attempt: observed.has('input_attempt'),
      castbarStart: observed.has('castbar_start'),
      castbarEnd: observed.has('castbar_end'),
      effect: observed.has('effect'),
      interrupt: observed.has('interrupt')
    },
    serverAccepted: 'unknown',
    requestQueued: 'unknown',
    gcdActive: 'unknown',
    queueSettingsObserved: queueModes,
    provenance,
    limitations: 'Observed events are not proof of native/server acknowledgement or queue behavior.'
  };
}

// Optional CLI for bounded, developer-provided JSON fixtures. No file writes.
if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const path = process.argv[2];
  if (!path) throw new Error('Usage: node tools/classify-cast-evidence.mjs <fixture.json>');
  const input = JSON.parse(await readFile(path, 'utf8'));
  process.stdout.write(JSON.stringify(classifyCastEvidence(input.events, input.identity), null, 2) + '\n');
}
