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

## Upstream sync bot

`sync/upstream-sync` verifies an already acquired candidate source lock. It
requires the exact local archive and a clean local checkout that contains the
candidate's immutable Git revision, then applies any ordered `*.patch` files
in an ephemeral worktree using `git am --3way`.

```sh
python3 sync/upstream-sync \
  --record sources/component.yaml \
  --archive /secure-cache/component.tar.xz \
  --upstream-repo /secure-checkouts/component \
  --patch-dir patches/component \
  --report upstream-sync-report.json
```

Success emits a `needs-review` report. The bot never downloads upstream
material, changes a lock, creates or merges a pull request, builds firmware,
signs, distributes, flashes, or alters RF settings. Verification that needs a
private cache or checkout is run explicitly on a development machine, not in
GitHub Actions.
