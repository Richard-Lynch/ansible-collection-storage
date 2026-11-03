# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from ansible_devkit.argspec.models import ArgumentSpec, ArgumentSpecs, OptionSpec
DEFAULT_AUTHOR = "Collection maintainers"

argument_specs = ArgumentSpecs(
    argument_specs={
        "main": ArgumentSpec(
            short_description="Export the TrueNAS config DB via midclt and fetch it to the controller",
            description=[
                "Protects the single highest-value, lowest-cost artefact on the TrueNAS appliance: "
                "/data/freenas-v1.db. That SQLite file IS the TrueNAS configuration — pool "
                "topology, datasets, shares, iSCSI targets, users, snapshot tasks, everything. Losing "
                "it means rebuilding the NAS by hand even though every disk survived.",
                "OUT OF SCOPE, deliberately: the ZFS POOL DATA itself, which lives on the "
                "pool's disks. This role does not and cannot back "
                "that up — it only protects the small config DB that describes it.",
                "Prefers TrueNAS's own native export (`midclt call core.download config.save`, the same "
                "mechanism behind the UI's 'Save Config' button) over a raw file copy, because a "
                "live copy of the SQLite file can catch it mid-write. Runs on the appliance itself "
                "via midclt, as truenas_snapshot_tasks does — midclt authenticates locally as "
                "root, so this adds no new credential.",
                "Verifies the exported artefact by read-back: it must exist, exceed a sane minimum "
                "size (a tiny file can look like a backup and restore nothing), and carry "
                "the SQLite or POSIX-tar magic bytes rather than being an empty file or an error page.",
                "Fetches the verified artefact to a controller-local staging directory so a separate "
                "play can push it onward to durable storage. This role does NOT itself decide where "
                "the durable copy lives; that is the calling play's decision.",
            ],
            version_added="1.0",
            author=DEFAULT_AUTHOR,
            options={
                "truenas_config_backup_remote_dir": OptionSpec(
                    type="str",
                    required=False,
                    default="/root/.ansible-truenas-config-backup",
                    description=[
                        "Scratch directory on the TrueNAS appliance the export is written into "
                        "before being fetched off. Cleaned up after a successful fetch.",
                    ],
                ),
                "truenas_config_backup_secretseed": OptionSpec(
                    type="bool",
                    required=False,
                    default=True,
                    description=[
                        "Include the password secret seed in the export. Required to restore local "
                        "user passwords; without it a restore resets them. This makes the artefact "
                        "security-sensitive — it is never logged and must land only in a secret "
                        "store or the backup storage, never printed.",
                    ],
                ),
                "truenas_config_backup_root_authorized_keys": OptionSpec(
                    type="bool",
                    required=False,
                    default=True,
                    description=[
                        "Include root's authorized_keys in the export, so a restore preserves SSH "
                        "access rather than locking the appliance out.",
                    ],
                ),
                "truenas_config_backup_local_staging_dir": OptionSpec(
                    type="str",
                    required=False,
                    default="/tmp/truenas-config-backup-staging",
                    description=[
                        "Controller-local directory the verified artefact is fetched into. A "
                        "separate play pushes it onward to durable storage from here.",
                    ],
                ),
                "truenas_config_backup_min_size_bytes": OptionSpec(
                    type="int",
                    required=False,
                    default=102400,
                    description=[
                        "Minimum acceptable artefact size in bytes (default 100KB). It rejects "
                        "the failure mode of a tiny file that LOOKS like a backup and restores "
                        "nothing.",
                    ],
                ),
                "truenas_config_backup_fallback_to_raw_db": OptionSpec(
                    type="bool",
                    required=False,
                    default=False,
                    description=[
                        "If true AND the native `config.save` export fails, fall back to copying "
                        "/data/freenas-v1.db directly. Off by default: a raw copy of a live SQLite "
                        "file can be caught mid-write and is not guaranteed consistent. The native "
                        "export is strongly preferred; this exists only as a documented last resort.",
                    ],
                ),
                "truenas_config_backup_apply": OptionSpec(
                    type="bool",
                    required=False,
                    default=False,
                    description=[
                        "Generate-don't-apply gate. When false (default) the role only confirms "
                        "midclt is reachable and reports the export it WOULD run and where the "
                        "artefact would be staged; it does not call config.save or fetch anything. "
                        "Set true to actually export, verify, and fetch the artefact.",
                    ],
                ),
            },
        )
    }
)
