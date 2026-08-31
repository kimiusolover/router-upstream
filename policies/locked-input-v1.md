# Locked upstream input specification v1

## Purpose

This specification defines the input boundary between upstream acquisition and
router package or firmware builds.  A consumer may build only from a source
record whose `status` is `locked` and from the exact archive named by that
record.  The contract is intentionally fail-closed: absent, ambiguous, or
unverified data is not a lock.

This specification establishes source identity and integrity only.  It does
not establish board compatibility, boot-image compatibility, RF authorization,
or permission to flash a device.

## Record location and identity

- A record is a UTF-8 YAML document at `sources/<name>.yaml`.
- `<name>` and `name` must be identical and match
  `^[a-z0-9][a-z0-9._+-]*$`.
- A record represents one source artifact used by one component version.  A
  source change requires a new reviewed lock change; consumers must not infer
  an archive URL or version from the file name.

## Required fields

Every record must contain these scalar fields:

| Field | Requirement |
| --- | --- |
| `name` | Stable source identifier as above. |
| `status` | `pending-verification` or `locked`. |
| `upstream` | Canonical HTTPS project or release-page URL. |
| `source_type` | `git` or `archive`. |
| `revision` | Exact immutable source revision.  For `git`, a lowercase 40- or 64-hex object ID; for `archive`, the upstream release version or immutable release identifier. |
| `archive` | Cache filename only: no path separator, URL, `..`, or control character. |
| `sha256` | Lowercase SHA-256 hex digest of the archive bytes. |
| `license` | SPDX identifier or SPDX expression. |
| `retrieved_at` | RFC 3339 timestamp of the reviewed retrieval. |
| `provenance` | Object containing the retrieval evidence described below. |

`pending-verification` records may use `unset` only for `revision`, `archive`,
and `sha256`.  A `locked` record must supply valid, non-`unset` values for all
required fields.

## Provenance and trust

`provenance` is required for every record and contains:

- `archive_url`: exact HTTPS URL used to obtain the cached archive;
- `retrieved_by`: accountable human or automation identity;
- `retrieval_method`: `manual` or `automation`;
- `evidence`: one or more immutable or versioned references, such as an
  upstream signed tag, release checksum, or reviewed release page;
- `signature`: optional verification result.  If present, it contains
  `status` (`verified`, `not-present`, or `not-verified`), `type`, and the
  signer/key fingerprint when verification succeeded.

The SHA-256 is mandatory even when an upstream signature was verified.  A
signature result never substitutes for archive-byte verification.  A record
with `signature.status: not-verified` can be locked only after explicit review
recorded in the lock-change commit; automated promotion must reject it.

## Lock acceptance rules

A record is an accepted lock only when all of the following are true:

1. It validates against `schemas/source-lock-v1.schema.json` after YAML is
   parsed.
2. `status` is exactly `locked`.
3. `upstream` and `provenance.archive_url` use HTTPS.
4. `archive` is a cache filename and the local cache contains that exact name.
5. The SHA-256 of the local archive exactly equals `sha256`.
6. The revision is immutable under the rules for `source_type`.
7. The consumer uses no network access to fill in any field or acquire a
   replacement archive.

Any failure blocks the build.  Consumers must report the record and failed
condition, and must not fall back to a mirror, a moving branch, a different
tag, or a locally modified source tree.

## Change control

- Lock changes are reviewable, atomic changes to the record and any required
  patch metadata.
- Updating `revision`, `archive`, `sha256`, or `provenance.archive_url` is a
  new source intake, not a formatting-only change.
- Patches are downstream policy and remain outside the archive digest.  Their
  ordered identifiers and digests must be declared by the consuming build
  provenance.
- Automated sync may propose a change, but may not merge it, publish artifacts,
  sign artifacts, deploy, flash, or alter RF settings.

## Consumer requirements

Consumers must read only a locked checkout of this repository, verify the
archive locally before extraction, and preserve at least `name`, `revision`,
`sha256`, `archive`, and the lock repository commit in build provenance.
