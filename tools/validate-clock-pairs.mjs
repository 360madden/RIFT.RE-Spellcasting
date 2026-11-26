// Offline structural gate for paired game-frame and UTC observations.
// This is NOT a clock calibration or a client/server acknowledgement detector.
function reject(reason) { return { accepted: false, reason, latencyQualified: false }; }
const named = x => typeof x === 'string' && x.trim().length > 0;

// Parse UTC without Date.parse's normalization of impossible calendar dates or
// silent truncation of sub-millisecond fractions. Integer nanoseconds preserve
// ordering and interval comparisons for typical high-resolution receipt strings.
function utcNanoseconds(value) {
  if (typeof value !== 'string') return null;
  const match = /^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d{1,9}))?Z$/.exec(value);
  if (!match) return null;
  const whole = Date.parse(match[1] + '.000Z');
  if (!Number.isFinite(whole) || new Date(whole).toISOString() !== match[1] + '.000Z') return null;
  return BigInt(whole) * 1000000n + BigInt((match[2] || '').padEnd(9, '0'));
}

export function validateClockPairs(input, { maxCaptureWindowMs = 250 } = {}) {
  if (!input || !Array.isArray(input.pairs) || input.pairs.length < 2) return reject('at-least-two-pairs-required');
  // The configured maximum must be representable in integer nanoseconds.
  if (typeof maxCaptureWindowMs !== 'number') return reject('invalid-window-limit');
  const maxNs = Math.floor(maxCaptureWindowMs * 1000000);
  if (!Number.isSafeInteger(maxNs) || maxNs <= 0)
    return reject('invalid-window-limit');
  const { session } = input;
  if (!named(input.sessionId) || !session || !['host', 'buildSha256', 'processStart', 'playerId'].every(k => named(session[k]))) return reject('session-identity-required');
  if (!/^[a-f0-9]{64}$/i.test(session.buildSha256)) return reject('build-sha-invalid');
  let previousFrame, previousEnd, firstFrame, maxWindow = 0n;
  for (const [i, p] of input.pairs.entries()) {
    if (!p || !Number.isFinite(p.gameFrame) || p.gameFrame < 0) return reject('invalid-pair-' + i);
    const start = utcNanoseconds(p.utcBefore), end = utcNanoseconds(p.utcAfter);
    if (start === null || end === null) return reject('invalid-pair-' + i);
    if (p.sessionId !== input.sessionId || !named(p.sessionId)) return reject('session-mismatch-' + i);
    const window = end - start;
    if (window < 0n || window > BigInt(maxNs)) return reject('capture-window-invalid-' + i);
    if (i && (p.gameFrame <= previousFrame || start <= previousEnd)) return reject('non-monotonic-pairs-' + i);
    if (!i) firstFrame = p.gameFrame;
    if (window > maxWindow) maxWindow = window;
    previousFrame = p.gameFrame;
    previousEnd = end;
  }
  return { accepted: true, pairCount: input.pairs.length, sessionId: input.sessionId,
    maxObservedCaptureWindowMs: Number(maxWindow) / 1000000,
    frameSpan: previousFrame - firstFrame,
    latencyQualified: false, reason: 'structural-pairs-only-no-calibrated-drift-or-event-latency' };
}
