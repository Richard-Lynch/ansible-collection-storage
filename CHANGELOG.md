<!--
Copyright: (c) 2026, Richard Lynch
SPDX-License-Identifier: GPL-3.0-or-later
-->

# Changelog

All notable changes to this collection are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the collection
uses [Semantic Versioning](https://semver.org/).

## [1.0.2] — 2026-11-06

### Changed

- The CI, release and disclose callers use ansible-devkit `v0.4.1`.

### Fixed

- `restic_backup` installs its backup script, which carries the repository password and the B2 keys, with `no_log` and `diff: false`, so `--diff` and a failed task's result no longer print them.
- `backup_restore_drill`: `restore_drill_password` and `restore_drill_b2_app_key` are `no_log` in the argument spec.

## [1.0.1] — 2026-11-03

### Added

- `meta/main.yml` with `galaxy_info` (author, description, license, minimum Ansible version, tags)
  for `iscsi_mount_units` and `truenas_storage`, so every role carries a description on Galaxy.

### Changed

- CI, disclosure and release callers use ansible-devkit v0.2.2.

## [1.0.0] — 2026-11-03

### Added

- Roles `truenas_storage` (grow-only zvols and datasets, generate-don't-apply), `truenas_snapshot_tasks` (periodic snapshot tasks via `midclt`), `truenas_config_backup` (native config export with size and type gates) and `truenas_exporter` (an off-box Prometheus exporter for pool health).
- Role `iscsi_mount_units`: an iSCSI login unit ordered before its mount unit, staged, diffed and verified with `systemd-analyze` before anything live changes.
- Roles `restic_backup` (restic to an Object-Locked B2 bucket on a systemd timer) and `backup_restore_drill` (restore and ZFS-rollback drills that prove a backup recovers data).
- Every estate-specific value is a required option with no default: the appliance address and password, the bucket and its credentials, the snapshot policy, the guest id and the drill dataset.
