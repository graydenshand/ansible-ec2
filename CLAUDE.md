`The purpose of this project is configuring AWS EC2 instances using Ansible.

`docker-compose.yml` runs a testing environment that emulates an ec2 for local development and testing.

`images`: docker images.

`inventories`: ansible inventories.

`playbooks` contains ansible playbooks
- `hello_world.yml`: hello world script to verify configuration
- `pg_install.yml`: install and start postgres (standalone)
- `pg_backup.yml`: configure scheduled pg_dump backups to S3 (requires `pg_backup_bucket` in inventory); leader-check guard skips backup on Patroni replicas
- `pg_patroni.yml`: install Patroni and deploy two-node HA PostgreSQL cluster (DynamoDB or Raft DCS)
- `pg_switchover.yml`: manual leader switchover via `patronictl`

`templates/pg_backup.sh.j2`: Jinja2 template for the backup shell script deployed by `pg_backup.yml`.

`templates/patroni.yml.j2`: Jinja2 template for the Patroni configuration file deployed by `pg_patroni.yml`. Supports DynamoDB DCS (production) or Raft DCS (`patroni_use_raft: true`, local testing).

`main.py`: AWS CDK stacks — `PostgresStack` (single instance) and `PostgresHAStack` (two-node HA with Patroni + DynamoDB).

`setup.sh`: post-deploy script; accepts an optional stack name argument (`PostgresStack` or `PostgresHAStack`), downloads the SSH key, and generates an appropriate ansible inventory.

`docker-compose.ha.yml`: two-container setup (pg-node-1 and pg-node-2) for local HA testing.

`inventories/docker_ha.yml`: two-node inventory for local HA testing using Raft DCS.

As you make changes, keep README.md and CLAUDE.md (this file) up to date.
