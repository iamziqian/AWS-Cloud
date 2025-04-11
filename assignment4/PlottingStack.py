from aws_cdk import (
    Stack,
    Duration,
    aws_s3 as s3,
    aws_dynamodb as Dynamodb,
    aws_apigateway as apigw,
    aws_lambda as _lambda,
)
from constructs import Construct

class PlottingStack(Stack):
    def __init__(self, scope: Construct, construct_id: str,
                table_arn: str,
                test_bucket_arn: str,
                **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Import table and test bucket
        table = Dynamodb.Table.from_table_arn(self, "ImportedTable", table_arn)
        bucket = s3.Bucket.from_bucket_arn(self, "ImportedTestBucket", test_bucket_arn)
        
        # Pre-built Matplotlib Layer
        matplotlib_layer = _lambda.LayerVersion.from_layer_version_arn(
            self,
            "MatplotlibLayer",
            "arn:aws:lambda:us-west-1:770693421928:layer:Klayers-p310-matplotlib:4"
        )

        # create plotting lambda
        plotting_lambda = _lambda.Function(
            self,
            "PlottingLambda",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="plotting_lambda.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                "TABLE_NAME": table.table_name,
                "S3_BUCKET_NAME": bucket.bucket_name,
            },
            timeout=Duration.seconds(120),
            memory_size=512,
            layers=[matplotlib_layer],  # Add the Matplotlib layer
        )

        # grant permissions
        table.grant_read_data(plotting_lambda)
        bucket.grant_write(plotting_lambda)

        # create Api gateway
        api = apigw.LambdaRestApi(
            self, "PlottingApi",
            handler=plotting_lambda,
        )

        # add a resource to the API
        plot_resource = api.root.add_resource("plot")
        plot_resource.add_method("GET")

        # expose api endpoint as an instance variable
        self.api_endpoint = api.url
        self.api_arn = f"arn:aws:execute-api:{self.region}:{self.account}:{api.rest_api_id}/*"