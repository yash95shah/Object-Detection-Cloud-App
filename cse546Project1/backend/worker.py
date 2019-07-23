import os
import subprocess
import time
import uuid

import boto3
import requests

PROCESS_ID = uuid.uuid4().hex
SLEEP_TIMER = 1
RESULT_PATH = "{0}_result".format(PROCESS_ID)
LABEL_PATH = "{0}_label".format(PROCESS_ID)

# load AWS credentials and configuration
aws_root_path = os.path.dirname(os.path.realpath(__file__))
os.environ.setdefault("AWS_SHARED_CREDENTIALS_FILE", os.path.join(aws_root_path, "credentials"))
os.environ.setdefault("AWS_CONFIG_FILE", os.path.join(aws_root_path, "config"))

# reserve AWS connectors
sqs_resource = boto3.resource("sqs")
QUEUE = dict()
QUEUE["input"] = sqs_resource.get_queue_by_name(QueueName="input")
QUEUE["output"] = sqs_resource.get_queue_by_name(QueueName="output")

s3_resource = boto3.resource("s3")
output_bucket = s3_resource.Bucket("cse546-video")


def simple_log(string):
    with open("/home/ubuntu/darknet/{0}_log".format(PROCESS_ID), "a") as logfile:
        logfile.writelines(string)
        logfile.write("\n")


def helper_func():
    # this code provided by the TA
    obj = set()

    file_in = open(RESULT_PATH, "r")
    file_out = open(LABEL_PATH, "w")
    for lines in file_in:
        if lines == "\n":
            continue
        if lines.split(":")[-1] == "\n":
            continue
        if lines.split(":")[-1][-2] == "%":
            obj.add(lines.split(":")[0])

    for items in obj:
        file_out.write(items)
        file_out.write(",")

    if obj.__len__() == 0:
        file_out.write("No item is detected")
    file_in.close()
    file_out.close()


def work_on_request():
    jobs = QUEUE["input"].receive_messages(MaxNumberOfMessages=1)  # check the job queue
    if len(jobs) == 0:
        return  # not exactly 1 job, wait and then try again

    try:
        os.remove("/home/ubuntu/darknet/{0}_log".format(PROCESS_ID))
    except Exception as e:
        # do nothing
        print("nothing to see here")

    simple_log("Job started by worker process {0}!".format(PROCESS_ID))

    # there's a job to do
    request_id = jobs[0].body
    jobs[0].delete()  # delete message from the queue
    simple_log("Job ID: {0}".format(request_id))

    # fetch data to classify
    res = requests.get("http://206.207.50.7/getvideo/")
    headers = res.headers["content-disposition"]
    if "attachment" not in headers:
        simple_log("Data could not be fetched; re-queuing job.")
        QUEUE["input"].send_message(MessageBody=request_id)
        return
    else:
        vidfile = headers.split("=")[1]
        vidpath = str(PROCESS_ID) + "_" + vidfile
        with open(vidpath, "wb") as outfile:
            outfile.write(res.content)
        simple_log("Data successfully fetched ({0}).".format(vidfile))

    # run the classifier
    command = "./darknet detector demo " \
              "cfg/coco.data cfg/yolov3-tiny.cfg " \
              "tiny.weights {0}" \
              " -dont_show > {1}".format(vidpath, RESULT_PATH)
    subprocess.run(command, shell=True)
    simple_log("\nClassification complete.")
    os.remove(vidpath)  # don't let video files build up over time!

    # post-process the results
    helper_func()
    with open(LABEL_PATH, "r") as labelfile:
        labels = labelfile.read()
    if labels[-1] == ",":
        labels = labels[:-1]  # trim that ugly trailing comma
    simple_log("Postprocessing complete:\n{0}".format(labels))

    # upload data and results to S3
    output_bucket.put_object(Key=vidfile, Body=labels)
    simple_log("Results stored to S3:\n{0}".format(labels))

    # file a result message
    QUEUE["output"].send_message(MessageBody=(request_id + "|" + vidfile + "|" + labels + "|" + PROCESS_ID))
    simple_log("Output queued in SQS.")

    simple_log("Job done!")


if __name__ == "__main__":
    os.chdir("/home/ubuntu/darknet/")
    while True:
        try:
            work_on_request()  # never stop working! the load balancer will destroy you when you are no longer useful
            time.sleep(SLEEP_TIMER)
        except Exception as e:
            simple_log(e)
