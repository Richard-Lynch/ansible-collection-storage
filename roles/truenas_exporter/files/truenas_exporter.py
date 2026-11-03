#!/usr/bin/env python
# SPDX-License-Identifier: GPL-3.0-or-later
"""Prometheus exporter for TrueNAS pool health, run OFF the appliance.

WHY OFF-BOX. TrueNAS SCALE is an appliance: /usr, /var, /etc, /root and /opt are all datasets under
boot-pool/ROOT/<version>, so an OS upgrade clones a NEW boot environment and anything installed
there is gone — silently. Monitoring that disappears at the next update and says nothing is worse
than none, because you stop looking. Nothing is installed on TrueNAS; this queries its middleware
API from a separate managed host. If the API ever changes, this exporter's scrape fails and
`up == 0` fires immediately, which is the loud failure an on-appliance install cannot give.

WHY THE MIDDLEWARE API AND NOT `zpool`. It is the same API the WebUI uses, so it reports what
TrueNAS itself believes. `zpool` output would need parsing and disagrees with the appliance during a
resilver. The API is also independent of the appliance's reporting stack, which has been
replaced between releases, so it is the stable contract.

WHAT THIS COVERS. TrueNAS's built-in reporting covers CPU, network, sensors and per-disk
temperatures, but exposes no pool series to Prometheus. Pool health, capacity and scrub state are
exactly the things a NAS most needs watched: a degraded or full pool under a mounted filesystem
otherwise goes unnoticed until its consumers start failing.

NO THIRD-PARTY EXPORTER. A community exporter exists, but it is young and would be an unpinned
dependency in the path of storage alerting. This is a short script against a documented API, with
its failure modes made explicit.
"""

from __future__ import annotations

import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

# No default address: the appliance is the deployer's (the role writes it from truenas_exporter_url).
TRUENAS_URL = os.environ.get("TRUENAS_URL", "")
API_KEY = os.environ.get("TRUENAS_API_KEY", "")
LISTEN_PORT = int(os.environ.get("EXPORTER_PORT", "9108"))
TIMEOUT = float(os.environ.get("TRUENAS_TIMEOUT", "20"))
# TrueNAS serves a self-signed certificate by default. The exporter is meant for an internal hop,
# but the API only speaks HTTPS, so verification is disabled rather than the transport being
# downgraded. Set TRUENAS_VERIFY_TLS=true once a
# trusted cert is in place.
VERIFY_TLS = os.environ.get("TRUENAS_VERIFY_TLS", "false").lower() == "true"


def _ctx() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    if not VERIFY_TLS:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return ctx


