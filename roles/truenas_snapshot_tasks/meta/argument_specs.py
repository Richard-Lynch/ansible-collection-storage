# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
from ansible_devkit.argspec.models import ArgumentSpec, ArgumentSpecs, OptionSpec
DEFAULT_AUTHOR = "Collection maintainers"

argument_specs = ArgumentSpecs(
    argument_specs={
        "main": ArgumentSpec(
            short_description="Reconcile TrueNAS SCALE periodic ZFS snapshot tasks via midclt on the appliance",
            version_added="1.0",
            author=DEFAULT_AUTHOR,
            options={
                "truenas_snapshot_tasks": OptionSpec(
                    type="list",
                    elements="dict",
                    required=True,
                    description=[
                        "Per-dataset snapshot policy ({dataset, recursive, lifetime_value, lifetime_unit, naming_schema, schedule, ...})."
                    ],
                ),
                "truenas_snapshot_enabled_on_create": OptionSpec(
                    type="bool",
                    required=False,
                    default=False,
                    description=[
                        "Enable newly-created tasks immediately (default false — an operator reviews first)."
                    ],
                ),
            },
        )
    }
)
