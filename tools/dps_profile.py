"""Strict versioned input profiles for the offline DPS simulation lab.

Profiles describe hypothetical encounters. They are not live ability catalogs,
readiness records, or instructions for a game client.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import stat

from dps_planner import Ability, ResourcePool, validate_model, validate_resources

MAX_PROFILE_BYTES = 64 * 1024
REQUIRED = {
    'schema_version', 'model_kind', 'name', 'assumptions',
    'horizon_ms', 'resource', 'resource_max', 'abilities',
}
OPTIONAL = {'regen_per_second', 'initial_lockout_ms', 'state_budget'}
ABILITY_FIELDS = {'id', 'damage', 'cost', 'cooldown_ms', 'lockout_ms'}
V2_FIELDS = {'impact_delay_ms', 'resource_gain', 'cooldown_anchor'}
V3_FIELDS = {'periodic_damage', 'periodic_interval_ms', 'periodic_ticks'}
V4_FIELDS = {'effect_duration_ms', 'self_bonus_bps', 'target_bonus_bps'}
V5_FIELDS = {'extra_costs', 'extra_gains'}


@dataclass(frozen=True)
class Scenario:
    name: str
    assumptions: str
    abilities: tuple[Ability, ...]
    horizon_ms: int
    resource: int
    resource_max: int
    regen_per_second: int = 0
    initial_lockout_ms: int = 0
    state_budget: int = 20000
    profile_version: int = 1
    extra_resources: tuple[ResourcePool, ...] = ()

    def model_kwargs(self):
        return {
            'horizon_ms': self.horizon_ms,
            'resource': self.resource,
            'resource_max': self.resource_max,
            'regen_per_second': self.regen_per_second,
            'initial_lockout_ms': self.initial_lockout_ms,
            'state_budget': self.state_budget,
            'extra_resources': self.extra_resources,
        }


def object_fields(value, required, optional, label):
    if not isinstance(value, dict):
        raise ValueError(label + ' must be an object')
    missing = required - value.keys()
    unknown = value.keys() - required - optional
    if missing or unknown:
        raise ValueError(f'{label} fields: missing {sorted(missing)}, unknown {sorted(unknown)}')


def parse_profile(value):
    version = value.get('schema_version') if isinstance(value, dict) else None
    object_fields(value, REQUIRED, OPTIONAL | ({'extra_resources'} if type(version) is int and version == 5 else set()), 'profile')
    if type(version) is not int or version not in (1, 2, 3, 4, 5):
        raise ValueError('unsupported profile schema')
    if value['model_kind'] != 'synthetic-simulation':
        raise ValueError('only synthetic simulation profiles are supported')
    for field, limit in [('name', 128), ('assumptions', 2048)]:
        text = value[field]
        if not isinstance(text, str) or not text.strip() or len(text) > limit:
            raise ValueError('invalid profile ' + field)
    rows = value['abilities']
    if not isinstance(rows, list) or not 1 <= len(rows) <= 32:
        raise ValueError('profile requires one to 32 abilities')
    abilities = []
    pools = []
    if version >= 5:
        raw_pools = value.get('extra_resources', [])
        if not isinstance(raw_pools, list) or len(raw_pools) > 3:
            raise ValueError('invalid additional resource list')
        for row in raw_pools:
            object_fields(row, {'id', 'initial', 'capacity'}, {'regen_per_second'}, 'resource')
            pools.append(ResourcePool(**row))
    pools = validate_resources(pools)
    allowed = {'ready_at_ms'} | (V2_FIELDS if version >= 2 else set())
    if version >= 3:
        allowed |= V3_FIELDS
    if version >= 4:
        allowed |= V4_FIELDS
    if version >= 5:
        allowed |= V5_FIELDS
    for row in rows:
        object_fields(row, ABILITY_FIELDS, allowed, 'ability')
        arguments = dict(row)
        for field in V5_FIELDS:
            if field in arguments:
                entries = arguments[field]
                if not isinstance(entries, dict):
                    raise ValueError('additional resource amounts must be an object')
                arguments[field] = tuple(sorted(entries.items()))
        abilities.append(Ability(**arguments))
    kwargs = {key: value[key] for key in (
        'horizon_ms', 'resource', 'resource_max', *sorted(OPTIONAL)
    ) if key in value}
    canonical, *_ = validate_model(abilities, extra_resources=pools, **kwargs)
    return Scenario(value['name'], value['assumptions'], canonical, profile_version=version, extra_resources=pools, **kwargs)


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON field: ' + key)
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError('non-finite JSON value: ' + value)


def load_profile(path):
    # Bound the actual read as well as the initial size check. The caller
    # supplies a local file; no network or automatic discovery is performed.
    with Path(path).open('rb') as handle:
        info = os.fstat(handle.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_PROFILE_BYTES:
            raise ValueError('profile must be a bounded regular file')
        raw = handle.read(MAX_PROFILE_BYTES + 1)
    if len(raw) > MAX_PROFILE_BYTES:
        raise ValueError('profile exceeded byte limit')
    try:
        obj = json.loads(raw.decode('utf-8'), object_pairs_hook=unique_pairs,
                         parse_constant=reject_constant)
    except (UnicodeError, RecursionError) as error:
        raise ValueError('invalid profile encoding or nesting') from error
    return parse_profile(obj)
