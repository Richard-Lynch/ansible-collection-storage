# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from ansible_devkit.argspec.models import ArgumentSpec, ArgumentSpecs, OptionSpec
DEFAULT_AUTHOR = "Collection maintainers"

argument_specs = ArgumentSpecs(
    argument_specs={
        "main": ArgumentSpec(
            short_description="Own a host's iSCSI login + mount systemd units, ordered to survive a reboot",
            description=[
                "Replaces hand-written iscsi-login@/*.mount units with generated ones that survive",
                "a reboot, removing three defects such units commonly carry:",
                "",
                "  D1 the login unit declares Requires=pvevm@<vmid>.service, a unit that does not",
                "     exist on current PVE — so it cannot be restarted by hand at all",
                "  D2 the login races the NAS, times out, latches `failed`, and never retries",
                "  D3 the mount unit carries a ConditionPathExists on the iSCSI device, which",
                "     cannot exist before login — a failed Condition is NOT an error, so the mount",
                "     silently skips itself every boot and reports success",
                "",
                "Generate-don't-apply: the default run renders the replacements to a staging dir,",
                "validates them with systemd-analyze, and shows a diff against the live units",
                "without touching /etc/systemd/system.",
                "",
                "It ENABLES but never STARTS the units: it will not remount a live filesystem, and",
                "the only honest test of boot behaviour is a reboot.",
            ],
            version_added="1.0",
            author=DEFAULT_AUTHOR,
            options={
                "iscsi_units_target_iqn": OptionSpec(
                    type="str",
                    required=True,
                    description=[
                        "iSCSI target IQN, e.g. 'iqn.2005-10.org.freenas.ctl:media'. Required and",
                        "never defaulted — a wrong IQN yields units that look right and mount",
                        "nothing.",
                    ],
                ),
                "iscsi_units_portal_host": OptionSpec(
                    type="str",
                    required=True,
                    description=["Portal IP/host, e.g. '192.0.2.10'."],
                ),
                "iscsi_units_mount_path": OptionSpec(
                    type="str",
                    required=True,
                    description=[
                        "Absolute mount path, e.g. '/mnt/media'. The .mount unit name is derived from",
                        "it with systemd's own escaping, so it can never drift from the real unit.",
                    ],
                ),
                "iscsi_units_apply": OptionSpec(
                    type="bool",
                    required=False,
                    default=False,
                    description=[
                        "false (default) stages + validates + diffs, writing nothing to",
                        "/etc/systemd/system. true installs and enables the units (still without",
                        "starting them).",
                    ],
                ),
                "iscsi_units_portal_port": OptionSpec(
                    type="int",
                    required=False,
                    default=3260,
                    description=["iSCSI portal TCP port."],
                ),
                "iscsi_units_lun": OptionSpec(
                    type="int",
                    required=False,
                    default=0,
                    description=["LUN number, used to build the by-path device name."],
                ),
                "iscsi_units_fs_type": OptionSpec(
                    type="str",
                    required=False,
                    default="ext4",
                    description=["Filesystem type of the LUN."],
                ),
                "iscsi_units_mount_options": OptionSpec(
                    type="str",
                    required=False,
                    default="defaults,_netdev,noatime,discard",
                    description=[
                        "Mount options. _netdev matters: it tells systemd this is network storage.",
                    ],
                ),
                "iscsi_units_portal_wait_tries": OptionSpec(
                    type="int",
                    required=False,
                    default=60,
                    description=[
                        "How many times the login unit probes the portal before giving up. With the",
                        "default delay this is a 5-minute window — enough for a NAS VM to boot and",
                        "start serving on a cold start, which is the race being fixed.",
                    ],
                ),
                "iscsi_units_portal_wait_delay": OptionSpec(
                    type="int",
                    required=False,
                    default=5,
                    description=["Seconds between portal probes."],
                ),
                "iscsi_units_portal_probe_timeout": OptionSpec(
                    type="int",
                    required=False,
                    default=3,
                    description=["Per-probe TCP connect timeout in seconds."],
                ),
                "iscsi_units_restart_sec": OptionSpec(
                    type="int",
                    required=False,
                    default=30,
                    description=[
                        "Delay before systemd retries a failed login. Without Restart=, one",
                        "transient timeout leaves the mount down until someone intervenes.",
                    ],
                ),
                "iscsi_units_mount_timeout": OptionSpec(
                    type="str",
                    required=False,
                    default="120s",
                    description=[
                        "How long the mount unit waits for the device to appear after login (udev",
                        "creates it asynchronously).",
                    ],
                ),
                "iscsi_units_guest_ctid": OptionSpec(
                    type="int",
                    required=True,
                    description=["Guest whose state is reported for context. Never modified here."],
                ),
                "iscsi_units_stage_dir": OptionSpec(
                    type="str",
                    required=False,
                    default="/run/ansible-iscsi-units",
                    description=[
                        "Where the units are rendered for validation and diffing. On tmpfs so a dry",
                        "run leaves nothing behind across a reboot.",
                    ],
                ),
                "iscsi_units_show_diff": OptionSpec(
                    type="bool",
                    required=False,
                    default=True,
                    description=["Print the full unit diff, not just changed/identical."],
                ),
                "iscsi_units_systemd_dir": OptionSpec(
                    type="str",
                    required=False,
                    default="/etc/systemd/system",
                    description=[
                        "Where unit files live. Overridable ONLY so the molecule scenario can run",
                        "the real role against a fixture tree; production never sets it.",
                    ],
                ),
                "iscsi_units_doc_path": OptionSpec(
                    type="str",
                    required=False,
                    default="/usr/local/share/doc/iscsi_mount_units/README.md",
                    description=[
                        "Documentation= path recorded in the generated units, so an operator",
                        "reading `systemctl cat` on the host is pointed at the reasoning. The role",
                        "does not install a file there; point it at wherever you keep the notes.",
                    ],
                ),
            },
        )
    }
)
