import boto3
from botocore.exceptions import ClientError

iam = boto3.client('iam')

role_name = "MyPythonRole"  # Role you created

# --- Step 1: List and delete all inline policies ---
try:
    policies = iam.list_role_policies(RoleName=role_name)['PolicyNames']
    for policy_name in policies:
        iam.delete_role_policy(RoleName=role_name, PolicyName=policy_name)
        print(f"Deleted inline policy {policy_name} from role {role_name}")
except ClientError as e:
    print(f"Error deleting inline policies: {e}")

# --- Step 2: Delete the role itself ---
try:
    iam.delete_role(RoleName=role_name)
    print(f"Deleted role {role_name} successfully.")
except ClientError as e:
    print(f"Error deleting role: {e}")