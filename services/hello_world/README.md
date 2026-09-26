# hello_world

A minimal EC2 instance used to verify that Ansible can connect and run tasks. Useful for validating SSH key setup and inventory configuration before deploying a more complex service.

## AWS deployment

```sh
cdk deploy HelloWorldStack
./setup.sh HelloWorldStack
```

`setup.sh` downloads the SSH key and generates an inventory at `inventories/HelloWorldStack.yml`, then runs the hello_world playbook to confirm connectivity.

## Local testing

```sh
ssh-keygen -t ed25519 -f ansible_key -N ""
docker compose -f ../postgres/docker-compose.yml up --build
ansible-playbook -i ../postgres/inventories/docker.yml playbooks/hello_world.yml
```

The hello_world playbook has no service-specific dependencies, so it can run against any inventory.

## Playbooks

### `playbooks/hello_world.yml`

Pings all hosts and prints a message. No side effects.

```sh
ansible-playbook -i inventories/HelloWorldStack.yml playbooks/hello_world.yml
```
