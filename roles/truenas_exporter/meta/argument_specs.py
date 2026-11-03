# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
from ansible_devkit.argspec.models import ArgumentSpec, ArgumentSpecs, OptionSpec
DEFAULT_AUTHOR = "Collection maintainers"

argument_specs = ArgumentSpecs(
    argument_specs={
        "main": ArgumentSpec(
            short_description="Off-box Prometheus exporter for TrueNAS pool health",
            version_added="1.0",
            author=DEFAULT_AUTHOR,
            options={
                "truenas_exporter_url": OptionSpec(
                    type="str",
                    required=True,
                    description=[
                        "The appliance's API base URL, https://<address>. No default: the address",
                        "is the caller's inventory configuration.",
                    ],
                ),
                "truenas_exporter_api_key": OptionSpec(
                    type="str",
                    required=False,
                    no_log=True,
                    description=[
                        "A TrueNAS API key (resolve it from a secret store). The role refuses to",
                        "deploy with an empty or implausibly short key: an exporter started without",
                        "one serves truenas_up 0 forever, which reads as an appliance outage.",
                    ],
                ),
                "truenas_exporter_port": OptionSpec(
                    type="int",
                    required=False,
                    description=["Port the exporter listens on."],
                ),
                "truenas_exporter_verify_tls": OptionSpec(
                    type="bool",
                    required=False,
                    description=[
                        "Verify the appliance's TLS certificate (false for a self-signed one)."
                    ],
                ),
                "truenas_exporter_apply": OptionSpec(
                    type="bool",
                    required=False,
                    description=[
                        "Deploy. False (the default) only reports what would be deployed."
                    ],
                ),
            },
        )
    }
)
