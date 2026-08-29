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
