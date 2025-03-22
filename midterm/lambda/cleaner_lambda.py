import os
import time
import boto3
from boto3.dynamodb.conditions import Key

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
dst_bucket = os.environ['DEST_BUCKET']
table = dynamodb.Table(os.environ["DYNAMO_TABLE"])

def lambda_handler(event, context):
    current_time = int(time.time())
    expiry_time = current_time - 10

    last_evaluated_key = None
    while True:
        query_params = {
            "IndexName": "DisownedCopiesIndex",
            "KeyConditionExpression": Key("IsDisowned").eq(1) & Key("DisownedAtTimestamp").lte(expiry_time),
        }
        if last_evaluated_key:
            query_params["ExclusiveStartKey"] = last_evaluated_key

        response = table.query(**query_params)

        # Delete S3 objects and DynamoDB entries
        for item in response.get("Items", []):
            try:
                # Delete from S3
                s3.delete_object(Bucket=dst_bucket, Key=item["DstObjName"])
                # Delete from DynamoDB
                table.delete_item(
                    Key={
                        "SrcObjName": item["SrcObjName"],
                        "CreatedAtTimestamp": item["CreatedAtTimestamp"],
                    }
                )
            except Exception as e:
                print(f"Error deleting {item['DstObject']}: {str(e)}")

        # Check for pagination
        last_evaluated_key = response.get("LastEvaluatedKey")
        if not last_evaluated_key:
            break