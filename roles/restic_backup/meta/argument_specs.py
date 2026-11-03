# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
from ansible_devkit.argspec.models import ArgumentSpec, ArgumentSpecs, OptionSpec
DEFAULT_AUTHOR = "Collection maintainers"

argument_specs = ArgumentSpecs(
    argument_specs={
        "main": ArgumentSpec(
            short_description="restic backup of host state to Object-Locked B2",
            version_added="1.0",
            author=DEFAULT_AUTHOR,
            options={
                "restic_backup_version": OptionSpec(
                    type="str", required=False, description=["restic release to install."]
                ),
                "restic_backup_b2_bucket": OptionSpec(
                    type="str", required=True, description=["B2 bucket (Object Lock)."]
                ),
                "restic_backup_repo": OptionSpec(
                    type="str", required=False, description=["restic repo URL (b2:bucket:path)."]
                ),
                "restic_backup_b2_key_id": OptionSpec(
                    type="str",
                    required=True,
                    no_log=True,
                    description=["B2 key id (resolve it from a secret store)."],
                ),
                "restic_backup_b2_app_key": OptionSpec(
                    type="str",
                    required=True,
                    no_log=True,
                    description=["B2 app key, a no-delete key (resolve it from a secret store)."],
                ),
                "restic_backup_password": OptionSpec(
                    type="str",
                    required=True,
                    no_log=True,
                    description=["restic repo password (resolve it from a secret store)."],
                ),
                "restic_backup_paths": OptionSpec(
                    type="list",
                    elements="str",
                    required=False,
                    description=["Static paths to back up."],
                ),
                "restic_backup_dumps": OptionSpec(
                    type="list",
                    elements="dict",
                    required=False,
                    description=["Pre-backup dump commands ({name, cmd})."],
                ),
                "restic_backup_dump_dir": OptionSpec(
                    type="str", required=False, description=["Dir the dumps write to (backed up)."]
                ),
                "restic_backup_oncalendar": OptionSpec(
                    type="str", required=False, description=["systemd OnCalendar schedule."]
                ),
                "restic_backup_keep_daily": OptionSpec(
                    type="int", required=False, description=["Retention: keep-daily."]
                ),
                "restic_backup_keep_weekly": OptionSpec(
                    type="int", required=False, description=["Retention: keep-weekly."]
                ),
                "restic_backup_keep_monthly": OptionSpec(
                    type="int", required=False, description=["Retention: keep-monthly."]
                ),
                "restic_backup_healthcheck_url": OptionSpec(
                    type="str", required=False, description=["Dead-man switch ping URL."]
                ),
                "restic_backup_run_now": OptionSpec(
                    type="bool",
                    required=False,
                    default=False,
                    description=["Run a backup during the play."],
                ),
            },
        )
    }
)
