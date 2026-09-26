import aws_cdk as cdk

from services.hello_world.stack import HelloWorldStack
from services.postgres.stack import PostgresStack
from services.postgres_ha.stack import PostgresHAStack

if __name__ == "__main__":
    app = cdk.App()
    HelloWorldStack(app, "HelloWorldStack")
    PostgresStack(app, "PostgresStack")
    PostgresHAStack(app, "PostgresHAStack")
    app.synth()
