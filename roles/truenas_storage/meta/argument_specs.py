# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from ansible_devkit.argspec.models import ArgumentSpec, ArgumentSpecs, OptionSpec
DEFAULT_AUTHOR = "Collection maintainers"

argument_specs = ArgumentSpecs(
    argument_specs={
        "main": ArgumentSpec(
            short_description="Reconcile TrueNAS zvol sizes and datasets via the API",
            description=[
                "Grows zvols and creates datasets on a TrueNAS appliance through its REST API, so "
                "storage layout is declared in the repo rather than clicked in the UI or typed as "
                "ad-hoc `zfs` over SSH.",
                "GROW-ONLY for zvols by design: ZFS cannot shrink a zvol, and a volsize below the "
                "consumer filesystem's size destroys data. The role refuses to shrink rather than "
                "trusting the caller to have got it right.",
                "Defaults to generate-don't-apply — reports the diff and changes nothing until "
                "truenas_storage_apply is true.",
            ],
            version_added="1.0",
            author=DEFAULT_AUTHOR,
            options={
                "truenas_storage_api_host": OptionSpec(
                    type="str",
                    required=True,
                    description=["Address of the TrueNAS appliance."],
                ),
                "truenas_storage_api_user": OptionSpec(
                    type="str",
                    required=False,
                    default="truenas_admin",
                    description=["API user. The default is the administrative account TrueNAS SCALE creates at install."],
                ),
                "truenas_storage_api_password": OptionSpec(
                    type="str",
                    required=True,
                    no_log=True,
                    description=[
                        "API password (resolve it from a secret store; an empty value is rejected).",
                    ],
                ),
                "truenas_storage_validate_certs": OptionSpec(
                    type="bool",
                    required=False,
                    default=False,
                    description=["TrueNAS presents a self-signed certificate by default."],
                ),
                "truenas_storage_zvols": OptionSpec(
                    type="list",
                    elements="dict",
                    required=False,
                    default=[],
                    description=[
                        "Zvols to reconcile. Only `volsize` is managed, and only upwards.",
                    ],
                    options={
                        "name": OptionSpec(
                            type="str",
                            required=True,
                            description=["Full zvol path, e.g. pool1/media."],
                        ),
                        "volsize_gb": OptionSpec(
                            type="int",
                            required=True,
                            description=[
                                "Desired size in GiB. Must be greater than or equal to the current "
                                "size — shrinking is refused.",
                            ],
                        ),
                    },
                ),
                "truenas_storage_datasets": OptionSpec(
                    type="list",
                    elements="dict",
                    required=False,
                    default=[],
                    description=["Filesystem datasets to create if absent."],
                    options={
                        "name": OptionSpec(
                            type="str",
                            required=True,
                            description=["Full dataset path, e.g. tank/backups."],
                        ),
                        "comments": OptionSpec(
                            type="str",
                            required=False,
                            description=["Free-text description stored on the dataset."],
                        ),
                        "quota_gb": OptionSpec(
                            type="int",
                            required=False,
                            description=["Optional quota in GiB. Omit for no quota."],
                        ),
                        "compression": OptionSpec(
                            type="str",
                            required=False,
                            default="lz4",
                            description=[
                                "Compression algorithm. LZ4 is near-free and near-always right."
                            ],
                        ),
                        "atime": OptionSpec(
                            type="str",
                            required=False,
                            default="DISABLED",
                            description=[
                                "Access-time updates: DISABLED or ENABLED. Deliberately NOT off/on — "
                                "bare off/on/OFF/ON are YAML 1.1 booleans, so the generated defaults "
                                "file trips yaml[truthy] and the value reaches the API as a bool "
                                "rather than the string TrueNAS wants. Mapped to OFF/ON at use.",
                            ],
                        ),
                    },
                ),
                "truenas_storage_destroy": OptionSpec(
                    type="list",
                    elements="dict",
                    required=False,
                    default=[],
                    description=[
                        "Datasets or zvols to DESTROY, recursively (snapshots included). Irreversible.",
                        "Every entry must carry `confirm: yes` AND the exact `expect_used_gb` the "
                        "role reads back from the appliance, so a typo or a stale plan cannot delete "
                        "the wrong thing or a thing that has since changed.",
                        "The role additionally refuses if the target is referenced by an iSCSI "
                        "extent, an NFS or SMB share, or a replication task, or if it has been "
                        "written to since its last snapshot.",
                    ],
                    options={
                        "name": OptionSpec(
                            type="str",
                            required=True,
                            description=["Full path of the dataset/zvol to destroy."],
                        ),
                        "confirm": OptionSpec(
                            type="str",
                            required=True,
                            description=[
                                "Must be the literal string 'yes'. Anything else refuses."
                            ],
                        ),
                        "expect_used_gb": OptionSpec(
                            type="int",
                            required=True,
                            description=[
                                "The size you believe this holds, in GiB. The role compares it "
                                "against the appliance (5% tolerance) and refuses on a mismatch — a "
                                "cheap guard against acting on a stale or mistaken plan.",
                            ],
                        ),
                    },
                ),
                "truenas_storage_pool_ceiling": OptionSpec(
                    type="int",
                    required=False,
                    default=80,
                    description=[
                        "Refuse to grow a zvol if its pool is already fuller than this percentage. "
                        "ZFS performance degrades sharply past ~80% and a full pool is very hard to "
                        "recover from.",
                    ],
                ),
                "truenas_storage_apply": OptionSpec(
                    type="bool",
                    required=False,
                    default=False,
                    description=[
                        "When false (default) the role reports the computed diff and changes nothing.",
                        "Set true to actually resize/create. Storage changes are hard to undo — run "
                        "once with false and read the diff first.",
                    ],
                ),
            },
        )
    }
)
