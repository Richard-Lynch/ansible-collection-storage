# backup_restore_drill

**Prove a restore.** Backups are worthless until a restore is proven, so this role exercises the real recovery path against a host that already runs `restic_backup`.

## What it does (READ-ONLY against the repo)

1. `restic check --read-data-subset` — verifies repo integrity by reading real pack data (a subset,
   so it stays cheap; set `restore_drill_read_data_subset: "100%"` for a full read or `""` to skip).
2. `restic restore latest --target <scratch>` — restores the newest snapshot to a **scratch dir**
   (wiped each run; never a live path).
3. Asserts each `restore_drill_expected_artifacts` entry returned **non-empty** — so the drill proves
   the restore is *useful* (a known DB dump came back), not merely that files exist.
4. *(optional)* A **ZFS snapshot rollback drill** on a **throwaway dataset**: writes a marker,
   snapshots, deletes the marker, rolls back, asserts the marker returned.

It never runs `backup`/`forget`/`prune` — restore + check only.

## Inputs

See [`meta/argument_specs.yml`](meta/argument_specs.yml). Key ones:
- `restore_drill_expected_artifacts` — `[{path, min_bytes}]`, paths relative to the restored tree
  (e.g. `dumps/app.db`). **Required** — a drill that checks nothing proves nothing.
- repo/creds default to the host's `restic_backup_*` values (resolved from your secret store).
- `restore_drill_zfs_enabled` + `restore_drill_zfs_dataset` — enable the ZFS rollback drill. The
  dataset name **must** contain `restore-drill`/`scratch` (a guard against pointing it at real data).

## Usage

```yaml
- hosts: app_host
  roles:
    - role: richard_lynch.storage.restic_backup            # provides the repo + creds
    - role: richard_lynch.storage.backup_restore_drill
      restore_drill_expected_artifacts:
        - { path: "var/backups/restic-dumps/app.db", min_bytes: 4096 }
```

## Prerequisites

The drill needs a repo with at least one snapshot: a B2 bucket, its key, and at least one completed
`restic_backup` run. Without them the role fails loud on its credentials assert.

## Testing

`molecule/default/` stubs a "restored" tree offline and asserts the artifact-verification logic accepts
a present non-empty file, that the size threshold is genuinely enforced (an under-size restore is
caught), and that the ZFS throwaway-dataset guard rejects a real dataset name.
