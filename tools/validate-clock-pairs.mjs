// Offline structural gate for paired game-frame and UTC observations.
// This is NOT a clock calibration or a client/server acknowledgement detector.
function reject(reason) { return { accepted: false, reason, latencyQualified: false }; }
const validIso = x => typeof x === 'string' && /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z$/.test(x) && Number.isFinite(Date.parse(x));
export function validateClockPairs(input, { maxCaptureWindowMs = 250 } = {}) {
  if (!input || !Array.isArray(input.pairs) || input.pairs.length < 2) return reject('at-least-two-pairs-required');
  if (!Number.isFinite(maxCaptureWindowMs) || maxCaptureWindowMs <= 0) return reject('invalid-window-limit');
  const { session } = input;
  if (!session || !['host', 'buildSha256', 'processStart', 'playerId'].every(k => typeof session[k] === 'string' && session[k].length > 0)) return reject('session-identity-required');
  if (!/^[a-f0-9]{64}$/i.test(session.buildSha256)) return reject('build-sha-invalid');
  const normalized = [];
  for (const [i, p] of input.pairs.entries()) {
    if (!p || !Number.isFinite(p.gameFrame) || !validIso(p.utcBefore) || !validIso(p.utcAfter)) return reject('invalid-pair-' + i);
    if (p.sessionId !== input.sessionId || typeof p.sessionId !== 'string' || !p.sessionId) return reject('session-mismatch-' + i);
    const start = Date.parse(p.utcBefore), end = Date.parse(p.utcAfter);
    if (end < start || end - start > maxCaptureWindowMs) return reject('capture-window-invalid-' + i);
    if (normalized.length && (p.gameFrame <= normalized.at(-1).gameFrame || start <= normalized.at(-1).utcEnd)) return reject('non-monotonic-pairs-' + i);
    normalized.push({ gameFrame: p.gameFrame, utcStart: start, utcEnd: end, captureWindowMs: end - start });
  }
  return { accepted: true, pairCount: normalized.length, sessionId: input.sessionId,
    maxObservedCaptureWindowMs: Math.max(...normalized.map(x => x.captureWindowMs)),
    frameSpan: normalized.at(-1).gameFrame - normalized[0].gameFrame,
    latencyQualified: false, reason: 'structural-pairs-only-no-calibrated-drift-or-event-latency' };
}
