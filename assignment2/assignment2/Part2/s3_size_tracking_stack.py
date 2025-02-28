# CDK stack includes S3 bucket, dynamodb table, lambda function, s3 event trigger
from aws_cdk import (
    Stack,
    RemovalPolicy,
    Duration,
    CfnOutput,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_s3_notifications as s3n,
)
from constructs import Construct

class S3SizeTrackingStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create S3 bucket
        self.bucket = s3.Bucket(
            self, "violet-test-bucket-ziqianfu-part2",
            removal_policy=RemovalPolicy.DESTROY,  # Bucket will be deleted when the stack is deleted
            auto_delete_objects=True)              # Automatically delete objects in the bucket

        # Create DynamoDB table
        self.table = dynamodb.Table(
            self, "S3-object-size-history-part2",
            partition_key=dynamodb.Attribute(
                name="bucket_name",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            stream=dynamodb.StreamViewType.NEW_IMAGE,  # Enables DynamoDB Streams
            removal_policy=RemovalPolicy.RETAIN,
            read_capacity=5,
            write_capacity=5
        )

        # Create Lambda function
        lambda_role = iam.Role(
            self, "S3SizeTrackingRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )

        # First Lambda function (tracking_lambda)
        tracking_lambda = _lambda.Function(
            self, "TrackingLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="tracking_lambda.lambda_handler",  # Refers to tracking_lambda.py
            code=_lambda.Code.from_asset("lambda"), 
            environment={
                "TABLE_NAME": self.table.table_name
            },
            role=lambda_role
        )

        # Grant permissions to tracking_lambda
        self.bucket.grant_read(tracking_lambda)
        self.table.grant_write_data(tracking_lambda)

        # Add S3 event trigger for object creation
        self.bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,    
            s3n.LambdaDestination(tracking_lambda)
        )

        # Add S3 event trigger for all object removal events
        self.bucket.add_event_notification(
            s3.EventType.OBJECT_REMOVED,    
            s3n.LambdaDestination(tracking_lambda)
        )

        # Add S3 event trigger for all object restore events
        self.bucket.add_event_notification(
            s3.EventType.OBJECT_RESTORE_POST,  # Restore request initiated
            s3n.LambdaDestination(tracking_lambda)
        )

        self.bucket.add_event_notification(
            s3.EventType.OBJECT_RESTORE_COMPLETED,  # Restore request completed
            s3n.LambdaDestination(tracking_lambda)
        )

        # Third Lambda function (driver_lambda)
        driver_lambda = _lambda.Function(
            self, 'DriverLambda',
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler='driver_lambda.lambda_handler',
            code=_lambda.Code.from_asset('lambda'),
            timeout=Duration.seconds(40),
            environment={
                "S3_BUCKET_NAME": self.bucket.bucket_name
            }
        )

        # Grant permissions to driver_lambda
        self.bucket.grant_read_write(driver_lambda) 

        hostname = "lp7b3dnccd" # update with your API Gateway hostname

        driver_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["execute-api:Invoke"],  # Action to invoke the API Gateway
                resources=[f"arn:aws:execute-api:us-west-1:180294206164:{hostname}/*/GET/plot"]
            )
        )

        CfnOutput(self, "LambdaFunctionName", value=driver_lambda.function_name)
        CfnOutput(self, "BucketName", value=self.bucket.bucket_name)

