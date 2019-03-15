import boto3
import pymongo
import uuid
import os

import time
from flask import Flask
from flask_restful import Api, Resource, reqparse

# load AWS credentials and configuration
aws_root_path = os.path.dirname(os.path.realpath(__file__))
os.environ.setdefault("AWS_SHARED_CREDENTIALS_FILE", os.path.join(aws_root_path,"credentials"))
os.environ.setdefault("AWS_CONFIG_FILE", os.path.join(aws_root_path,"config"))

# init the flask engine
app = Flask(__name__)
api = Api(app)

# reserve Mongo connector (unsafe writes!)
mongo_client = pymongo.MongoClient(host="localhost", port=27017, w=0)

# reserve AWS connectors
sqs_client = boto3.client("sqs")
input_sqs = sqs_client.get_queue_url(QueueName="input")["QueueUrl"]
output_sqs = sqs_client.get_queue_url(QueueName="output")["QueueUrl"]


class New(Resource):
    def get(self):
        # no video ID specified, queue a new video
        video_handle = mongo_client.cse546.videos
        req = dict()
        req["created_at"] = time.time()
        req["is_done"] = False
        req["completed_at"] = None
        req["_id"] = uuid.uuid4().hex
        print("Recording request status...")
        request_id = video_handle.insert_one(req).inserted_id
        print("Adding request {0} to queue...".format(request_id))
        sqs_client.send_message(QueueUrl=input_sqs, MessageBody=request_id)
        response = dict()
        response["status"] = "success"
        response["request_id"] = request_id
        print("Responding...")
        return response, 201


class Status(Resource):
    def get(self, filename):
        print("debug ({0})".format(filename))
        if filename == "all":
            # return the status of all videos so far
            all_vids = mongo_client.cse546.videos.find()
            return all_vids, 200

        elif filename == "complete":
            # return the status of all completed videos
            all_vids = mongo_client.cse546.videos.find({"is_done": True})
            return all_vids, 200

        elif filename == "incomplete":
            # return the status of incomplete videos
            all_vids = mongo_client.cse546.videos.find({"is_done": False})
            return all_vids, 200

        elif filename != "":
            # specific video, return info for that video
            vid = mongo_client.cse546.videos.find({"_id": filename})
            return vid, 200

        else:
            return "invalid request", 400


api.add_resource(New, "/new")
api.add_resource(Status, "/status/<string:filename>")
app.run(debug=True)
