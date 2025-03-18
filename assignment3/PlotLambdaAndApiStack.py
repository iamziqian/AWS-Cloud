from aws_cdk import (
    Stack,
    Duration,
    aws_apigateway as apigw,
    aws_lambda as _lambda,
    CfnOutput,
)
from constructs import Construct

class PlotLambdaAndApiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, storage_stack: Stack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        table = storage_stack.table
        bucket = storage_stack.bucket
        
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
            timeout=Duration.seconds(40),
            memory_size=512,
            layers=[matplotlib_layer],  # Add the Matplotlib layer
        )

        # grant permissions
        table.grant_read_data(plotting_lambda)
        bucket.grant_write(plotting_lambda)

        # create Api gateway
        self.api = apigw.LambdaRestApi(
            self, "PlottingApi",
            handler=plotting_lambda,
        )

        # add a resource to the API
        plot_resource = self.api.root.add_resource("plot")
        plot_resource.add_method("GET")

        # expose api endpoint
        api_endpoint = self.api.url
        CfnOutput(self, "APIEndpoint", value=api_endpoint)  # Output the API endpoint URL
