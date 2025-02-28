# CDK stack includes a dynamodb table, dynamodb table trigger, and lambda function
from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    aws_apigateway as apigw,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_lambda_event_sources as event_sources,
)
from constructs import Construct

class S3ObjectSizeHistoryPlottingStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, table_stack: Stack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        table = table_stack.table
        stream_arn = table.table_stream_arn  # Access the stream ARN

        # Pre-built Matplotlib Layer (replace ARN with your region's version)
        matplotlib_layer = _lambda.LayerVersion.from_layer_version_arn(
            self,
            "MatplotlibLayer",
            "arn:aws:lambda:us-west-1:770693421928:layer:Klayers-p39-matplotlib:1"
        )

        # Create Lambda function
        lambda_role = iam.Role(
            self, "PlottingLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ],
            description="Role for PlottingLambda to access DynamoDB stream",
        )

        # Grant permission for Lambda function to access DynamoDB stream and query the table
        table.grant_stream_read(lambda_role)
        table.grant_read_data(lambda_role)

        # Create an IAM policy to allow s3:PutObject on the specific bucket/folder
        lambda_policy = iam.PolicyStatement(
            actions=["s3:PutObject"],
            resources=[f"arn:aws:s3:::{table_stack.bucket.bucket_name}/plot/*"]
        )

        # Attach the policy directly to the Lambda function's role
        lambda_role.add_to_policy(lambda_policy)

        plotting_lambda = _lambda.Function(
            self,
            "PlottingLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="plotting_lambda.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            timeout=Duration.seconds(40),
            memory_size=512,
            role=lambda_role,
            environment={
                "TABLE_NAME": table.table_name,
                "S3_BUCKET_NAME": table_stack.bucket.bucket_name
            },
            layers=[matplotlib_layer],  # Add the Matplotlib layer
        )

        # Create API Gateway
        api = apigw.LambdaRestApi(
            self, "PlottingApi",
            handler=plotting_lambda,
            proxy=False  # Set to False to define custom routes
        )

        # Define a specific endpoint for plotting
        plot_resource = api.root.add_resource("plot")
        plot_resource.add_method("GET")

        # Output the API Gateway URL
        CfnOutput(self, "APIEndpoint", value=api.url)

        # I originally use DynamoDB Stream as trigger for the plotting Lambda, untill i see the last sentence...
        
        # Add DynamoDB Stream as an event source to the Lambda function
        # plotting_lambda.add_event_source(event_sources.DynamoEventSource(
        #     table,
        #     starting_position=_lambda.StartingPosition.LATEST, # Only trigger on new inserts
        #     batch_size=5,
        #     retry_attempts=2
        # ))