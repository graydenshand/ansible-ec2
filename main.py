import typing as t

import aws_cdk as cdk
from constructs import Construct


class Ec2Instance(Construct):
    """A high level EC2 instance construct."""

    def __init__(
        self,
        scope: Construct,
        id: str,
        vpc: cdk.aws_ec2.IVpc,
        instance_type: cdk.aws_ec2.InstanceType = cdk.aws_ec2.InstanceType("t4g.micro"),
        volume: cdk.aws_ec2.BlockDeviceVolume | None = None,
        public_ports: t.Iterable[int] | None = None,
        **kwargs: t.Any,
    ) -> None:
        super().__init__(scope, id, **kwargs)
        self.key_pair = cdk.aws_ec2.KeyPair(
            self,
            "KeyPair",
            type=cdk.aws_ec2.KeyPairType.ED25519,
            format=cdk.aws_ec2.KeyPairFormat.PEM,
        )

        block_devices = []
        if volume is not None:
            block_devices.append(
                cdk.aws_ec2.BlockDevice(
                    device_name="/dev/xvda",
                    volume=volume,
                )
            )

        self.instance = cdk.aws_ec2.Instance(
            self,
            "Ec2Instance",
            instance_type=instance_type,
            machine_image=cdk.aws_ec2.MachineImage.latest_amazon_linux2023(
                cpu_type=cdk.aws_ec2.AmazonLinuxCpuType.ARM_64
            ),
            vpc=vpc,
            key_pair=self.key_pair,
            block_devices=block_devices,
        )

        self.instance.connections.allow_from_any_ipv4(
            cdk.aws_ec2.Port.tcp(5432), "Allow PostgreSQL access from anywhere"
        )

        self.instance.connections.allow_from_any_ipv4(
            cdk.aws_ec2.Port.tcp(22), "Allow SSH access from anywhere"
        )

        self.key_pair_parameter_name = self.key_pair.private_key.parameter_name
        self.public_ip = self.instance.instance_public_ip


if __name__ == "__main__":
    app = cdk.App()

    stack = cdk.Stack(app, "PostgresStack")
    vpc = cdk.aws_ec2.Vpc(
        stack,
        "VPC",
        max_azs=2,
        nat_gateways=0,
        subnet_configuration=[
            cdk.aws_ec2.SubnetConfiguration(
                name="Public", subnet_type=cdk.aws_ec2.SubnetType.PUBLIC
            )
        ],
    )
    instance = Ec2Instance(
        stack,
        "PostgresInstance",
        vpc=vpc,
        volume=cdk.aws_ec2.BlockDeviceVolume.ebs(20),
        public_ports=[22, 5432],
    )
    cdk.CfnOutput(
        stack,
        "KeyPairPrivateKeyParameterName",
        value=instance.key_pair_parameter_name,
    )
    cdk.CfnOutput(stack, "InstancePublicIp", value=instance.public_ip)

    app.synth()
