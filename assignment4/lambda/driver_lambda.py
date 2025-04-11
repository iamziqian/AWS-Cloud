import boto3
import time
import os
import urllib.request 

s3 = boto3.client('s3')
bucket_name = os.environ["S3_BUCKET_NAME"]

'''
P1  60s/ P2 60s
+19 +28 +2/ 0: 19 -> 47 -> 49 -> 21
+19 + 28 / +2: 19 -> 47 -> 19 -> 2
+19 / +28 + 2: 19 -> 28 -> 30 -> 2
'''

def lambda_handler(event, context):
    # create obj assignment1.txt in S3 bucket
    s3.put_object(
        Bucket=bucket_name,
        Key="assignment1.txt",
        Body="Empty Assignment 1 "
    )
    print("Created assignment1.txt with content 'Empty Assignment 1") #19 bytes

    time.sleep(5)

    # create obj assignment2.txt in S3 bucket
    s3.put_object(
        Bucket=bucket_name,
        Key="assignment2.txt",
        Body="Empty Assignment 2222222222 "
    )
    print("Created assignment2.txt with content 'Empty Assignment 2222222222 '") #28 bytes

    time.sleep(55)
    
    # (At this point, the alarm should fire and Cleaner should delete `assignment2.txt`

    # create obj assignment3.txt in S3 bucket
    s3.put_object(
        Bucket=bucket_name,
        Key="assignment3.txt",
        Body="33"
    )
    print("Created assignment3.txt with content '33'") #2 bytes

    time.sleep(55)
    # (At this point, the alarm should fire and Cleaner should delete `assignment1.txt`

    # Lastly, call the API exposed for the plotting lambda
    api_endpoint = os.environ["API_ENDPOINT"]
    if not api_endpoint:
        return {
            'statusCode': 500,
            'body': 'API_ENDPOINT environment variable is not set'
        }
    
    try:
        req = urllib.request.Request(api_endpoint, method="GET")
        
        # Send the request and get the response
        with urllib.request.urlopen(req) as response:
            api_response = response.read().decode()
            print(f"API Response: {api_response}")
            return {
                'statusCode': 200,
                'body': api_response
            }
    except Exception as e:
        print(f"Error calling the API: {e}")
        return {
            'statusCode': 500,
            'body': f"Error calling the API: {e}"
        }


    