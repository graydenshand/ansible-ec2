import typing as t

import aws_cdk as cdk
from constructs import Construct

from common.constructs import Ec2Instance, public_vpc


class HelloWorldStack(cdk.Stack):
    """Single EC2 instance for verifying Ansible connectivity."""

    def __init__(self, scope: Construct, id: str, **kwargs: t.Any) -> None:
        super().__init__(scope, id, **kwargs)

        vpc = public_vpc(self)
        instance = Ec2Instance(self, "HelloWorldInstance", vpc=vpc)

        cdk.CfnOutput(self, "KeyPairPrivateKeyParameterName", value=instance.key_pair_parameter_name)
        cdk.CfnOutput(self, "InstancePublicIp", value=instance.public_ip)
