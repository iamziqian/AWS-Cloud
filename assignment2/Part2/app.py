import aws_cdk as cdk
from s3_size_tracking_stack import S3SizeTrackingStack

app = cdk.App()
S3SizeTrackingStack(app, "S3SizeTrackingStack")

app.synth()