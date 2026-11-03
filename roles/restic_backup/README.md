# restic_backup

Install `restic` + a systemd-timed nightly backup of a host's **critical small state** to an
**Object-Locked Backblaze B2** bucket.

## The ransomware control (why Object Lock + a no-delete key)

- DBs are **dumped** (not copied live) into `restic_backup_dump_dir`, which is then backed up.
- This host's B2 app key is **append-only — it cannot delete**. So a compromised host can't wipe its
  own backups. Pruning (`restic prune`) is done **elsewhere** with a separate delete-capable key.
- The bucket has **Object Lock (compliance)** — even the account can't delete within the retention.

## What it does

Installs restic, drops a `/usr/local/sbin/restic-backup.sh` (root:root 0700 — it holds the B2 creds),
and a systemd timer (nightly, randomized). Each run: dumps → `restic backup` → `restic forget`
(retention, no prune) → optional Healthchecks.io ping (dead-man switch).

## Inputs (per-host; set in inventory)

See [`meta/argument_specs.yml`](meta/argument_specs.yml). Key ones:
- `restic_backup_paths` — static paths to back up.
- `restic_backup_dumps` — `[{name, cmd}]` run before the snapshot (e.g. `sqlite3 x.db ".backup ..."`,
  `pg_dump ...`, an HA export).
- **Required, no default:** `restic_backup_b2_bucket`, `restic_backup_b2_key_id`,
  `restic_backup_b2_app_key`, `restic_backup_password`. Declare them in inventory and resolve the
  three credentials from a secret store at run time. Provision the bucket (Object Lock) and a
  no-delete key first.

## Usage (example — an application host)

```yaml
- hosts: app_host
  roles:
    - role: richard_lynch.storage.restic_backup
      restic_backup_dumps:
        - { name: app,  cmd: 'docker exec app  sqlite3 /config/app.db  ".backup {{ restic_backup_dump_dir }}/app.db"' }
        - { name: wiki, cmd: 'docker exec wiki sqlite3 /data/wiki.db   ".backup {{ restic_backup_dump_dir }}/wiki.db"' }
      restic_backup_paths:
        - /opt   # per-service compose + configs
```

The play installs + schedules but **does not run a backup** unless `restic_backup_run_now: true`.

## Safety / what it does NOT do

- Never prunes (no delete key on this host) — retention is `forget` only.
- Never runs a backup during the play by default (schedules the timer).
- Requires the B2 bucket + no-delete key to exist first (asserts the creds are present).

## Testing

`molecule/default/` renders the backup script from sample vars and asserts it uses `restic forget`
(never `prune`) and includes the dump dir — the ransomware-safety invariants.
