# Designed and created by Carlos Mendez - www.linkedin.com/in/carlos-mendez1 - CR - 2026
"""
Smoke tests against LocalStack (localhost:4566).
Verifies that S3 put/get and SQS send/receive work end-to-end.
"""
import uuid
import boto3
import pytest

LOCALSTACK_URL = "http://localhost:4566"
REGION = "us-east-1"


@pytest.fixture(scope="module")
def s3():
    return boto3.client(
        "s3",
        endpoint_url=LOCALSTACK_URL,
        region_name=REGION,
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )


@pytest.fixture(scope="module")
def sqs():
    return boto3.client(
        "sqs",
        endpoint_url=LOCALSTACK_URL,
        region_name=REGION,
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )


def test_s3_put_and_get(s3):
    bucket = f"weather-test-{uuid.uuid4().hex[:8]}"
    key = "readings/sample.json"
    body = b'{"station_id": "s3-smoke", "temperature_c": 20.0}'

    s3.create_bucket(Bucket=bucket)
    s3.put_object(Bucket=bucket, Key=key, Body=body)

    response = s3.get_object(Bucket=bucket, Key=key)
    assert response["Body"].read() == body


def test_sqs_send_and_receive(sqs):
    queue_name = f"weather-events-{uuid.uuid4().hex[:8]}"
    queue_url = sqs.create_queue(QueueName=queue_name)["QueueUrl"]

    message_body = '{"station_id": "sqs-smoke", "event": "reading_ingested"}'
    sqs.send_message(QueueUrl=queue_url, MessageBody=message_body)

    messages = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1).get(
        "Messages", []
    )
    assert len(messages) == 1
    assert messages[0]["Body"] == message_body
