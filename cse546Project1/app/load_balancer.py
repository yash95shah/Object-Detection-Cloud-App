import math
import os
import time

import boto3
import requests

SLEEP_TIME = 5
JOBS_PER_WORKER = 2  # how many jobs can an instance process in the time it takes to spin one up?
JOB_TIMEOUT = 120  # how long to wait for a job before resubmitting it
JOB_TIMERS = dict()

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
        print(requests.get("https://api.behrens.dev/process"))
    except requests.exceptions.ConnectionError as e:
        print("Failed to send signal, probably the server is offline.")


def balance_load():
    def _scale_up(worker_dict, waiting_reqs):
        # start 1 instance for every X waiting jobs (assume workers are already instantiated, as per prof)
        needed_workers = math.ceil(waiting_reqs / float(JOBS_PER_WORKER))

        # don't count active or starting workers
        active_workers = len(worker_dict["running"]) + len(worker_dict["pending"])
        needed_workers = max(0, needed_workers - active_workers)

        print("We have {0} active worker(s); we need {1} more.".format(active_workers, needed_workers))

        if needed_workers > 0:
            print("We need to scale up! Let's see if we have any idle workers we can use...")

            # we still need some! take them from the stopped workers
            for each_worker in worker_dict["stopped"]:
                if needed_workers <= 0:
                    break  # don't start more than we need
                print("Starting worker: {0}".format(each_worker))
                each_worker.start()
                needed_workers -= 1

    def _scale_down(worker_dict):
        global JOB_TIMERS

        # we won't scale down unless the input queue is empty (but workers might still be busy!)

        # make sure we don't stop a server that is still working
        try:
            response = requests.get("https://api.behrens.dev/status/incomplete").json()
            if len(response) > 0:
                print("{0} job(s) in progress; increment their timeout intervals...".format(str(len(response))))
                for job_dict in response:
                    # keep track of jobs which are dragging on and on;
                    #   these jobs were picked up by a worker, but haven't completed
                    job_id = job_dict["_id"]
                    if job_id in JOB_TIMERS:
                        JOB_TIMERS[job_id] += SLEEP_TIME

                        if JOB_TIMERS[job_id] >= JOB_TIMEOUT:
                            # job timed out! we need to resubmit it
                            print("Job {0} timed out, resubmitting...".format(job_id))
                            input_queue = sqs_resource.get_queue_by_name(QueueName="input")
                            input_queue.send_message(MessageBody=str(job_id))
                            JOB_TIMERS.pop(job_id)  # reset the timer for this job
                    else:
                        JOB_TIMERS[job_id] = SLEEP_TIME

                print("Still work to be done! Don't kill them yet, they may be in the middle of something.")
                return  # there are still pending jobs, don't stop any

            print("Looks like the cluster is idle! Ensure all workers are sleeping...")
            for idle_worker in worker_dict["running"]:
                print("Stopping worker: {0}".format(idle_worker))
                idle_worker.stop()  # stop this instance

        except requests.exceptions.ConnectionError as e:
            print("Failed to get status, probably the status server is offline.")

    QUEUE["input"] = sqs_resource.get_queue_by_name(QueueName="input")
    QUEUE["output"] = sqs_resource.get_queue_by_name(QueueName="output")

    waiting_responses = int(QUEUE["output"].attributes["ApproximateNumberOfMessages"])

    if waiting_responses > 0:
        process_results()  # there are results to process! do so

    curr_instances = ec2_resource.instances.all()
    worker_info = {"pending": [], "running": [], "shutting-down": [], "terminated": [], "stopping": [], "stopped": []}
    for each_instance in curr_instances:
        if "worker" in str(each_instance.tags).lower():
            curr_state = each_instance.state["Name"]
            worker_info[curr_state].append(each_instance)

    # determine if we should be scaling up or scaling down
    waiting_requests = int(QUEUE["input"].attributes["ApproximateNumberOfMessages"])
    if waiting_requests == 0 and waiting_responses == 0:
        _scale_down(worker_info)
    else:
        _scale_up(worker_info, waiting_requests)


if __name__ == "__main__":
    # this checks the state of the queues, rebalances the load,
    # and tells the controller to consume results when ready (we assume controller is on the same instance)
    print("Starting load balancer!")
    print("AWS Root: {0}".format(aws_root_path))
    print("Loop Timer: {0}".format(SLEEP_TIME))

    while True:
        try:
            balance_load()
            time.sleep(SLEEP_TIME)
        except Exception as e:
            print("\n***** ERROR *****\n{0}\n*****************\n".format(e))
