# CDK stack includes S3 bucket, dynamodb table, lambda function, s3 event trigger
from aws_cdk import (
    Stack,
    RemovalPolicy,
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
        bucket = s3.Bucket(
            self, "violet-test-bucket-ziqianfu-part2",
            removal_policy=RemovalPolicy.DESTROY,  # Bucket will be deleted when the stack is deleted
            auto_delete_objects=True)              # Automatically delete objects in the bucket

        # Create DynamoDB table
        table = dynamodb.Table(
            self, "S3-object-size-history-part2",
            partition_key=dynamodb.Attribute(
                name="bucket_name",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
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

        lambda_function = _lambda.Function(
            self, "sizeTrackingLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                "TABLE_NAME": table.table_name
            },
            role=lambda_role
        )

        # Grant permissions
        bucket.grant_read(lambda_function)
        table.grant_write_data(lambda_function)

        # Add S3 event trigger for object creation
        bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,    
            s3n.LambdaDestination(lambda_function)
        )

        # Add S3 event trigger for all object removal events
        bucket.add_event_notification(
            s3.EventType.OBJECT_REMOVED,    
            s3n.LambdaDestination(lambda_function)
        )

        # Add S3 event trigger for all object restore events
        bucket.add_event_notification(
            s3.EventType.OBJECT_RESTORE_POST,  # Restore request initiated
            s3n.LambdaDestination(lambda_function)
        )

        bucket.add_event_notification(
            s3.EventType.OBJECT_RESTORE_COMPLETED,  # Restore request completed
            s3n.LambdaDestination(lambda_function)
        )