`The purpose of this project is configuring AWS EC2 instances using Ansible.

`docker-compose.yml` runs a testing environment that emulates an ec2 for local development and testing.

`images`: docker images.

`inventories`: ansible inventories.

`playbooks` contains ansible playbooks
- `hello_world.yml`: hello world script to verify configuration
- `pg_install.yml`: install and start postgres
- `pg_backup.yml`: configure scheduled pg_dump backups to S3 (requires `pg_backup_bucket` in inventory)

`templates/pg_backup.sh.j2`: Jinja2 template for the backup shell script deployed by `pg_backup.yml`.

`main.py`: an AWS CDK stack that deploys an ec2 instance

`setup.sh`: a post-deploy script that parses outputs from cloud formation stack, downloads the ssh key, and builds an ansible inventory.

As you make changes, keep README.md and CLAUDE.md (this file) up to date.
