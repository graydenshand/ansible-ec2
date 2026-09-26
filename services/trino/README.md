# Trino

A single-node Trino deployment. The node acts as both coordinator and worker. Trino is installed from the release tarball and run as a systemd service.

## AWS deployment

```sh
cdk deploy Trino
./setup.sh Trino
```

`setup.sh` downloads the SSH key and generates an inventory at `services/trino/inventories/Trino.yml`, then runs the hello_world playbook to confirm connectivity. The inventory configures an `iceberg` catalog alongside `tpch`.

Then install Trino:

```sh
ansible-playbook -i services/trino/inventories/Trino.yml services/trino/playbooks/trino_install.yml
```

Port 8080 is not open to the internet because authentication isn't configured yet. Use an SSH tunnel:

```sh
ssh -i ~/.ssh/trino-hosting.pem -L 8080:localhost:8080 ec2-user@<InstancePublicIp>
# then browse http://localhost:8080 or: trino --server http://localhost:8080
```

## Iceberg catalog

On AWS, the `iceberg` catalog uses the **Glue Data Catalog** as its metastore. Data and metadata files go in the stack's S3 bucket under `s3://<BucketName>/warehouse/`. Catalog state lives in Glue and S3 rather than on the instance, so rebuilding the instance loses no tables. The instance role can manage Glue databases and tables in the stack's account and region.

Create schemas in SQL. Without an explicit `location`, a schema goes under the warehouse directory:

```sql
CREATE SCHEMA iceberg.analytics;
CREATE TABLE iceberg.analytics.nation AS SELECT * FROM tpch.tiny.nation;
```

`cdk destroy` deletes the bucket, including all data. Glue databases created through Trino are not removed.

The docker environment has no AWS credentials, so local runs use `tpch` only and skip the Iceberg smoke test.

## Local testing

```sh
ssh-keygen -t ed25519 -f ansible_key -N ""   # repo root, once
docker compose -f services/trino/docker-compose.yml up --build -d
ansible-playbook -i services/trino/inventories/docker.yml services/trino/playbooks/trino_install.yml
```

The Trino UI is exposed on host port **8081**.

## Playbooks

### `playbooks/trino_install.yml`

- Installs Amazon Corretto 25 (Trino requires Java 25).
- Downloads the server tarball and CLI from GitHub releases into `/opt/trino`, and points `/opt/trino/current` at the release.
- Templates config into `/etc/trino`, one file per entry in `trino_catalogs`. Catalog files not in `trino_catalogs` are removed.
- Starts the `trino` systemd unit, waits until `/v1/info` reports it has started, then runs a `tpch` smoke query. If an `iceberg` catalog is configured, it also creates, reads and drops a table in a temporary `iceberg.trino_smoke_test` schema.

To upgrade, bump `trino_version` and rerun. The symlink moves and Trino restarts. Old release directories are left in place for rollback.

Key variables (defaults in `playbooks/group_vars/all.yml`, override in the inventory):

| Variable                  | Default                            | Purpose                                                       |
| ------------------------- | ---------------------------------- | ------------------------------------------------------------- |
| `trino_version`           | `"483"`                            | Trino release                                                 |
| `trino_java_package`      | `java-25-amazon-corretto-headless` | JDK package                                                   |
| `trino_jvm_heap`          | `5G`                               | `-Xmx`; ~70% of host RAM                                      |
| `trino_http_port`         | `8080`                             | HTTP port                                                     |
| `trino_environment`       | `production`                       | `node.environment`                                            |
| `trino_catalogs`          | `{tpch: {connector.name: tpch}}`   | Catalog name → properties (`setup.sh` adds `iceberg` for AWS) |
| `trino_config_properties` | `{}`                               | Extra `config.properties` entries                             |
