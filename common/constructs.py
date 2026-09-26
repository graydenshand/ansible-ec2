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
        key_pair: cdk.aws_ec2.IKeyPair | None = None,
        vpc_subnets: cdk.aws_ec2.SubnetSelection | None = None,
        **kwargs: t.Any,
    ) -> None:
        super().__init__(scope, id, **kwargs)
        if key_pair is None:
            self.key_pair = cdk.aws_ec2.KeyPair(
                self,
                "KeyPair",
                type=cdk.aws_ec2.KeyPairType.ED25519,
                format=cdk.aws_ec2.KeyPairFormat.PEM,
            )
        else:
            self.key_pair = key_pair

        block_devices = []
        if volume is not None:
            block_devices.append(
                cdk.aws_ec2.BlockDevice(
                    device_name="/dev/xvda",
                    volume=volume,
                )
            )

        instance_kwargs: dict[str, t.Any] = dict(
            instance_type=instance_type,
            machine_image=cdk.aws_ec2.MachineImage.latest_amazon_linux2023(
                cpu_type=cdk.aws_ec2.AmazonLinuxCpuType.ARM_64
            ),
            vpc=vpc,
            key_pair=self.key_pair,
            block_devices=block_devices,
        )
        if vpc_subnets is not None:
            instance_kwargs["vpc_subnets"] = vpc_subnets

        self.instance = cdk.aws_ec2.Instance(self, "Ec2Instance", **instance_kwargs)

        self.instance.connections.allow_from_any_ipv4(
            cdk.aws_ec2.Port.tcp(5432), "Allow PostgreSQL access from anywhere"
        )

        self.instance.connections.allow_from_any_ipv4(
            cdk.aws_ec2.Port.tcp(22), "Allow SSH access from anywhere"
        )

        self.key_pair_parameter_name = self.key_pair.private_key.parameter_name
        self.public_ip = self.instance.instance_public_ip
        self.private_ip = self.instance.instance_private_ip


def public_vpc(scope: Construct) -> cdk.aws_ec2.Vpc:
    vpc = cdk.aws_ec2.Vpc(
        scope,
        "VPC",
        max_azs=2,
        nat_gateways=0,
        subnet_configuration=[
            cdk.aws_ec2.SubnetConfiguration(
                name="Public", subnet_type=cdk.aws_ec2.SubnetType.PUBLIC
            )
        ],
    )
    vpc.add_gateway_endpoint("S3Endpoint", service=cdk.aws_ec2.GatewayVpcEndpointAwsService.S3)
    vpc.add_gateway_endpoint(
        "DynamoEndpoint", service=cdk.aws_ec2.GatewayVpcEndpointAwsService.DYNAMODB
    )
    return vpc
