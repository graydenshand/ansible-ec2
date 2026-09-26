# postgres

Single-node PostgreSQL deployment on EC2. Includes automated pg_dump backups to S3.

## AWS deployment

```sh
cdk deploy PostgresStack
./setup.sh PostgresStack
```

`setup.sh` downloads the SSH key and generates an inventory at `services/postgres/inventories/PostgresStack.yml`.

Then install and configure PostgreSQL:

```sh
ansible-playbook -i services/postgres/inventories/PostgresStack.yml services/postgres/playbooks/pg_install.yml
ansible-playbook -i services/postgres/inventories/PostgresStack.yml services/postgres/playbooks/pg_backup.yml
```

## Local testing

```sh
ssh-keygen -t ed25519 -f ansible_key -N ""
docker compose -f docker-compose.yml up --build
ansible-playbook -i services/postgres/inventories/docker.yml ../../services/hello_world/services/postgres/playbooks/hello_world.yml
ansible-playbook -i services/postgres/inventories/docker.yml services/postgres/playbooks/pg_install.yml
```

## Playbooks

### `services/postgres/playbooks/pg_install.yml`

Installs PostgreSQL 17, initializes the data directory, configures remote access, and starts the service. Prompts for a password for the `postgres` user.

```sh
ansible-playbook -i services/postgres/inventories/PostgresStack.yml services/postgres/playbooks/pg_install.yml
```

### `services/postgres/playbooks/pg_backup.yml`

Installs AWS CLI, deploys `/usr/local/bin/pg_backup.sh`, and configures a cron job (default: 3 AM daily, runs as `postgres`). Requires `pg_backup_bucket` in the inventory (set automatically by `setup.sh`).

The backup script checks the Patroni REST API at startup and skips execution on replica nodes, so this playbook is safe to run on HA clusters as well.

```sh
ansible-playbook -i services/postgres/inventories/PostgresStack.yml services/postgres/playbooks/pg_backup.yml
```

For local testing without S3:

```sh
ansible-playbook -i services/postgres/inventories/docker.yml services/postgres/playbooks/pg_backup.yml \
  -e pg_backup_dry_run=true -e pg_backup_bucket=test-bucket
```

Key variables:

| Variable | Default | Purpose |
|---|---|---|
| `pg_backup_databases` | `["postgres"]` | Databases to back up |
| `pg_backup_bucket` | *(from inventory)* | S3 bucket name |
| `pg_backup_s3_prefix` | `"backups"` | S3 key prefix |
| `pg_backup_cron_minute` | `"0"` | Cron minute |
| `pg_backup_cron_hour` | `"3"` | Cron hour |
| `pg_backup_dry_run` | `false` | Skip S3 upload |
