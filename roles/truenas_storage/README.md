# truenas_storage

Reconciles **zvol sizes** and **datasets** on a TrueNAS appliance through its REST API, so storage
layout is declared in code rather than clicked in the UI or typed as ad-hoc `zfs` over SSH.

## Why it refuses things

The role is deliberately opinionated, because storage mistakes are hard to undo:

- **GROW-ONLY for zvols.** ZFS cannot shrink a zvol, and setting `volsize` below the size of the
  filesystem living on it destroys data. A shrink is refused with no override flag.
- **Resize, never create.** Creating a zvol involves decisions this role does not model (block size,
  sparseness, parent pool), so a named-but-missing zvol is an error rather than a silent create.
- **Pool ceiling.** Growth into a pool already past `truenas_storage_pool_ceiling` (default 80%) is
  refused. ZFS degrades sharply past ~80%, and a genuinely full pool can block writes for everything
  sharing it.
- **A failed capacity read is fatal**, not skipped. Without proof that there is room, nothing grows.

## Usage

```yaml
- hosts: truenas
  roles:
    - role: richard_lynch.storage.truenas_storage
      truenas_storage_api_password: "{{ truenas_password }}"   # from your secret store
      truenas_storage_zvols:
        - {name: "pool1/media", volsize_gb: 16384}
      truenas_storage_datasets:
        - {name: "tank/backups", comments: "backup datastore", quota_gb: 4096}
```

```bash
ansible-playbook <play>.yml                                    # diff only, changes nothing
ansible-playbook <play>.yml -e truenas_storage_apply=true      # apply
```

## After growing a zvol

Growing the zvol does **not** grow the filesystem on it. An iSCSI consumer must rescan its session
and extend its filesystem before the space is usable — that is a separate, host-side play. The role
prints this reminder.

## Variables

See `meta/argument_specs.yml` for the validated interface. **That file and `defaults/main.yml` are
generated** from `meta/argument_specs.py` — edit the Python and run
`argspec x generate truenas_storage` (from
ansible-devkit).

Note `atime` takes `DISABLED`/`ENABLED`, not `off`/`on`: bare `off`/`on` are YAML 1.1 booleans, so
they trip `yaml[truthy]` in the generated defaults and reach the API as a bool rather than the
string TrueNAS expects. Mapped to `OFF`/`ON` at the call site.

## Tests

`molecule/default/verify.yml` — 10 assertions against an invented appliance fixture
(pool1/media 11.5T, tank/media 7.19T). Covers grow, shrink (large **and** one-GiB-marginal), no-op
idempotency, missing zvol, pool ceiling in both directions, insufficient free space, and the atime
mapping. Tested in both directions deliberately — a gate only ever exercised on the happy path can
be unable to fire and still pass.

```bash
cd roles/truenas_storage && molecule test
```
