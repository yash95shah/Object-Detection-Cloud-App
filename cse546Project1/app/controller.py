import datetime
import os
import uuid

import boto3
import pymongo
from flask_restful import Api, Resource
from app import app

# pip install --upgrade pip wheel gunicorn python-dotenv flask flask_restful requests boto3 pymongo

# load AWS credentials and configuration
aws_root_path = os.path.dirname(os.path.realpath(__file__))
os.environ.setdefault("AWS_SHARED_CREDENTIALS_FILE", os.path.join(aws_root_path, "credentials"))
os.environ.setdefault("AWS_CONFIG_FILE", os.path.join(aws_root_path, "config"))

# init the flask API addon
api = Api(app)

# reserve Mongo connector (unsafe writes!)
MONGO_CLIENT = pymongo.MongoClient(host="localhost", port=27017, w=0)

# reserve AWS connectors
sqs_resource = boto3.resource("sqs")
QUEUE = dict()
QUEUE["input"] = sqs_resource.get_queue_by_name(QueueName="input")
QUEUE["output"] = sqs_resource.get_queue_by_name(QueueName="output")
s3_resource = boto3.resource("s3")
S3_BUCKET = s3_resource.Bucket("cse546-video")
ec2_resource = boto3.resource("ec2")


@app.route("/")
def blank_page():
    return "Please access the APIs directly."


# noinspection PyMethodMayBeStatic
class New(Resource):
    def get(self):
        # no video ID specified, queue a new video
        video_handle = MONGO_CLIENT.cse546.videos
        req = dict()
        req["timestamp"] = str(datetime.datetime.now())
        req["is_done"] = False
        req["_id"] = uuid.uuid4().hex
        print("Recording request status...")
        request_id = video_handle.insert_one(req).inserted_id
        print("Adding request {0} to queue...".format(request_id))
        QUEUE["input"].send_message(MessageBody=str(request_id))
        response = dict()
        response["status"] = "success"
        response["request_id"] = request_id
        print("Responding...")
        return response, 201


# noinspection PyMethodMayBeStatic
class Status(Resource):
    def get(self, filename):
        if filename == "all":
            # return the status of all videos so far
            res = MONGO_CLIENT.cse546.videos.find()
            return list(res), 200

        elif filename == "complete":
            # return the status of all completed videos
            res = MONGO_CLIENT.cse546.videos.find({"is_done": True})
            return list(res), 200

        elif filename == "incomplete":
            # return the status of incomplete videos
            res = MONGO_CLIENT.cse546.videos.find({"is_done": False})
            return list(res), 200

        elif filename == "overview":
            # return a high-level view of the state
            res = dict()

            # sqs info
            QUEUE["input"] = sqs_resource.get_queue_by_name(QueueName="input")
            QUEUE["output"] = sqs_resource.get_queue_by_name(QueueName="output")

            res["input_sqs_count"] = int(QUEUE["input"].attributes["ApproximateNumberOfMessages"])
            res["output_sqs_count"] = int(QUEUE["output"].attributes["ApproximateNumberOfMessages"])

            # s3 info
            res["s3_bucket_count"] = sum(1 for _ in S3_BUCKET.objects.all())

            # worker info
            res["worker_instance_count"] = 0
            for each_instance in ec2_resource.instances.all():
                if "worker" in str(each_instance.tags).lower():
                    if "running" in str(each_instance.state).lower():
                        res["worker_instance_count"] += 1
                    elif "pending" in str(each_instance.state).lower():
                        res["worker_instance_count"] += 1
            res["worker_process_count"] = res["worker_instance_count"] * 2  # 2 processes per worker

            # mongo info
            res["request_complete_count"] = len(list(MONGO_CLIENT.cse546.videos.find({"is_done": True})))
            res["request_incomplete_count"] = len(list(MONGO_CLIENT.cse546.videos.find({"is_done": False})))
            res["request_total_count"] = res["request_complete_count"] + res["request_incomplete_count"]

            return res, 200

        elif filename == "reset-all":
            # debugging to reset system

            # purge backing DB
            MONGO_CLIENT.cse546.videos.delete_many({})

            # empty all queues
            QUEUE["input"].purge()
            QUEUE["output"].purge()

            # empty all buckets
            bucket = boto3.resource('s3').Bucket('cse546-video')
            bucket.objects.all().delete()

            return "reset complete", 200

        elif filename != "":
            # specific video, return info for that video
            res = MONGO_CLIENT.cse546.videos.find_one({"_id": filename})
            return res, 200

        else:
            return "invalid request", 400


# noinspection PyMethodMayBeStatic
class Process(Resource):
    def get(self):
        # there are results in the results queue that need to be processed
        processed = []
        while True:
            # is there a result to process?
            message = QUEUE["output"].receive_messages(MaxNumberOfMessages=1)

            if len(message) == 0:
                print("No results left to process!")
                break
            else:
                print("Processing result...")
                message = message[0]

            # record the updated status of the message
            raw_response = message.body
            request_id, vidfile, classification_result, worker_id = raw_response.split("|")
            updated_status = dict()
            updated_status["_id"] = request_id
            updated_status["is_done"] = True
            updated_status["timestamp"] = str(datetime.datetime.now())
            updated_status["video"] = vidfile
            updated_status["classification"] = classification_result
            updated_status["worker_id"] = worker_id

            # write results
            MONGO_CLIENT.cse546.videos.save(updated_status)
            processed.append(request_id)

            # message processed, delete it so it doesn't get received again
            message.delete()

            print("Result processed!")

        return {"response_count": len(processed)}, 200


api.add_resource(New, "/new")
api.add_resource(Status, "/status/<string:filename>")
api.add_resource(Process, "/process")
