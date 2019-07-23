[Group Members]
Hans Behrens    #1211230537
Hardik Shah     #1213315179
Yash Shah       #1215487117

[API Endpoints]
https://api.behrens.dev/
    Base HTTPS URL. Note that HTTP access is not available.

https://api.behrens.dev/new
    Generates a new classification request, and returns the request ID.

https://api.behrens.dev/status/overview
    Provides a high-level overview of the state of the system, including S3, EC2, SQS, etc.

https://api.behrens.dev/status/complete
    Returns detailed information about completed requests.

https://api.behrens.dev/status/incomplete
    Returns detailed information about incomplete requests.

https://api.behrens.dev/status/all
    Returns detailed information about all requests.

https://api.behrens.dev/status/[request id]
    Returns detailed information about a specific request, identified by its ID.

https://api.behrens.dev/status/reset-all
    Resets the system to the start state by purging all queues, buckets, etc.

[S3 Bucket Name]
cse546-video

[AWS Credentials]
Access Key ID: AKIAJVI4VIFESSLTGZ3Q
Secret Access Key: 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

