import boto3
import time
import os
import urllib.request # requests are not supported in cdk

s3 = boto3.client('s3')

bucket_name = os.environ["S3_BUCKET_NAME"]

def lambda_handler(event, context):
    # create obj assignment1.txt in S3 bucket
    s3.put_object(
        Bucket=bucket_name,
        Key="assignment1.txt",
        Body="Empty Assignment 1"
    )
    print("Created assignment1.txt with content 'Empty Assignment 1") #19 bytes

    time.sleep(2)

    # update obj assignment1.txt in S3 bucket
    s3.put_object(
        Bucket=bucket_name,
        Key="assignment1.txt",
        Body="Empty Assignment 2222222222"  # 28 bytes
    )
    print("Updated assignment1.txt with content 'Empty Assignment 2222222222'")

    time.sleep(2)

    # delete obj assignment1.txt in S3 bucket
    s3.delete_object(
        Bucket=bucket_name,
        Key="assignment1.txt"
    )
    print("Deleted assignment1.txt")

    time.sleep(2)

    # create obj assignment2.txt in S3 bucket
    s3.put_object(
        Bucket=bucket_name,
        Key="assignment2.txt",
        Body="33"
    )
    print("Created assignment2.txt with content '33'") #2 bytes

    # The API Gateway URL
    url = "https://lp7b3dnccd.execute-api.us-west-1.amazonaws.com/prod/plot"
    
    # Prepare the request
    req = urllib.request.Request(url, method="GET")
    
    try:
        # Send the request and get the response
        with urllib.request.urlopen(req) as response:
            api_response = response.read().decode()
            print(f"API Response: {api_response}")
    except Exception as e:
        print(f"Error calling the API: {e}")
    
    return {
        'statusCode': 200,
        'body': 'Operations completed successfully'
    }