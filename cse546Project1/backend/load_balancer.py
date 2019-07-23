import os
import time
import uuid

import boto3
import requests

WORKER_CAP = 19
WORKER_AMI = "ami-060ccb420a60a44d6"
SLEEP_TIME = 5
JOB_SPINUP_TRADEOFF = 2  # how many jobs can an instance process in the time it takes to spin one up?
FLASK_PORT = 5000

# load AWS credentials and configuration
aws_root_path = os.path.dirname(os.path.realpath(__file__))
os.environ.setdefault("AWS_SHARED_CREDENTIALS_FILE", os.path.join(aws_root_path, "credentials"))
os.environ.setdefault("AWS_CONFIG_FILE", os.path.join(aws_root_path, "config"))

# reserve AWS connectors
sqs_resource = boto3.resource("sqs")
QUEUE = dict()
QUEUE["input"] = sqs_resource.get_queue_by_name(QueueName="input")
QUEUE["output"] = sqs_resource.get_queue_by_name(QueueName="output")

ec2_resource = boto3.resource("ec2")


def process_results():
    print("Sending result processing signal...")
    try:
        print(requests.get("http://127.0.0.1:{0}/process".format(FLASK_PORT)))
    except requests.exceptions.ConnectionError as e:
        print("Failed to send signal, probably the server is offline.")


def balance_load():
    def _scale_up(curr_workers, waiting_reqs):
        # spin up 1 instance for every X waiting jobs
        needed_workers = (waiting_reqs - (curr_workers * JOB_SPINUP_TRADEOFF) / JOB_SPINUP_TRADEOFF)
        needed_workers = min(needed_workers, WORKER_CAP - curr_workers) # don't spin up too many
        print("Scaling *UP* by {0} workers...".format(needed_workers))
        # note that needed workers might be a fraction or a negative number, but this is OK

        while needed_workers > 0:
            # always add only 1 worker at a time, for stable scaling
            new_worker_name = "worker-{0}".format(str(uuid.uuid4().hex))
            instance = ec2_resource.create_instances(
                MaxCount=1,
                MinCount=1,
                InstanceType="t2.micro",
                KeyName="cse546",
                SecurityGroups=["Worker"],
                ImageId=WORKER_AMI,
                TagSpecifications=[
                    {"ResourceType": "instance",
                     "Tags": [
                         {"Key": "Name", "Value": new_worker_name}
                     ]}
                ]
            )[0]
            print("New instance created ({0})!".format(instance.id))
            needed_workers -= 1
        ############################################

    def _scale_down(idle_workers):
        # make sure we don't kill a server that is still working
        try:
            response = requests.get("http://127.0.0.1:{0}/status/incomplete".format(FLASK_PORT)).json()
        except requests.exceptions.ConnectionError as e:
            response = ["abort"]
            print("Failed to get status, probably the server is offline.")

        if len(response) > 0:
            print("Still work to be done! Don't kill them yet, they might be in the middle of something.")
            return  # there are still pending jobs, don't kill anyone
        print("Scaling *DOWN* all workers...")

        for worker_instance_to_kill in idle_workers:
            print("Killing worker: {0}".format(worker_instance_to_kill))
            worker_instance_to_kill.terminate()  # kill!
        ############################################

    # print("Balancing load...")

    QUEUE["input"].reload()
    waiting_requests = int(QUEUE["input"].attributes["ApproximateNumberOfMessages"])

    QUEUE["output"].reload()
    waiting_responses = int(QUEUE["output"].attributes["ApproximateNumberOfMessages"])

    if waiting_responses > 0:
        process_results()  # there are results to process! do so

    curr_instances = ec2_resource.instances.all()
    running_workers = []
    pending_workers = []
    for each_instance in curr_instances:
        if "worker" in str(each_instance.tags).lower():
            if "running" in str(each_instance.state).lower():
                running_workers.append(each_instance)
            elif "pending" in str(each_instance.state).lower():
                pending_workers.append(each_instance)

    # case 1: requests >> instances: scale up!
    worker_count = len(running_workers) + len(pending_workers)
    if waiting_requests > 0 and worker_count < WORKER_CAP and len(pending_workers) == 0:
        _scale_up(worker_count, waiting_requests)
    elif (waiting_requests == 0 and waiting_responses == 0 and worker_count > 0) or worker_count > WORKER_CAP:
        _scale_down(running_workers)  # kill workers FIFO
    else:
        print("Looking good!\n\tRequests:{0} Workers:{1}".format(waiting_requests, worker_count))


if __name__ == "__main__":
    # this checks the state of the queues, rebalances the load,
    # and tells the controller to consume results when ready (we assume controller is on the same instance)
    print("Starting load balancer!")
    print("AWS Root: {0}".format(aws_root_path))
    print("Loop Timer: {0}\nCap: {1}\nWorker Image: {2}".format(SLEEP_TIME, WORKER_CAP, WORKER_AMI))

    while True:
        try:
            balance_load()
            time.sleep(SLEEP_TIME)
        except Exception as e:
            print("\n***** ERROR *****\n{0}\n*****************\n".format(e))
