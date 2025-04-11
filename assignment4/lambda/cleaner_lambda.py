import boto3
import logging
import os

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize S3 client
s3_client = boto3.client('s3')

def lambda_handler(event, context):
    """
    Lambda function to delete largest obj in the TestBucket
    """
    # get the bucket name from the environment variable
    bucket_name = os.environ.get("TEST_BUCKET")
    if not bucket_name:
        logger.error("TEST_BUCKET environment variable is not set.")
        return {
            "statusCode": 500,
            "body": "TEST_BUCKET environment variable is not set."
        }
    
    try:
        # list objs in the bucket
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        if 'Contents' not in response:
            logger.info("Bucket is empty.")
            return {
                "statusCode": 200,
                "body": "No objects found in the bucket."
            }
        
        # Filter out objects with the "plot/" prefix
        filtered_objects = [
            obj for obj in response['Contents']
            if not obj['Key'].startswith("plot/")
        ]

        
        # find the largest object
        largest_object = max(filtered_objects, key=lambda obj: obj['Size'])
        largest_object_key = largest_object['Key']
        largest_object_size = largest_object['Size']

        logger.info(f"Largest object found: {largest_object_key}, Size: {largest_object_size} bytes")

        # delete the largest object
        s3_client.delete_object(Bucket=bucket_name, Key=largest_object_key)
        logger.info(f"Deleted largest object: {largest_object_key}")

        return {
            "statusCode": 200,
            "body": f"Deleted largest object: {largest_object_key}"
        }
    
    except Exception as e:
        logger.error(f"Error deleting largest object: {str(e)}")
        return {
            "statusCode": 500,
            "body": f"Error deleting largest object: {str(e)}"
        }
