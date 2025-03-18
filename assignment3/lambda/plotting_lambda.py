# Plotting lambda function trigger to query dynamodb table and generate plot
from datetime import datetime, timedelta
import os
import boto3
import matplotlib.pyplot as plt
import numpy as np
import json

dynamodb = boto3.client("dynamodb")
s3 = boto3.client("s3")

table_name = os.environ['TABLE_NAME'] 
bucket_name = os.environ["S3_BUCKET_NAME"]
PLOT_FILE = "/tmp/size_history_plot.png"

def get_max_bucket_size(bucket_name):
    max_size = 0
    last_evaluated_key = None

    while True:
        if last_evaluated_key:
            response = dynamodb.query(
                TableName=table_name,
                KeyConditionExpression="bucket_name = :bucket_name",
                ExpressionAttributeValues={
                    ":bucket_name": {"S": bucket_name}
                },
                ExclusiveStartKey=last_evaluated_key
            )
        else:
            response = dynamodb.query(
                TableName=table_name,
                KeyConditionExpression="bucket_name = :bucket_name",
                ExpressionAttributeValues={
                    ":bucket_name": {"S": bucket_name}
                }
            )
            
            for item in response['Items']:
                size = int(item['bucket_size']['N'])
                if size > max_size:
                    max_size = size

            last_evaluated_key = response.get('LastEvaluatedKey')
            if not last_evaluated_key:
                break

    return max_size

    
def lambda_handler(event, context):
    current_time = datetime.utcnow() # Get current time in UTC
    print("event query at: ", current_time)

    # query items in table for last 20 second
    threshold_time = current_time - timedelta(seconds=20)
    threshold_time_str = threshold_time.strftime("%Y-%m-%d %H:%M:%S")
    print("threshold time: ", threshold_time)

    # Retrieve the bucket size from the DynamoDB table
    response = dynamodb.query(
        TableName=table_name,
        KeyConditionExpression="bucket_name = :bucket_name AND #ts >= :threshold_time",
        ExpressionAttributeValues={
            ":bucket_name": {"S": bucket_name},
            ":threshold_time": {"S": threshold_time_str}
        },
        ExpressionAttributeNames={"#ts": "timestamp"},   # map timestamp to #ts
        ScanIndexForward=True  # ascending (oldest to newest)
    )

    print("response: ", response)
    print("response length: ", len(response['Items']))

    size_data = []
    timestamps = []

    for item in response['Items']:
        # Extract bucket size and timestamp from each item
        print("item: ", item)
        
        sizeData = item['bucket_size']['N']
        timestamp = item['timestamp']['S']

        print("ADD item bucket_size: ", sizeData)
        print("ADD item timestamp: ", timestamp)

        size_data.append(int(sizeData))                 #convert str to int
        timestamps.append(timestamp.split('.')[0])      # remove milliseconds

    print("ENDED size_data: ", size_data)
    print("ENDED timestamps: ", timestamps)

    if len(size_data) == 0:
        print("No data found for the last 20 seconds.")
        return {"status": "No size_data produced"}
    
    # Get the maximum bucket size in history
    max_bucket_size = get_max_bucket_size(bucket_name)
    print(f"Maximum bucket size in history: {max_bucket_size}")

    # Generate and store the plot
    timestamp_objects = [datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") for ts in timestamps]

    plt.figure(figsize=(10, 5))
    plt.plot(timestamp_objects, size_data, marker="o", linestyle="-", color="b", label="Bucket Size")
    
    # Add a horizontal line for the maximum bucket size
    plt.axhline(y=max_bucket_size, color="r", linestyle="--", label="Max Bucket Size")

    # Adjust the y-axis limits 
    plt.ylim(min(size_data) - 1, max_bucket_size + 20)
    plt.yticks(np.arange(min(size_data) - 0.5, max_bucket_size + 10, 10))

    plt.xlabel("Timestamp")
    plt.ylabel("Bucket Size")
    plt.title("S3 Bucket Size History (Last 20s)")
    plt.legend()
    plt.grid()
    plt.xticks(rotation=45)

    # Debug
    print("Plot data - Timestamps:", timestamps)
    print("Plot data - Size data:", size_data)

    plt.savefig(PLOT_FILE)  # Save locally in Lambda's temp storage
    print(f"Plot saved locally at {PLOT_FILE}")

    # Upload the plot to S3
    plot_key = "plot/size_history_plot.png"
    try:
        s3.upload_file(PLOT_FILE, bucket_name, plot_key)
        print(f"Plot uploaded to S3://{bucket_name}/{plot_key}")

    except Exception as e:
        print(f"Error uploading plot to S3: {e}")
        return {
            "status": "Error",
            "message": f"Failed to upload plot to S3: {e}"
        } 

    # Return success response 
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "status": "Success",
            "s3_path": f"s3://{bucket_name}/{plot_key}",
            "max_bucket_size": max_bucket_size
        })
    }