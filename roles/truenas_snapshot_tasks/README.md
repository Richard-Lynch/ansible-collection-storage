# truenas_snapshot_tasks

Create/reconcile **TrueNAS SCALE periodic ZFS snapshot tasks** through the appliance middleware
(`midclt`), so the recurring-snapshot policy is declared in code rather than clicked in the UI. ZFS
snapshots are **Copy-2** (local, cheap, instant) of the
3-2-1 backup model — they defend against fat-finger deletes and are the source for `restic`/replication.

## Why midclt, not sanoid (and not the REST API)

The pools live **inside the TrueNAS SCALE appliance**. SCALE owns snapshot scheduling in its
middleware (`pool.snapshottask`); running `sanoid` inside the appliance would fight the platform.
The role runs **on the appliance** via `midclt call pool.snapshottask.*`. midclt authenticates
locally as root — **no API key**, so this adds no credential.

## What it does

1. Validates the requested policy (every `naming_schema` carries the middleware-required
   `%Y %m %d %H %M` tokens; `lifetime_unit` is one of `HOUR/DAY/WEEK/MONTH/YEAR`).
2. `midclt call pool.snapshottask.query` to see what already exists.
3. Creates only the **missing** tasks (matched on `naming_schema`, unique per tier) — **idempotent and
   additive**: it never edits or deletes tasks it didn't create.

## Inputs

See [`meta/argument_specs.yml`](meta/argument_specs.yml). Key ones:
- `truenas_snapshot_tasks` — the per-dataset policy. Each item: `{dataset, recursive, lifetime_value,
  lifetime_unit, naming_schema, schedule{minute,hour,dom,month,dow}, exclude?, allow_empty?}`.
- `truenas_snapshot_enabled_on_create` — default `false`: new tasks are created **disabled** so an
  operator reviews the policy in the UI before snapshots start. Set `true` to enable on create.

## Example policy (tiered, applied recursively to the pool root)

`truenas_snapshot_tasks` is **required and has no default**: which datasets to snapshot is the
caller's configuration, so declare it in inventory. A tiered policy for a pool named `pool1`:

| Tier | Schedule | Keeps |
|---|---|---|
| frequent | hourly | 2 days |
| daily | 02:00 daily | 2 weeks |
| weekly | 03:00 Sundays | 2 months |

```yaml
truenas_snapshot_tasks:
  - { dataset: pool1, recursive: true, lifetime_value: 2, lifetime_unit: DAY,
      naming_schema: "auto-%Y-%m-%d_%H-%M-frequent",
      schedule: { minute: "0", hour: "*", dom: "*", month: "*", dow: "*" } }
  - { dataset: pool1, recursive: true, lifetime_value: 2, lifetime_unit: WEEK,
      naming_schema: "auto-%Y-%m-%d_%H-%M-daily",
      schedule: { minute: "0", hour: "2", dom: "*", month: "*", dow: "*" } }
  - { dataset: pool1, recursive: true, lifetime_value: 2, lifetime_unit: MONTH,
      naming_schema: "auto-%Y-%m-%d_%H-%M-weekly",
      schedule: { minute: "0", hour: "3", dom: "*", month: "*", dow: "0" } }
```

## Safety / what it does NOT do

- Never deletes or edits existing snapshot tasks (additive reconcile only).
- Creates tasks **disabled** by default — no snapshots start until someone enables them (or you set
  `truenas_snapshot_enabled_on_create: true`).

## Testing

`molecule/default/` exercises the offline-testable logic with **no real appliance contact**: it runs
`validate.yml` against a well-formed policy and asserts the reconcile compute skips an already-existing
task and schedules only the missing one (idempotency).
