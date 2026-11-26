"""Summarize bounded, explicitly supplied offline combat-event records.

No client access or action output. The observation interval is supplied by
the record, not inferred from first and last damage events.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

MAX_BYTES = 2 * 1024 * 1024
KINDS = {"damage", "dodge", "miss", "resist", "immune", "heal"}
FIELDS = {"schema_version", "model_kind", "clock_domain", "start_ms",
          "end_ms", "coverage", "events"}
EVENT_FIELDS = {"id", "time_ms", "clock_domain", "kind", "ability_id",
                "caster_id", "target_id", "amount"}


def integer(value, label, minimum=0, maximum=10**12):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError("invalid " + label)
    return value


def name(value, label):
    if not isinstance(value, str) or not value.strip() or len(value) > 128:
        raise ValueError("invalid " + label)
    return value


def fields(value, expected, label):
    if not isinstance(value, dict) or value.keys() != expected:
        raise ValueError("invalid " + label + " fields")


def summarize(record):
    fields(record, FIELDS, "record")
    if type(record["schema_version"]) is not int or record["schema_version"] != 1:
        raise ValueError("unsupported schema")
    if record["model_kind"] not in ("synthetic-combat-events", "saved-combat-events"):
        raise ValueError("unsupported record kind")
    domain = name(record["clock_domain"], "clock domain")
    start = integer(record["start_ms"], "start")
    end = integer(record["end_ms"], "end", minimum=start + 1)
    if record["coverage"] not in ("partial", "declared-complete"):
        raise ValueError("coverage must be explicit")
    events = record["events"]
    if not isinstance(events, list) or len(events) > 10000:
        raise ValueError("invalid event list")
    counts = Counter()
    damage_by_ability = defaultdict(int)
    damage_by_caster = defaultdict(int)
    damage_by_target = defaultdict(int)
    seen = set()
    last = start
    damage = healing = 0
    for event in events:
        fields(event, EVENT_FIELDS, "event")
        event_id = name(event["id"], "event id")
        if event_id in seen:
            raise ValueError("duplicate event id")
        seen.add(event_id)
        stamp = integer(event["time_ms"], "event time", start, end)
        if stamp < last:
            raise ValueError("events not ordered")
        last = stamp
        if event["clock_domain"] != domain:
            raise ValueError("mixed clock domains")
        kind = event["kind"]
        if not isinstance(kind, str) or kind not in KINDS:
            raise ValueError("unsupported event kind")
        ability = name(event["ability_id"], "ability id")
        caster = name(event["caster_id"], "caster id")
        target = name(event["target_id"], "target id")
        amount = integer(event["amount"], "amount", maximum=10**9)
        if kind not in ("damage", "heal") and amount != 0:
            raise ValueError("avoidance must not carry damage or healing")
        counts[kind] += 1
        if kind == "damage":
            damage += amount
            damage_by_ability[ability] += amount
            damage_by_caster[caster] += amount
            damage_by_target[target] += amount
        elif kind == "heal":
            healing += amount
    span = end - start
    return {
        "schema_version": 1, "mode": "offline-record-summary",
        "model_kind": record["model_kind"], "clock_domain": domain,
        "observation_span_ms": span, "coverage": record["coverage"],
        "event_count": len(events), "event_counts": dict(sorted(counts.items())),
        "recorded_damage": damage, "recorded_healing": healing,
        "recorded_damage_per_second": damage * 1000 / span,
        "damage_by_ability": dict(sorted(damage_by_ability.items())),
        "damage_by_caster": dict(sorted(damage_by_caster.items())),
        "damage_by_target": dict(sorted(damage_by_target.items())),
        "coverage_independently_verified": False, "runtime_qualified": False,
        "limitations": "Totals cover only supplied events; declared coverage is not independently verified. "
                       "The supplied clock span is not calibrated latency or complete encounter DPS.",
    }


def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("duplicate JSON field: " + key)
        result[key] = value
    return result


def load_and_summarize(path):
    with Path(path).open("rb") as handle:
        raw = handle.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("record exceeds byte limit")
    try:
        obj = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs)
    except (UnicodeError, RecursionError) as error:
        raise ValueError("invalid record encoding or nesting") from error
    report = summarize(obj)
    report["source_sha256"] = hashlib.sha256(raw).hexdigest()
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record")
    args = parser.parse_args(argv)
    try:
        report = load_and_summarize(args.record)
    except (OSError, ValueError) as error:
        parser.exit(2, "Record rejected: " + str(error) + "\n")
    print(json.dumps(report, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
