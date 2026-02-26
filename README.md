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
