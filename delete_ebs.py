import boto3
from botocore.exceptions import ClientError

REGION = "us-east-1"
SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:494810892147:test-ebs"

ec2 = boto3.client("ec2", region_name=REGION)
sns = boto3.client("sns", region_name=REGION)

def get_deletable_volumes():
    """Return only volumes that are truly available (state='available' and no attachments)."""
    volumes = ec2.describe_volumes()['Volumes']
    deletable = []
    for vol in volumes:
        if vol['State'] == 'available' and not vol.get('Attachments'):
            deletable.append(vol)
        else:
            print(f"Skipping {vol['VolumeId']} - State: {vol['State']}, Attachments: {len(vol.get('Attachments', []))}")
    return deletable

def notify_volume(volume):
    vol_id = volume['VolumeId']
    creator = "Unknown"
    if 'Tags' in volume:
        for tag in volume['Tags']:
            if tag['Key'].lower() in ['owner', 'createdby']:
                creator = tag['Value']
    message = f"EBS Volume {vol_id} is available and will be deleted in 10 days unless you respond."
    sns.publish(TopicArn=SNS_TOPIC_ARN, Message=message, Subject=f"Volume {vol_id} Scheduled for Deletion")
    print(f"Notification sent for {vol_id} to {creator}")

def main():
    deletable_volumes = get_deletable_volumes()
    if not deletable_volumes:
        print("No deletable volumes found.")
        return
    for vol in deletable_volumes:
        notify_volume(vol)
        # Optional deletion: only if still available
        ec2.delete_volume(VolumeId=vol['VolumeId'])
        print(f"Deleted volume {vol['VolumeId']}")

if __name__ == "__main__":
    main()