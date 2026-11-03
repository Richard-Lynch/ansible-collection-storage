# iscsi_mount_units

Owns a host's **iSCSI login + mount systemd units**, generated so that an iSCSI-backed mount
(`/mnt/media` in the examples) comes back after a reboot, including when the iSCSI target is
slower to come up than the initiator (a NAS that boots after the host that mounts from it).

## The three unit defects it replaces

Hand-written units for this job commonly carry three defects; the role detects them in the live
units, replaces them, and asserts they are gone.

| | Defect | Effect |
|---|---|---|
| **D1** | `Requires=pvevm@<vmid>.service` | That unit **does not exist** on current PVE (guests start via `pve-guests`/`pvescheduler`). At boot the unsatisfiable `Requires` is ignored; on any manual restart systemd refuses outright — the unit **cannot be restarted by hand at all**. |
| **D2** | Bare `oneshot` login, no readiness check, no `Restart=` | Fires shortly after boot, before the NAS is serving iSCSI, gets `error (8 - connection timed out)`, latches `failed`, and **never retries**. |
| **D3** | `ConditionPathExists=` on the iSCSI device | The device cannot exist before login. **A failed Condition is not an error** — systemd records the unit as skipped and reports success, so the mount quietly does nothing on every cold boot. Usually paired with `Wants=` (no ordering, no failure propagation). |

D3 is a silent guard: a check that reads as a safety interlock whose only effect is to make the
failure invisible.

## What the replacements do

**Login unit** — waits for the **portal to actually answer** (`/dev/tcp` probe, bounded) before
attempting `iscsiadm --login`, tolerates rc 15 (`already logged in`) so it is idempotent, and
`Restart=on-failure` with `StartLimitIntervalSec=0` so a slow NAS self-heals instead of latching.

The portal probe is the crux: **a running NAS VM is not a serving iSCSI target**, and that gap is
exactly D2. Depending on a TCP port also removes any need to know PVE's internal unit naming — the
mistake behind D1.

**Mount unit** — `Requires=` + `After=` the login unit, no `ConditionPathExists`, bounded
`TimeoutSec` for the udev-created device node. If the login fails, the mount fails loudly.

## Usage

```yaml
- hosts: pve_node
  gather_facts: true          # REQUIRED — backup filenames use ansible_facts.date_time
  become: true
  roles:
    - role: richard_lynch.storage.iscsi_mount_units
      iscsi_units_target_iqn: "iqn.2005-10.org.freenas.ctl:media"
      iscsi_units_portal_host: "192.0.2.10"
      iscsi_units_mount_path: "/mnt/media"
      iscsi_units_guest_ctid: 101 # required: the guest whose state is reported
      iscsi_units_apply: "{{ units_apply | default(false) }}"
```

Inputs are declared in `meta/argument_specs.py` — the `.yml` and `defaults/main.yml` are
**generated** (`argspec x generate iscsi_mount_units`, from
ansible-devkit).

## Safety properties

Asserted by `molecule/default/verify.yml`; the D3 and ordering gates are mutation-tested.

- **Generate-don't-apply.** The default run renders to a staging dir, validates with
  `systemd-analyze verify`, and shows a **real diff** against the live units — writing nothing.
- **Backs up before replacing**, timestamped and `force: false`, so the original hand-written units
  survive any number of re-applies. Hand-written units are often in no version control, so these
  backups may be the only record.
- **Read-back gate** asserts the installed units contain **no `pvevm@` dependency directive** and
  **no `ConditionPathExists`** — checking directives, not comments, so the units' own documentation
  cannot satisfy or break the check.
- **Enables but never starts.** It will not remount a live filesystem; the only honest test of boot
  behaviour is a reboot.
- **Never touches the guest.** Container state and `onboot` are the caller's concern; the role only
  reports the state of `iscsi_units_guest_ctid`.

## Rollback

```bash
ls /etc/systemd/system/*.bak-*
cp /etc/systemd/system/<unit>.bak-<stamp> /etc/systemd/system/<unit>
systemctl daemon-reload
```

Printed with the real timestamp after applying.

## Test coverage (honest)

`molecule/default/` runs the **real role** against fixture copies of units carrying all three
defects, with `systemctl`/`systemd-analyze`/`iscsiadm`/`findmnt`/`pct` faked. Genuinely covered: the
dry-run guarantee, rendered unit content, all three defect removals, ordering, the backup contract,
and that the backup holds the *original* content.

**Not covered, and not claimed:** `systemctl enable` (the module talks D-Bus to the real systemd, so
it is skipped when pointed at a fixture directory), whether systemd accepts the units at boot, and
whether the mount actually succeeds. Those need a real host and a real reboot.
