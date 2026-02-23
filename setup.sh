# This script fetches the PublicIP address and SSH Key for an Ec2 stack.
# It adds the host to the known hosts file and saves the SSH key to the .ssh directory.
# Aside from adding the host to inventory.yml, this is everything needed for ansible
# to connect to the host and run playbooks.
read -p "Enter the stack name: "

RHOST=$(aws cloudformation describe-stacks --stack-name PostgresStack --query "Stacks[0].Outputs[?contains(OutputKey, 'InstancePublicIp')].OutputValue | [0]" --output text)
KEY_NAME=$(aws cloudformation describe-stacks --stack-name PostgresStack --query "Stacks[0].Outputs[?contains(OutputKey, 'ParameterName')].OutputValue | [0]" --output text)


chmod u+w ~/.ssh/pg-hosting.pem
aws ssm get-parameter --name $KEY_NAME --with-decryption --query "Parameter.Value" --output text > ~/.ssh/pg-hosting.pem
chmod 400 ~/.ssh/pg-hosting.pem

# Add host to known hosts
ssh-keyscan -H $RHOST >> ~/.ssh/known_hosts
