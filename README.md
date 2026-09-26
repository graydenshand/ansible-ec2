# ansible-ec2

AWS EC2 deployments configured with Ansible. Each service lives in its own directory under `services/` with its own CDK stack, playbooks, inventories, and setup script.

## Prerequisites

```sh
uv sync   # or: pip install -e .
```

## Services

| Service | Stack | Description |
|---|---|---|
| [hello_world](services/hello_world/README.md) | `HelloWorldStack` | Minimal EC2 instance for verifying Ansible connectivity |
| [postgres](services/postgres/README.md) | `PostgresStack` | Single-node PostgreSQL with S3 backups |
| [postgres_ha](services/postgres_ha/README.md) | `PostgresHAStack` | Two-node HA PostgreSQL with Patroni + DynamoDB |

## Usage

Deploy a stack and run its setup script to download the SSH key and generate an inventory:

```sh
cdk deploy <StackName>
./setup.sh <StackName>
```

Then run playbooks from the service directory. See each service's README for details.

## Local testing

Each service includes a `docker-compose.yml` that emulates the EC2 environment locally.

```sh
ssh-keygen -t ed25519 -f ansible_key -N ""
docker compose -f services/postgres/docker-compose.yml up --build
```

## Project structure

```
services/
  hello_world/   # connectivity test
  postgres/      # single-node PostgreSQL
  postgres_ha/   # two-node HA PostgreSQL
common/          # shared CDK constructs (Ec2Instance, public_vpc)
main.py          # CDK app entry point
setup.sh         # dispatcher → calls services/<name>/setup.sh
```
