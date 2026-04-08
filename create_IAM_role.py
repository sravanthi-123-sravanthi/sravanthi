import boto3
import json
from botocore.exceptions import ClientError

iam = boto3.client('iam')

# --- Step 1: Create IAM Role ---
role_name = "MyPythonRole"
trust_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "ec2.amazonaws.com"  # Adjust if needed
            },
            "Action": "sts:AssumeRole"
        }
    ]
}

try:
    response = iam.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(trust_policy),
        Description="Role created via Python with inline policies"
    )
    print(f"Role {role_name} created successfully.")
except ClientError as e:
    print(f"Error creating role: {e}")

# --- Step 2: Attach Inline Policy for S3 Put/Get ---
s3_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:ListBucket"
            ],
            "Resource": "*"
        }
    ]
}

try:
    iam.put_role_policy(
        RoleName=role_name,
        PolicyName="S3PutGetPolicy",
        PolicyDocument=json.dumps(s3_policy)
    )
    print("S3 Put/Get inline policy attached.")
except ClientError as e:
    print(f"Error attaching S3 policy: {e}")

# --- Step 3: Attach Inline Policy for ViewOnly Permissions ---
viewonly_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ec2:Describe*",
                "s3:ListAllMyBuckets",
                "s3:GetBucketLocation",
                "s3:GetObject"
            ],
            "Resource": "*"
        }
    ]
}

try:
    iam.put_role_policy(
        RoleName=role_name,
        PolicyName="ViewOnlyPolicy",
        PolicyDocument=json.dumps(viewonly_policy)
    )
    print("ViewOnly inline policy attached.")
except ClientError as e:
    print(f"Error attaching ViewOnly policy: {e}")