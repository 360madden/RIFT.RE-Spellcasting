import test from 'node:test';
import assert from 'node:assert/strict';
import { validateClockPairs } from './validate-clock-pairs.mjs';
const session = { host: 'AMD-DESKTOP', buildSha256: 'a'.repeat(64), processStart: 'ticks:123', playerId: 'uPlayer' };
const example = () => ({ sessionId: 'trial-A', session: { ...session }, pairs: [
  { sessionId: 'trial-A', gameFrame: 100, utcBefore: '2026-11-16T20:00:00.000Z', utcAfter: '2026-11-16T20:00:00.100Z' },
  { sessionId: 'trial-A', gameFrame: 102, utcBefore: '2026-11-16T20:00:02.000Z', utcAfter: '2026-11-16T20:00:02.120Z' }
] });
test('accepts bounded, same-session synthetic pairs but no latency qualification', () => {
  assert.deepEqual(validateClockPairs(example()), { accepted: true, pairCount: 2, sessionId: 'trial-A', maxObservedCaptureWindowMs: 120, frameSpan: 2, latencyQualified: false, reason: 'structural-pairs-only-no-calibrated-drift-or-event-latency' });
});
test('one pair cannot establish a clock relation', () => { const a = example(); a.pairs.pop(); assert.equal(validateClockPairs(a).reason, 'at-least-two-pairs-required'); });
test('rejects foreign session and missing process identity', () => {
  const a = example(); a.pairs[1].sessionId = 'trial-B'; assert.equal(validateClockPairs(a).reason, 'session-mismatch-1');
  const b = example(); delete b.session.processStart; assert.equal(validateClockPairs(b).reason, 'session-identity-required');
});
test('rejects inverted or excessive UTC windows', () => {
  const a = example(); a.pairs[0].utcAfter = '2026-11-16T19:59:59.000Z'; assert.equal(validateClockPairs(a).reason, 'capture-window-invalid-0');
  const b = example(); b.pairs[0].utcAfter = '2026-11-16T20:00:01.000Z'; assert.equal(validateClockPairs(b).reason, 'capture-window-invalid-0');
});
test('rejects nonmonotonic frame or overlapping UTC intervals', () => {
  const a = example(); a.pairs[1].gameFrame = 100; assert.equal(validateClockPairs(a).reason, 'non-monotonic-pairs-1');
  const b = example(); b.pairs[1].utcBefore = '2026-11-16T20:00:00.090Z'; b.pairs[1].utcAfter = '2026-11-16T20:00:00.110Z'; assert.equal(validateClockPairs(b).reason, 'non-monotonic-pairs-1');
});
test('rejects missing frame, bad timestamp and build digest', () => {
  const a = example(); a.pairs[0].gameFrame = null; assert.equal(validateClockPairs(a).reason, 'invalid-pair-0');
  const b = example(); b.pairs[0].utcBefore = 'yesterday'; assert.equal(validateClockPairs(b).reason, 'invalid-pair-0');
  const c = example(); c.session.buildSha256 = 'invalid'; assert.equal(validateClockPairs(c).reason, 'build-sha-invalid');
});

test('rejects normalized impossible UTC calendar dates and 24-hour rollover', () => {
  for(const value of ['2026-02-30T20:00:00Z','2026-11-31T20:00:00Z','2026-11-16T24:00:00Z','2026-11-16T20:00:60Z']) {
    const a=example(); a.pairs[0].utcBefore=value;
    assert.equal(validateClockPairs(a).reason,'invalid-pair-0');
  }
});
test('preserves distinct sub-millisecond UTC intervals', () => {
  const a=example();
  a.pairs[0].utcBefore='2026-11-16T20:00:00.0000001Z';
  a.pairs[0].utcAfter='2026-11-16T20:00:00.0000002Z';
  a.pairs[1].utcBefore='2026-11-16T20:00:00.0000003Z';
  a.pairs[1].utcAfter='2026-11-16T20:00:00.0000005Z';
  const r=validateClockPairs(a);
  assert.equal(r.accepted,true);
  assert.equal(r.maxObservedCaptureWindowMs,0.0002);
  a.pairs[1].utcBefore=a.pairs[0].utcAfter;
  assert.equal(validateClockPairs(a).reason,'non-monotonic-pairs-1');
});
test('detects sub-millisecond inverted and excessive windows', () => {
  const a=example();
  a.pairs[0].utcBefore='2026-11-16T20:00:00.0000002Z';
  a.pairs[0].utcAfter='2026-11-16T20:00:00.0000001Z';
  assert.equal(validateClockPairs(a).reason,'capture-window-invalid-0');
  const b=example();
  b.pairs[0].utcAfter='2026-11-16T20:00:00.250000001Z';
  assert.equal(validateClockPairs(b).reason,'capture-window-invalid-0');
});
test('rejects unsupported precision and negative frame values', () => {
  const a=example(); a.pairs[0].utcBefore='2026-11-16T20:00:00.0000000001Z';
  assert.equal(validateClockPairs(a).reason,'invalid-pair-0');
  const b=example(); b.pairs[0].gameFrame=-1;
  assert.equal(validateClockPairs(b).reason,'invalid-pair-0');
});
test('blank session identity and malformed limits fail closed', () => {
  const a=example(); a.session.playerId='   ';
  assert.equal(validateClockPairs(a).reason,'session-identity-required');
  for (const maxCaptureWindowMs of [NaN,Infinity,0,-1,'250',1n,Symbol('limit')]) {
    assert.equal(validateClockPairs(example(),{maxCaptureWindowMs}).reason,'invalid-window-limit');
  }
});
