# router-upstream

Source maps, synchronization policy, and downstream patch metadata for the
upstream projects consumed by the router platform.

## Layout

```
sources/   # one source record per upstream component
policies/  # version, trust, and update rules
patches/   # patch series metadata; payloads may be referenced by consumers
sync/      # automation for detecting and proposing updates
schemas/   # source-map and policy schemas
```

Source records identify immutable revisions and checksums. They do not claim
that an upstream version is compatible with a particular board; that decision
is made by firmware composition after platform validation.

## Locked upstream inputs

The normative v1 contract is [policies/locked-input-v1.md](policies/locked-input-v1.md).
Each `sources/<name>.yaml` record is validated as YAML against
[`schemas/source-lock-v1.schema.json`](schemas/source-lock-v1.schema.json).

A build consumer accepts only `status: locked` records, an exact local cache
archive, and a matching SHA-256.  It must not download, select a mirror, or
resolve a moving upstream ref during the build.  Source locks establish source
identity and integrity only; they do not authorize a firmware image, device
flash, or RF operation.