def fetch(path: str):
    req = urllib.request.Request(
        f"{TRUENAS_URL}/api/v2.0{path}",
        headers={"Authorization": f"Bearer {API_KEY}", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT, context=_ctx()) as resp:
        return json.loads(resp.read().decode("utf-8"))


def esc(value) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def render() -> str:
    """Build the exposition text. Exactly ONE HELP and ONE TYPE per metric — a second HELP line
    makes Prometheus reject the whole payload, silently dropping every series in it."""
    out = [
        "# HELP truenas_up 1 if the TrueNAS API answered this scrape.",
        "# TYPE truenas_up gauge",
        "# HELP truenas_pool_healthy 1 if TrueNAS considers the pool healthy.",
        "# TYPE truenas_pool_healthy gauge",
        "# HELP truenas_pool_status_online 1 if pool status is ONLINE. DEGRADED/FAULTED/UNAVAIL read 0.",
        "# TYPE truenas_pool_status_online gauge",
        "# HELP truenas_pool_size_bytes Total pool size.",
        "# TYPE truenas_pool_size_bytes gauge",
        "# HELP truenas_pool_allocated_bytes Bytes allocated in the pool.",
        "# TYPE truenas_pool_allocated_bytes gauge",
        "# HELP truenas_pool_free_bytes Bytes free in the pool.",
        "# TYPE truenas_pool_free_bytes gauge",
        "# HELP truenas_pool_fragmentation_percent Pool fragmentation.",
        "# TYPE truenas_pool_fragmentation_percent gauge",
        "# HELP truenas_pool_scrub_errors Errors found by the last scrub. Non-zero means investigate.",
        "# TYPE truenas_pool_scrub_errors gauge",
        "# HELP truenas_pool_scrub_in_progress 1 while a scrub or resilver is running.",
        "# TYPE truenas_pool_scrub_in_progress gauge",
        "# HELP truenas_pool_scrub_finished_timestamp_seconds When the last scrub ended. ABSENT if never scrubbed.",
        "# TYPE truenas_pool_scrub_finished_timestamp_seconds gauge",
        "# HELP truenas_scrape_duration_seconds How long querying the TrueNAS API took.",
        "# TYPE truenas_scrape_duration_seconds gauge",
    ]

    started = time.monotonic()
    try:
        pools = fetch("/pool")
    except Exception:
        # A failed scrape emits truenas_up 0 and NO pool series. Deliberately not stale values:
        # a pool reported healthy from cache while the API is unreachable is exactly the lie this
        # exporter exists to prevent.
        out.append("truenas_up 0")
        out.append(f"truenas_scrape_duration_seconds {time.monotonic() - started:.3f}")
        return "\n".join(out) + "\n"

    for pool in pools:
        name = str(pool.get("name") or "")
        if not name:
            continue
        lbl = f'pool="{esc(name)}"'
        status = str(pool.get("status") or "UNKNOWN")

        out.append(f"truenas_pool_healthy{{{lbl}}} {1 if pool.get('healthy') else 0}")
        out.append(
            f'truenas_pool_status_online{{{lbl},status="{esc(status)}"}} '
            f"{1 if status == 'ONLINE' else 0}"
        )
        for key, metric in (
            ("size", "size_bytes"),
            ("allocated", "allocated_bytes"),
            ("free", "free_bytes"),
            ("fragmentation", "fragmentation_percent"),
        ):
            value = pool.get(key)
            if value is None:
                continue
            try:
                out.append(f"truenas_pool_{metric}{{{lbl}}} {float(value)}")
            except (TypeError, ValueError):
                pass

        scan = pool.get("scan") or {}
        errors = scan.get("errors")
        if errors is not None:
            try:
                out.append(f"truenas_pool_scrub_errors{{{lbl}}} {int(errors)}")
            except (TypeError, ValueError):
                pass
        out.append(
            f"truenas_pool_scrub_in_progress{{{lbl}}} "
            f"{1 if str(scan.get('state') or '') == 'SCANNING' else 0}"
        )
        end = scan.get("end_time")
        # {"$date": ms}. Absent means NEVER SCRUBBED, reported as no series rather than 0 — a 1970
        # timestamp reads as "scrubbed long ago" and sorts correctly on a graph, hiding the pool
        # that has never been scrubbed at all.
        if isinstance(end, dict) and end.get("$date") is not None:
            try:
                out.append(
                    f"truenas_pool_scrub_finished_timestamp_seconds{{{lbl}}} "
                    f"{int(end['$date']) / 1000.0}"
                )
            except (TypeError, ValueError):
                pass

    out.append("truenas_up 1")
    out.append(f"truenas_scrape_duration_seconds {time.monotonic() - started:.3f}")
    return "\n".join(out) + "\n"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 - required by BaseHTTPRequestHandler
        if self.path.rstrip("/") in ("/metrics", ""):
            body = render().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path.rstrip("/") == "/healthz":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok\n")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *_args):
        # Silent: one line per scrape at 30s intervals is pure journal noise, and the interesting
        # failure (API unreachable) is already visible as truenas_up 0 in Prometheus.
        return


def main() -> int:
    if not TRUENAS_URL:
        print("TRUENAS_URL is not set — refusing to start", file=sys.stderr)
        return 2
    if not API_KEY:
        print("TRUENAS_API_KEY is not set — refusing to start", file=sys.stderr)
        return 2
    HTTPServer(("0.0.0.0", LISTEN_PORT), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
