# Getting started

Install the package: uv sync / pip install

Deploy the infrastructure using the CDK app in main.py.

Run the setup.sh script to generate an inventory and download the ssh key needed to connect to the instance.

Run ansible playbooks.

```sh
ansible-playbook -i inventories/inventory.yml playbooks/hello_world.yml
```

## Development container

You can als run a local docker container emulating the AmazonLinux2023 environment used in the ec2 deployment.

First you will need to generate an ssh key for testing. Then build and run the docker-compose file, and (in a separate shell) run an ansible playbook using the docker.yml inventory.

```
ssh-keygen -t ed25519 -f ansible_key -N ""
docker compose up --build
ansible-playbook -i inventories/docker.yml playbooks/hello_world.yml
```

## Playbooks

- playbooks/pg_install.yml: Install and start a postgres server that you can connect to remotely
- playbooks/pg_backup.yml: Configure scheduled pg_dump backups to S3

### pg_backup.yml

Installs AWS CLI, deploys `/usr/local/bin/pg_backup.sh`, and sets up a cron job (runs as `postgres`, default: 3 AM daily). Requires `pg_backup_bucket` to be set in the inventory (populated automatically by `setup.sh` after `cdk deploy`).

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
