# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
from ansible_devkit.argspec.models import ArgumentSpec, ArgumentSpecs, OptionSpec
DEFAULT_AUTHOR = "Collection maintainers"

argument_specs = ArgumentSpecs(
    argument_specs={
        "main": ArgumentSpec(
            short_description="Prove a restore: restic check + restore + verify artifacts",
            version_added="1.0",
            author=DEFAULT_AUTHOR,
            options={
                "restore_drill_repo": OptionSpec(
                    type="str",
                    required=False,
                    description=["restic repo URL to drill (defaults to restic_backup_repo)."],
                ),
                "restore_drill_password": OptionSpec(
                    type="str",
                    required=False,
                    description=["restic repo password (defaults to restic_backup_password)."],
                ),
                "restore_drill_b2_key_id": OptionSpec(
                    type="str",
                    required=False,
                    description=["B2 key id (defaults to restic_backup_b2_key_id)."],
                ),
                "restore_drill_b2_app_key": OptionSpec(
                    type="str",
                    required=False,
                    description=["B2 app key (defaults to restic_backup_b2_app_key)."],
                ),
                "restore_drill_target": OptionSpec(
                    type="str",
                    required=False,
                    description=["Scratch restore dir (wiped each run; never a live path)."],
                ),
                "restore_drill_expected_artifacts": OptionSpec(
                    type="list",
                    elements="dict",
                    required=False,
                    description=["Artifacts that must return non-empty ({path, min_bytes})."],
                ),
                "restore_drill_read_data_subset": OptionSpec(
                    type="str",
                    required=False,
                    description=[
                        "restic check --read-data-subset value ('' to skip, '100%' for full)."
                    ],
                ),
                "restore_drill_zfs_enabled": OptionSpec(
                    type="bool",
                    required=False,
                    default=False,
                    description=["Also drill a ZFS snapshot rollback on a throwaway dataset."],
                ),
                "restore_drill_zfs_dataset": OptionSpec(
                    type="str",
                    required=False,
                    description=[
                        "Throwaway dataset for the ZFS rollback drill (name must contain 'restore-drill'/'scratch')."
                    ],
                ),
            },
        )
    }
)
