# truenas_config_backup

Exports the **TrueNAS configuration database** (`/data/freenas-v1.db`) via TrueNAS's own
`config.save` middleware method — the same mechanism behind the UI's "Save Config" button — and
fetches the verified artefact to the Ansible controller. This is the single highest-value,
lowest-cost thing to protect on the appliance: that one SQLite file **is** the TrueNAS
configuration (pool topology, datasets, shares, iSCSI targets, users, snapshot tasks, everything).
Losing it means rebuilding the NAS by hand even though every disk survived.

## Two layers — read this before assuming this role "backs up TrueNAS"

1. **The ZFS pool data** lives on the pool's disks. This role does **not** and **cannot** back that
   up — it is out of scope, on purpose. Pool data is protected by ZFS snapshots
   (`truenas_snapshot_tasks`) plus replication or an offsite copy.
2. **The TrueNAS config** (this role's entire job) is small and cheap to protect, and needs its own
   backup: a pool snapshot does not capture the boot pool, and an image-level backup that excludes
   the boot disk captures nothing useful.

## Why `config.save`, not a raw copy of the SQLite file

`config.save` is TrueNAS's own export path (`job: true, downloadable: true` in the middleware,
`roles: [FULL_ADMIN]`) — the same thing the UI's "Save Config" button calls. It produces a
consistent, restorable artefact. Copying `/data/freenas-v1.db` directly can catch it mid-write. The
native export is driven via `midclt call core.download config.save ...`, which runs the job and
returns a one-time download URL that is then fetched from the appliance's own HTTP endpoint on
localhost. It runs on the appliance itself (`hosts: <your TrueNAS host>`), as
`truenas_snapshot_tasks` does: **midclt authenticates locally as root, so this adds no new
credential.**

A raw copy of `/data/freenas-v1.db` is available as a documented last resort
(`truenas_config_backup_fallback_to_raw_db: true`) if the native export ever fails, with the
consistency caveat stated plainly in the task output.

## What it exports

By default the export includes:
- `secretseed: true` — required to restore local user passwords; without it a restore resets them.
- `root_authorized_keys: true` — so a restore doesn't lock root out of SSH.

Both make the artefact **security-sensitive** — treat the staged file like a credential. It is
never logged; only the response of the final `file -b` type-check is printed (harmless — a file
type string, not a secret).

## Verification (read-back, not trust)

The role never treats "the command exited 0" as proof of a good backup:
1. **Exists and non-empty** — `stat` after the export.
2. **Exceeds a minimum size** (default 100KB) — this gate rejects a tiny file that looks like a
   backup and restores nothing. A DB-only export is hundreds of KB; a tar with keys/seed is
   larger still, so a real export clears 100KB by a wide margin.
3. **Is actually a tar archive or SQLite database** (`file -b`) — size alone isn't enough; a padded
   HTML error page could clear 100KB too. Molecule's `verify.yml` proves this fires independently
   of the size gate.
4. **Checksum match after fetch** — the controller-side copy is re-stat'd and compared against the
   appliance-side checksum, so a truncated `fetch` can't silently ship a corrupt artefact onward.

## Generate-don't-apply

Default (`truenas_config_backup_apply: false`) only confirms `midclt` is reachable and reports the
export it **would** run and where the artefact would land. Nothing is exported or fetched. Set
`truenas_config_backup_apply: true` to actually run it.

```yaml
- hosts: nas
  roles:
    - role: richard_lynch.storage.truenas_config_backup
      truenas_config_backup_apply: true   # omit for the report-only run
```

## Where the artefact ends up

This role only stages the verified artefact **on the controller**
(`truenas_config_backup_local_staging_dir`, default `/tmp/truenas-config-backup-staging`). It
deliberately does not decide the durable destination: that is the calling play's job. Push it
somewhere that is NOT the appliance itself (storing a TrueNAS backup on TrueNAS is circular), and
preferably to more than one place, so losing any single machine does not lose the backup with it.

## Variables

See [`meta/argument_specs.yml`](meta/argument_specs.yml) — generated from `meta/argument_specs.py`.
**Never hand-edit the `.yml` or `defaults/main.yml`**; edit the Python and regenerate:
`argspec x generate truenas_config_backup` (from
ansible-devkit).

Key ones: `truenas_config_backup_apply`, `truenas_config_backup_min_size_bytes`,
`truenas_config_backup_fallback_to_raw_db`, `truenas_config_backup_secretseed`,
`truenas_config_backup_root_authorized_keys`.

## Testing

`molecule/default/` is **check/parse tier** (this role talks to a real appliance over midclt,
which CI cannot reproduce). It stubs three fixtures (a genuine tar over the size floor, a 2048-byte
"looks like a backup" file, and an over-size-but-wrong-
type file) and re-runs the role's own size + `file -b` type-guard logic against all three, in both
directions — proving the gates actually fire rather than merely existing.

```bash
cd roles/truenas_config_backup && molecule test
```
