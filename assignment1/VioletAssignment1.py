import boto3
import json
import time

# create user with permissions to assume roles
# @return credentials of the user
def create_iam_user(iam_client, username, DEV_ROLE_ARN, USER_ROLE_ARN):
  iam_client.create_user(UserName=username)
  print(f"IAM user {username} is created successfully!")
   
  # define assume role policy
  assume_role_policy = {
      "Version": "2012-10-17",
      "Statement": [
          {
              "Effect": "Allow",
              "Action": "sts:AssumeRole",
              "Resource": [DEV_ROLE_ARN, USER_ROLE_ARN]
          }
      ]
  }

  # grant users to assume the dev role
  iam_client.put_user_policy(
      UserName=username,
      PolicyName='AssumeRolePolicy',
      PolicyDocument=json.dumps(assume_role_policy)
  )

  # extract credentials of newly created user
  access_key_response = iam_client.create_access_key(UserName=username)
  access_key_id = access_key_response['AccessKey']['AccessKeyId']
  secret_access_key = access_key_response['AccessKey']['SecretAccessKey']

  print(f"{username}'s Access Key ID: {access_key_id}")
  print(f"{username}'s Secret Access Key: {secret_access_key}")

  return access_key_id, secret_access_key


# create role and attach policy to the role
def create_role(iam_client, role_name, trust_policy, policy_arn):
  iam_client.create_role(
      RoleName=role_name,
      AssumeRolePolicyDocument=json.dumps(trust_policy),
      Description=f"{role_name} role with s3 access"
  )

  # attach policy for role with access to s3
  iam_client.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
  print(f"Role {role_name} created and policy attached.")


# assume role and return credentials of the assumed role
def assume_role(sts_client, role_arn, session_name):
   response = sts_client.assume_role(RoleArn=role_arn, RoleSessionName=session_name)
   return response['Credentials']


# ---------- MAIN SCRIPT ----------
def main():
  # initialize accountID, region, username, role
  ACCOUNT_ID = "180294206164"
  REGION = "us-west-2"
  USERNAME = "VioletHasADream"
  DEV_ROLE_ARN = f"arn:aws:iam::{ACCOUNT_ID}:role/Dev"
  USER_ROLE_ARN = f"arn:aws:iam::{ACCOUNT_ID}:role/User"

  # initialize objects
  objects= [
      ("assignment1.txt", "Empty Assignment 1"),
      ("assignment2.txt", "Empty Assignment 2"),
      ("recording1.jpg", "/Users/ziqianfu/CS6620/CS6620/assignment1/Grace.jpg") 
  ]

  # initialize IAM client with IAM user session
  iam_client = boto3.client('iam')

  # create IAM user and get credentials
  access_key_id, secret_access_key = create_iam_user(iam_client, USERNAME, DEV_ROLE_ARN, USER_ROLE_ARN)

  # define trust policy
  trust_policy = {
    "Version": "2012-10-17",
    "Statement": [
          {
            "Effect": "Allow",
            "Action": "sts:AssumeRole",
            "Principal": {"AWS": f"arn:aws:iam::{ACCOUNT_ID}:user/{USERNAME}"}
          }
      ]
  }

  # Ensure IAM changes are propagated
  print("Waiting for IAM changes to propagate...")
  time.sleep(10)

  # create dev and user roles
  create_role(iam_client, "Dev", trust_policy, 'arn:aws:iam::aws:policy/AmazonS3FullAccess')
  create_role(iam_client, "User", trust_policy, 'arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess')

  # get a new user session to initialize sts client preparing for assuming role
  new_user_session = boto3.Session(aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key)
  sts = new_user_session.client('sts')

  # Ensure role changes and new user session are propagated
  print("Waiting for role changes and new user session to propagate...")
  time.sleep(10)

  # assume dev role and get a new dev role session to initialize s3 client
  print("Assuming dev role...")
  dev_role_credentials = assume_role(sts, DEV_ROLE_ARN, 'DevSession')
  dev_role_session = boto3.Session(dev_role_credentials['AccessKeyId'], dev_role_credentials['SecretAccessKey'], dev_role_credentials['SessionToken'])
  s3_client_dev = dev_role_session.client('s3', region_name='us-west-2')

  # dev role create bucket
  bucket_name=f"lecture1{int(time.time())}"

  s3_client_dev.create_bucket(
    Bucket=bucket_name,
    CreateBucketConfiguration={
          'LocationConstraint': 'us-west-2'
    }
  )
  print(f"{bucket_name} has been created successfully!")

  # create 2 txts and 1 jpg in the bucket lecture1
  for file_name, content in objects:
      try:
        if file_name.endswith(".txt"):
            s3_client_dev.put_object(Bucket=bucket_name, Key=file_name, Body=content)
            print(f"{file_name} is uploaded!")

        elif file_name.endswith(".jpg"):
            with open(content, 'rb') as img_file:
                s3_client_dev.put_object(Bucket=bucket_name, Key=file_name, Body=img_file)
            print(f"{file_name} is uploaded!")
    
      except Exception as e:
          print(f"Error uploading {file_name}: {e}")

  # assume user role and get a new user role session to initialize s3 client
  print("Assuming user role...")
  user_role_credentials = assume_role(sts, USER_ROLE_ARN, 'UserSession')
  user_role_session = boto3.Session(user_role_credentials['AccessKeyId'], user_role_credentials['SecretAccessKey'], user_role_credentials['SessionToken'])
  s3_client_user = user_role_session.client('s3', region_name='us-west-2')

  if s3_client_user:
    #  Find all the objects whose key has the prefix `assignment` and compute the total size of those objects.
    list_objects=s3_client_user.list_objects_v2(Bucket=bucket_name, Prefix="assignment")
    total_size_prefix_assignment_object = 0

    for obj in list_objects.get('Contents', []):
        total_size_prefix_assignment_object += obj['Size']
    print(f"Total size of objects with 'assignment' prefix is {total_size_prefix_assignment_object}!")
        

  # assume dev roles and get a new dev role session to initialize s3 client
  print("Assuming dev role...")
  dev_role_credentials = assume_role(sts, DEV_ROLE_ARN, 'DevSession')
  dev_role_session = boto3.Session(dev_role_credentials['AccessKeyId'], dev_role_credentials['SecretAccessKey'], dev_role_credentials['SessionToken'])
  s3_client_dev_delete = dev_role_session.client('s3', region_name='us-west-2')

  if s3_client_dev_delete:

    # delete all the objects inside lecture1
    objs_to_delete = s3_client_dev_delete.list_objects_v2(Bucket=bucket_name).get('Contents', [])
    for obj in objs_to_delete:
        s3_client_dev_delete.delete_object(Bucket=bucket_name, Key=obj['Key'])
        print(f"{obj['Key']} is deleted!")

    # delete lecture1
    s3_client_dev_delete.delete_bucket(Bucket=bucket_name)
    print("bucket lecture1 is deleted!")

if __name__ == "__main__":
  main()