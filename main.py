import boto3
import time
#######################for checking purpose i have added this line#####
### this is for my dev proejct ###
REGION = "us-east-1"
INSTANCE_ID = "i-xxxxxxxxxxxx"

ec2 = boto3.client("ec2", region_name=REGION)
asg = boto3.client("autoscaling", region_name=REGION)

# --- Check instance state ---
def is_running(instance_id):
    res = ec2.describe_instances(InstanceIds=[instance_id])
    return res['Reservations'][0]['Instances'][0]['State']['Name'] == "running"

# --- Check ASG ---
def get_asg(instance_id):
    res = asg.describe_auto_scaling_instances(InstanceIds=[instance_id])
    if res['AutoScalingInstances']:
        return res['AutoScalingInstances'][0]['AutoScalingGroupName']
    return None

# --- Check AMI exists ---
def check_ami(instance_id):
    images = ec2.describe_images(
        Owners=['self'],
        Filters=[{'Name': 'name', 'Values': [f'backup-{instance_id}*']}]
    )['Images']
    return len(images) > 0

# --- Check snapshot exists ---
def check_snapshots(instance_id):
    inst = ec2.describe_instances(InstanceIds=[instance_id])
    mappings = inst['Reservations'][0]['Instances'][0]['BlockDeviceMappings']

    for m in mappings:
        vol_id = m['Ebs']['VolumeId']
        snaps = ec2.describe_snapshots(
            OwnerIds=['self'],
            Filters=[{'Name': 'volume-id', 'Values': [vol_id]}]
        )['Snapshots']
        if snaps:
            return True
    return False

# --- Create AMI ---
def create_ami(instance_id):
    print("Creating AMI...")
    ec2.create_image(
        InstanceId=instance_id,
        Name=f"backup-{instance_id}-{int(time.time())}",
        NoReboot=True
    )

# --- Create snapshots ---
def create_snapshots(instance_id):
    print("Creating snapshots...")
    inst = ec2.describe_instances(InstanceIds=[instance_id])
    mappings = inst['Reservations'][0]['Instances'][0]['BlockDeviceMappings']

    for m in mappings:
        vol_id = m['Ebs']['VolumeId']
        ec2.create_snapshot(
            VolumeId=vol_id,
            Description=f"Snapshot of {vol_id}"
        )

# --- ASG control ---
def suspend_asg(asg_name):
    print(f"Suspending ASG {asg_name}")
    asg.suspend_processes(
        AutoScalingGroupName=asg_name,
        ScalingProcesses=["Launch", "Terminate"]
    )

def resume_asg(asg_name):
    print(f"Resuming ASG {asg_name}")
    asg.resume_processes(AutoScalingGroupName=asg_name)

# --- Instance control ---
def stop_instance(instance_id):
    print("Stopping instance...")
    ec2.stop_instances(InstanceIds=[instance_id])
    ec2.get_waiter('instance_stopped').wait(InstanceIds=[instance_id])

def start_instance(instance_id):
    print("Starting instance...")
    ec2.start_instances(InstanceIds=[instance_id])
    ec2.get_waiter('instance_running').wait(InstanceIds=[instance_id])

# --- MAIN ---
def main():
    if not is_running(INSTANCE_ID):
        print("Instance is stopped. Exiting...")
        return

    asg_name = get_asg(INSTANCE_ID)

    if asg_name:
        print(f"Instance is in ASG: {asg_name}")

        suspend_asg(asg_name)

        create_ami(INSTANCE_ID)
        create_snapshots(INSTANCE_ID)

        stop_instance(INSTANCE_ID)

        resume_asg(asg_name)

        start_instance(INSTANCE_ID)

    else:
        print("Instance is NOT in ASG")

        ami_exists = check_ami(INSTANCE_ID)
        snap_exists = check_snapshots(INSTANCE_ID)

        if ami_exists and snap_exists:
            print("Backups exist → taking backup again")
            create_ami(INSTANCE_ID)
            create_snapshots(INSTANCE_ID)
        else:
            print("No previous backup found → skipping backup")

        stop_instance(INSTANCE_ID)
        start_instance(INSTANCE_ID)

if __name__ == "__main__":
    main()