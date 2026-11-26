// Offline-only cast evidence model. This module never accesses a RIFT process or network.
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const kinds = new Set(['input_attempt', 'castbar_start', 'castbar_end', 'effect', 'interrupt', 'queue_setting']);
const named = value => typeof value === 'string' && value.trim().length > 0;
const record = value => value !== null && typeof value === 'object' && !Array.isArray(value);
export function classifyCastEvidence(events, identity) {
  if (!Array.isArray(events)) throw new TypeError('events must be an array');
  const validIdentity = record(identity) && named(identity.casterId) && named(identity.abilityId);
  if (validIdentity && identity.targetId !== undefined && !named(identity.targetId))
    throw new TypeError('specified targetId must be a nonblank string');
  if ((!validIdentity && (identity != null || events.some(e => e?.kind !== 'queue_setting')))) {
    throw new TypeError('exact casterId and abilityId required for cast events');
  }
  const lastTime = new Map();
  const seen = new Set();
  const observed = new Set();
  const provenance = [];
  const queueModes = [];
  // Count excluded evidence instead of silently collapsing missing identity,
  // foreign identity and target mismatches into a single absent observation.
  const excluded = { missingCastIdentity: 0, otherCastIdentity: 0, otherTarget: 0, missingEffectTarget: 0 };
  for (const event of events) {
    if (!record(event) || !kinds.has(event.kind) || !named(event.id) ||
        !Number.isFinite(event.time) || event.time < 0 ||
        !named(event.clockDomain) || !named(event.sourceId)) {
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
      queueModes.push({ mode: event.mode, eventId: event.id, sourceId: event.sourceId,
        clockDomain: event.clockDomain, time: event.time });
      continue;
    }
    // A supplied malformed ID is not equivalent to an omitted ID. Preserve
    // absent caster/ability as unattributed evidence, never as a match.
    for (const field of ['casterId', 'abilityId', 'targetId']) {
      if (event[field] !== undefined && !named(event[field]))
        throw new TypeError('invalid event ' + field);
    }
    if (!named(event.casterId) || !named(event.abilityId)) {
      excluded.missingCastIdentity++;
      continue;
    }
    if (event.casterId !== identity.casterId || event.abilityId !== identity.abilityId) {
      excluded.otherCastIdentity++;
      continue;
    }
    const targetRequested = identity.targetId !== undefined;
    const targetReported = event.targetId !== undefined;
    if (targetRequested && targetReported && event.targetId !== identity.targetId) {
      excluded.otherTarget++;
      continue;
    }
    if (targetRequested && event.kind === 'effect' && !targetReported) {
      excluded.missingEffectTarget++;
      continue;
    }
    // Castbar/input observations often lack target telemetry. They can
    // describe the matching caster/ability, but not an exact target.
    const targetBinding = !targetRequested ? 'target-not-requested'
      : targetReported ? 'exact-target' : 'target-unspecified';
    observed.add(event.kind);
    provenance.push({ kind: event.kind, eventId: event.id, sourceId: event.sourceId,
      clockDomain: event.clockDomain, time: event.time, casterId: event.casterId,
      abilityId: event.abilityId, targetId: event.targetId ?? null, targetBinding });
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
    excludedEventCounts: excluded,
    limitations: 'Observed events are not proof of causality, native/server acknowledgement or queue behavior. Target-unspecified observations do not establish exact target identity.'
  };
}

// Optional CLI for bounded, developer-provided JSON fixtures. No file writes.
if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const path = process.argv[2];
  if (!path) throw new Error('Usage: node tools/classify-cast-evidence.mjs <fixture.json>');
  const input = JSON.parse(await readFile(path, 'utf8'));
  process.stdout.write(JSON.stringify(classifyCastEvidence(input.events, input.identity), null, 2) + '\n');
}
