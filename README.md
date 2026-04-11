# Getting started

Install the package: uv sync / pip install

Deploy the infrastructure using the CDK app in main.py.

Run the setup.sh script to generate an inventory and download the ssh key needed to connect to the instance.

Run ansible playbooks.

```sh
ansible-playbook -i inventories/inventory.yml playbooks/hello_world.yml
```

## Development container

You can also run a local docker container emulating the AmazonLinux2023 environment used in the ec2 deployment.

First you will need to generate an ssh key for testing. Then build and run the docker-compose file, and (in a separate shell) run an ansible playbook using the docker.yml inventory.

```
ssh-keygen -t ed25519 -f ansible_key -N ""
docker compose up --build
ansible-playbook -i inventories/docker.yml playbooks/hello_world.yml
```

## Playbooks

- `playbooks/hello_world.yml`: Verify Ansible can connect to the host
- `playbooks/pg_install.yml`: Install and start a standalone postgres server
- `playbooks/pg_backup.yml`: Configure scheduled pg_dump backups to S3
- `playbooks/pg_patroni.yml`: Deploy Patroni-managed HA PostgreSQL (two-node)
- `playbooks/pg_switchover.yml`: Manual leader switchover via `patronictl`

### pg_backup.yml

Installs AWS CLI, deploys `/usr/local/bin/pg_backup.sh`, and sets up a cron job (runs as `postgres`, default: 3 AM daily). Requires `pg_backup_bucket` to be set in the inventory (populated automatically by `setup.sh` after `cdk deploy`).

In HA mode, the backup script checks the Patroni REST API and skips execution on replica nodes — backups only run on the current primary.

Key variables (set in inventory or via `-e`):

| Variable | Default | Purpose |
|---|---|---|
| `pg_backup_databases` | `["postgres"]` | Databases to back up |
| `pg_backup_bucket` | *(from inventory)* | S3 bucket name |
| `pg_backup_s3_prefix` | `"backups"` | S3 key prefix |
| `pg_backup_cron_minute` | `"0"` | Cron minute |
| `pg_backup_cron_hour` | `"3"` | Cron hour |
| `pg_backup_dry_run` | `false` | Skip S3 upload (for local Docker testing) |

For local Docker testing, run with dry-run mode:

```sh
ansible-playbook -i inventories/docker.yml playbooks/pg_backup.yml -e pg_backup_dry_run=true -e pg_backup_bucket=test-bucket
```

---

## HA Deployment (PostgresHAStack)

The `PostgresHAStack` provisions two EC2 instances across two AZs, a DynamoDB table for Patroni consensus, and an S3 bucket for backups.

### AWS deployment

```sh
cdk deploy PostgresHAStack
./setup.sh PostgresHAStack
ansible-playbook -i inventories/PostgresHAStack.yml playbooks/pg_patroni.yml
ansible-playbook -i inventories/PostgresHAStack.yml playbooks/pg_backup.yml
```

### Local HA testing (Raft DCS, no DynamoDB required)

```sh
ssh-keygen -t ed25519 -f ansible_key -N ""
docker compose -f docker-compose.ha.yml up --build
ansible-playbook -i inventories/docker_ha.yml playbooks/pg_patroni.yml
```

The local inventory uses Patroni's built-in Raft consensus (`patroni_use_raft: true`) instead of DynamoDB, so no extra containers are needed.

### Manual switchover

```sh
ansible-playbook -i inventories/PostgresHAStack.yml playbooks/pg_switchover.yml
```

### Verification

1. **Cluster health**: `patronictl -c /etc/patroni/patroni.yml list` — both nodes visible, one Leader and one Replica
2. **Replication**: Create a table on the leader; verify it appears on the replica
3. **Automatic failover**: Stop the leader's Patroni service; verify the replica promotes within ~30 seconds
4. **Switchover**: Run `pg_switchover.yml`; verify leadership transfers cleanly
5. **Backups**: Check `/var/log/pg_backup.log` on both nodes — only the primary should run backups
