<!--
Copyright: (c) 2026, Richard Lynch
SPDX-License-Identifier: GPL-3.0-or-later
-->

# richard_lynch.storage

Storage and backup roles: TrueNAS zvols, datasets, periodic snapshot tasks and config backups through the appliance's API, an off-box TrueNAS pool-health exporter, systemd units that order an iSCSI login before its mount, and restic backups to Object-Locked B2 with a restore drill.

## Roles

| Role | Description |
| ---- | ----------- |
| `backup_restore_drill` | Prove a restore: restic check + restore + verify artifacts |
| `iscsi_mount_units` | Own a host's iSCSI login + mount systemd units, ordered to survive a reboot |
| `restic_backup` | restic backup of host state to Object-Locked B2 |
| `truenas_config_backup` | Export the TrueNAS config DB via midclt and fetch it to the controller |
| `truenas_exporter` | Off-box Prometheus exporter for TrueNAS pool health |
| `truenas_snapshot_tasks` | Reconcile TrueNAS SCALE periodic ZFS snapshot tasks via midclt on the appliance |
| `truenas_storage` | Reconcile TrueNAS zvol sizes and datasets via the API |

## Install

```sh
ansible-galaxy collection install richard_lynch.storage
```

or pin it in `requirements.yml`:

```yaml
collections:
  - name: richard_lynch.storage
    version: "1.0.2"
```

Requires ansible-core >=2.19.0.

## Development

```sh
# from a checkout at ansible_collections/richard_lynch/storage
ansible-test sanity --docker
ansible-test units --docker
ansible-galaxy collection build
devkit conform                  # the repository standard (ansible-devkit)
devkit check all                # the static checks, configured by devkit.toml
```

CI, the disclosure gate and releases are the shared workflows of
[ansible-devkit](https://github.com/Richard-Lynch/ansible-devkit), called from
`.github/workflows/` at tag `v0.4.1`. A release is a merged pull
request that bumps `version` in `galaxy.yml` and adds the matching
`CHANGELOG.md` section. `export.manifest` lists every tracked path; update it in
the same commit as any file added or removed.

## Licence

GPL-3.0-or-later. See [LICENSE](LICENSE).
