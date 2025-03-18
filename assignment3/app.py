#!/usr/bin/env python3
import os
import aws_cdk as cdk

from StorageAndSizeTrackingLambdaStack import StorageAndSizeTrackingLambdaStack
from PlotLambdaAndApiStack import PlotLambdaAndApiStack
from DriverLambdaStack import DriverLambdaStack

app = cdk.App()
storage_and_size_tracking_lambda_stack = StorageAndSizeTrackingLambdaStack(app, "StorageAndSizeTrackingLambdaStack", env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),)

plot_lambda_and_api_stack = PlotLambdaAndApiStack(app, "PlotLambdaAndApiStack", storage_and_size_tracking_lambda_stack, env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),)

driver_lambda_stack = DriverLambdaStack(app, "DriverLambdaStack", storage_and_size_tracking_lambda_stack, plot_lambda_and_api_stack, env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),)

app.synth()
