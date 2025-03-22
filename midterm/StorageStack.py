# CDK stack include s3 bucket: bucket_src, bucket_dest, and DynamoTableT
from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
)
from constructs import Construct

class StorageStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # S3 Bucket: Source
        self.bucket_src = s3.Bucket(
            self,
            "BucketSrc",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # S3 Bucket: Destination
        self.bucket_dst = s3.Bucket(
            self, 
            "BucketDest",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # Expose the bucket ARNs
        self.bucket_src_arn = self.bucket_src.bucket_arn
        self.bucket_dst_arn = self.bucket_dst.bucket_arn

        # DynamoDB Table
        self.table = dynamodb.Table(
            self,
            "DynamoTableT",
            partition_key=dynamodb.Attribute(
                name="SrcObjName",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="CreatedAtTimestamp",
                type=dynamodb.AttributeType.NUMBER
            ),
            removal_policy=RemovalPolicy.DESTROY
        )

        # Add Global Secondary Index for disowned copies
        self.table.add_global_secondary_index(
            index_name="DisownedCopiesIndex",
            partition_key=dynamodb.Attribute(
                name="IsDisowned",
                type=dynamodb.AttributeType.NUMBER),  # Store as 1/0
            sort_key=dynamodb.Attribute(
                name="DisownedAtTimestamp",
                type=dynamodb.AttributeType.NUMBER),
            projection_type=dynamodb.ProjectionType.ALL
        )


