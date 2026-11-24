# Update Helper integration — LEGION

Date: 2026-11-23 America/New_York (November 24 UTC).
Host verified by hostname: LEGION.

## Reuse decision

The directory C:\work\Update Helper now contains update_helper.py and
test_update_helper.py plus .gitignore. It has no .git directory in the
observed inventory. The reviewed script SHA-256 is
27a1b14561f6efc2b9d74e2e509712c06ca277eb54a35230a9b08ef95a49498f.

The existing utility owns immutable whole-install file manifests,
host/root/phase checks, comparison, and structural manifest validation.
Spellcasting owns PE fingerprints and its narrow manifest-to-PE binding.
Neither tool qualifies native addresses on a changed build from matching
file records alone. No sibling source was changed.

## Historical baseline recovery

The broad bounded search counted 150,358 files and hit its cap, with
some inaccessible long paths. It found a RiftWorld restored historical PE
with SHA df954b798331e18359be62a31cc74b49fc3f50b87385ebb080a5448256322c01,
not the required older PE. A second targeted search of 23,012 files
found no matching archive in the inspected directories. It found two
RRE SC306 source manifests documenting LEGION's earlier 1935a05c... build.
Those manifests describe a 452-byte slice, not a full executable.
No Update Helper capture manifest was found in its directory. These
bounded searches do not establish global absence.

## Consumer

tools/verify_update_manifest.py invokes the reviewed Update Helper
verify subcommand only, pins its source digest, checks the manifest
receipt against the exact manifest bytes, and binds the executable
record to a fresh PE fingerprint on the expected host and path.
It rejects a different phase, host, source digest, manifest digest,
installation path, or executable identity. Successful binding is
MANIFEST_BOUND_UNQUALIFIED (exit 3); blocked is exit 2.
A manifest is a recorded identity, not authentication of historical
provenance or proof of stable live behavior.

## Validation

- Python unit tests: 18/18 passed on LEGION.
- Real sibling validator integration with a temporary synthetic PE and
  structurally valid manifest: successful binding, native qualification
  false. Rewriting that fixture caused candidate identity rejection.
- No actual game installation capture was initiated; no client or
  sibling repository modifications occurred.

Next: obtain a verified full historical archive or a suitable recorded
capture and use the new consumer. Keep historical native tests opt-in
and do not substitute the newer RiftWorld archive for the older build.
