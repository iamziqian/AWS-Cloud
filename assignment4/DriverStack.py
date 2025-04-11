from aws_cdk import (
    Stack,
    Duration,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_iam as iam,
)
from constructs import Construct

class DriverStack(Stack):
    def __init__(self, scope: Construct, id: str, 
                test_bucket_arn: str,
                api_endpoint: str,
                api_arn: str,
                **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Get S3 bucket objects from ARN
        test_bucket = s3.Bucket.from_bucket_arn(self, "ImportedTestBucket", test_bucket_arn)

        # create driver lambda
        driver_lambda = _lambda.Function(
            self,
            "DriverLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="driver_lambda.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            timeout=Duration.seconds(120),
            environment={
                "S3_BUCKET_NAME": test_bucket.bucket_name,
                "API_ENDPOINT": api_endpoint
            }
        )

        # grant permissions
        test_bucket.grant_read_write(driver_lambda)

        driver_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["execute-api:Invoke"],  # Action to invoke the API Gateway
                resources=[api_arn]
            )
        )

        