# truenas_exporter

An off-box Prometheus exporter for TrueNAS pool health: a small Python service, installed as a
hardened systemd unit on a host you manage, that polls the appliance's REST API and serves
`truenas_up`, `truenas_pool_healthy{...}` and related gauges on `truenas_exporter_port`.

It runs OFF the appliance on purpose: TrueNAS reimages `/usr`, `/var`, `/etc`, `/root` and `/opt`
on every OS upgrade, so anything installed there disappears silently. Off-box, an upgrade can only
make the scrape FAIL, which Prometheus sees immediately.

## Inputs

See [`meta/argument_specs.yml`](meta/argument_specs.yml).

- `truenas_exporter_url` — **required, no default**: `https://<appliance address>`. The role
  refuses anything that is not `https://`.
- `truenas_exporter_api_key` — a TrueNAS API key, resolved from a secret store. The role refuses an
  empty or implausibly short key rather than starting an exporter that reports the appliance down.
- `truenas_exporter_apply` — `false` (default) reports what would be deployed and changes nothing.

## Usage

```yaml
- hosts: monitoring
  roles:
    - role: richard_lynch.storage.truenas_exporter
      vars:
        truenas_exporter_url: "https://{{ hostvars['nas']['ansible_host'] }}"
        truenas_exporter_api_key: "{{ lookup('my_secret_store', '<api key item>') }}"
```

After an apply the role asserts the exporter serves `truenas_up 1` and at least one pool series —
HTTP 200 alone is not proof, because the exporter answers 200 while the API is unreachable.

## Testing

`molecule test` (offline): the argspec refuses a call with no URL, the URL gate refuses
`http://`, and a dry run with valid inputs completes and writes nothing.
