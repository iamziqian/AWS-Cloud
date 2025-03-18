from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_iam as iam,
)
from constructs import Construct


class DriverLambdaStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, storage_stack: Stack, api_stack: Stack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        bucket = storage_stack.bucket
        api = api_stack.api

        # create driver lambda
        driver_lambda = _lambda.Function(
            self,
            "DriverLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="driver_lambda.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            timeout=Duration.seconds(40),
            environment= {
                "S3_BUCKET_NAME": bucket.bucket_name,
                "API_ENDPOINT": api.url
            }
        )

        # grant permissions
        bucket.grant_read_write(driver_lambda)

        api_arn = f"arn:aws:execute-api:{self.region}:{self.account}:{api.rest_api_id}/*"
        driver_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["execute-api:Invoke"],  # Action to invoke the API Gateway
                resources=[api_arn]
            )
        )

