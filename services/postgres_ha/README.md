# postgres_ha

Two-node HA PostgreSQL cluster using Patroni for automated failover. Nodes are placed in separate availability zones. A Network Load Balancer routes port 5432 to the current primary and port 5433 to the replica, using Patroni's REST API for health checks. DynamoDB is used as the distributed consensus store in production; Raft DCS is available for local testing without AWS dependencies.

## AWS deployment

```sh
cdk deploy PostgresHAStack
./setup.sh PostgresHAStack
```

`setup.sh` downloads the SSH key and generates an inventory at `inventories/PostgresHAStack.yml`.

Then deploy Patroni and configure backups:

```sh
ansible-playbook -i inventories/PostgresHAStack.yml playbooks/pg_patroni.yml
ansible-playbook -i inventories/PostgresHAStack.yml ../postgres/playbooks/pg_backup.yml
```

## Local testing (Raft DCS, no DynamoDB required)

```sh
ssh-keygen -t ed25519 -f ansible_key -N ""
docker compose -f docker-compose.ha.yml up --build
ansible-playbook -i inventories/docker_ha.yml playbooks/pg_patroni.yml
```

The local inventory sets `patroni_use_raft: true`, enabling Patroni's built-in Raft consensus instead of DynamoDB.

## Playbooks

### `playbooks/pg_patroni.yml`

Installs PostgreSQL 17 and Patroni, deploys the Patroni configuration and systemd unit, and starts the cluster. Prompts for passwords for the `postgres` and `replicator` users.

```sh
ansible-playbook -i inventories/PostgresHAStack.yml playbooks/pg_patroni.yml
```

### `playbooks/pg_switchover.yml`

Performs a manual leader switchover via `patronictl`. Prompts for the target node name.

```sh
ansible-playbook -i inventories/PostgresHAStack.yml playbooks/pg_switchover.yml
```

### `../postgres/playbooks/pg_backup.yml`

See [postgres/README.md](../postgres/README.md#playbookspg_backupyml). The backup script's leader-check guard ensures backups only run on the current primary.

## Verification

1. **Cluster health**: `patronictl -c /etc/patroni/patroni.yml list` — both nodes visible, one Leader and one Replica
2. **Replication**: Create a table on the leader; verify it appears on the replica
3. **Automatic failover**: Stop the leader's Patroni service; verify the replica promotes within ~30 seconds
4. **Switchover**: Run `pg_switchover.yml`; verify leadership transfers cleanly
5. **Backups**: Check `/var/log/pg_backup.log` on both nodes — only the primary should run backups
