import typing as t

import aws_cdk as cdk
from constructs import Construct


class PostgresInstance(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        vpc: cdk.aws_ec2.IVpc,
        instance_type: cdk.aws_ec2.InstanceType = cdk.aws_ec2.InstanceType("t4g.micro"),
        **kwargs: t.Any,
    ) -> None:
        super().__init__(scope, id, **kwargs)
        key_pair = cdk.aws_ec2.KeyPair(
            self,
            "KeyPair",
            type=cdk.aws_ec2.KeyPairType.ED25519,
            format=cdk.aws_ec2.KeyPairFormat.PEM,
        )

        volume = cdk.aws_ec2.BlockDeviceVolume.ebs(20)

        instance = cdk.aws_ec2.Instance(
            self,
            "Ec2Instance",
            instance_type=instance_type,
            machine_image=cdk.aws_ec2.MachineImage.latest_amazon_linux2023(
                cpu_type=cdk.aws_ec2.AmazonLinuxCpuType.ARM_64
            ),
            vpc=vpc,
            key_pair=key_pair,
            block_devices=[
                cdk.aws_ec2.BlockDevice(
                    device_name="/dev/xvda",
                    volume=volume,
                )
            ],
        )

        instance.connections.allow_from_any_ipv4(
            cdk.aws_ec2.Port.tcp(5432), "Allow PostgreSQL access from anywhere"
        )

        instance.connections.allow_from_any_ipv4(
            cdk.aws_ec2.Port.tcp(22), "Allow SSH access from anywhere"
        )

        cdk.CfnOutput(self, "KeyPairName", value=key_pair.key_pair_name)
        cdk.CfnOutput(
            self,
            "KeyPairPrivateKeyParameterName",
            value=key_pair.private_key.parameter_name,
        )
        cdk.CfnOutput(self, "InstancePublicIp", value=instance.instance_public_ip)


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
    PostgresInstance(stack, "PostgresInstance", vpc=vpc)

    app.synth()
