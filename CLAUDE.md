The purpose of this project is configuring AWS EC2 instances using Ansible.

## Structure

`services/`: one subdirectory per deployment type; each is a Python package and contains its own CDK stack, playbooks, templates, inventories, and docker-compose file.

- `services/hello_world/`: connectivity test playbook
- `services/postgres/`: single-node PostgreSQL deployment
- `services/postgres_ha/`: two-node HA PostgreSQL with Patroni + DynamoDB
- `services/trino/`: single-node Trino (tarball + systemd install)

`common/`: shared CDK constructs (`Ec2Instance`, `public_vpc`) imported by service stacks.

`images/`: Docker images used by all docker-compose files for local testing.

`main.py`: CDK app entry point — imports and instantiates stacks from service modules.

`setup.sh`: dispatcher script; accepts a stack name argument and delegates to the matching service's own `setup.sh`. Each service setup script fetches its own CDK outputs, downloads the SSH key, and generates an inventory into its `inventories/` folder. Add a new `case` entry here when adding a new service.

## Services

### hello_world
- `stack.py`: `HelloWorldStack` CDK stack (minimal EC2 instance, no extra services)
- `setup.sh`: fetches stack outputs and generates inventory
- `playbooks/hello_world.yml`: ping hosts to verify Ansible connectivity

### postgres
- `stack.py`: `PostgresStack` CDK stack (single EC2 instance + S3 backup bucket)
- `docker-compose.yml`: single-container local testing environment
- `inventories/docker.yml`: local inventory for docker testing
- `playbooks/pg_install.yml`: install and start standalone postgres
- `playbooks/pg_backup.yml`: configure scheduled pg_dump backups to S3 (requires `pg_backup_bucket` in inventory); leader-check guard skips backup on Patroni replicas
- `templates/pg_backup.sh.j2`: Jinja2 template for the backup shell script

### postgres_ha
- `stack.py`: `PostgresHAStack` + `PostgresHACluster` CDK constructs (two EC2 instances, DynamoDB, NLB)
- `docker-compose.ha.yml`: two-container (pg-node-1, pg-node-2) local HA testing
- `inventories/docker_ha.yml`: two-node inventory for local HA testing using Raft DCS
- `playbooks/pg_patroni.yml`: install Patroni and deploy two-node HA PostgreSQL cluster (DynamoDB or Raft DCS)
- `playbooks/pg_switchover.yml`: manual leader switchover via `patronictl`
- `templates/patroni.yml.j2`: Patroni configuration template; supports DynamoDB DCS (production) or Raft DCS (`patroni_use_raft: true`, local testing)

### trino
- `stack.py`: `TrinoStack` CDK stack (single t4g.large instance + S3 bucket + Glue IAM for the Iceberg catalog; port 8080 not public, use an SSH tunnel)
- `setup.sh`: fetches stack outputs and generates inventory, including an `iceberg` catalog (Glue metastore, S3 warehouse) in `trino_catalogs`
- `docker-compose.yml`: single-container local testing environment (host ports 2222 → SSH, 8081 → Trino)
- `inventories/docker.yml`: local inventory for docker testing (smaller JVM heap)
- `playbooks/trino_install.yml`: install Java 25 + Trino tarball from GitHub releases, deploy config/catalogs (stale catalog files are removed), run as systemd service, smoke test via tpch (plus an Iceberg round-trip when an `iceberg` catalog is configured)
- `playbooks/group_vars/all.yml`: variable defaults (`trino_version`, `trino_jvm_heap`, `trino_catalogs`, ...); kept out of play vars so inventories can override them
- `templates/`: `config.properties`, `node.properties`, `jvm.config`, `log.properties`, per-catalog properties, and the systemd unit

As you make changes, keep README.md and CLAUDE.md (this file) up to date.
