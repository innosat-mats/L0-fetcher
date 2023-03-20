from enum import Enum, unique

import boto3

from fetcher.handlers.l0_fetcher import (
    notify_queue,
    BotoClient,
)
from fetcher.l0_fetcher_stack import (
    PLATFORM_BUCKET,
    PLATFORM_STACK,
    RAC_BUCKET,
    RAC_STACK,
    SCHEDULE_BUCKET,
    SCHEDULE_STACK,
    TEMPLATE_OUTPUT_QUEUE,
)


@unique
class FetcherService(Enum):
    RAC_PAYLOAD = (
        RAC_BUCKET,  # bucket
        TEMPLATE_OUTPUT_QUEUE.format(stack_name=RAC_STACK)  # cfn-key
    )
    H5_PLATFORM = (
        PLATFORM_BUCKET,  # bucket
        TEMPLATE_OUTPUT_QUEUE.format(stack_name=PLATFORM_STACK)  # cfn-key
    )
    SCHEDULE = (
        SCHEDULE_BUCKET,  # bucket
        TEMPLATE_OUTPUT_QUEUE.format(stack_name=SCHEDULE_STACK)  # cfn-key
    )

    @property
    def bucket(self) -> str:
        return self.value[0]

    @property
    def queue_key(self) -> str:
        return self.value[1]


def get_queue_arn(
    cfn_client: BotoClient,
    cfn_key: str,
) -> str:
    exports = cfn_client.list_exports()["Exports"]
    for e in exports:
        if e["Name"] == cfn_key:
            return e["Value"]
    raise KeyError(f"key {cfn_key} not found in Cloud formation Exports")


def get_queue_url(
    sqs_client: BotoClient,
    queue_arn: str,
):
    queue_name = queue_arn.split(':')[-1]
    account_id = queue_arn.split(':')[-2]
    return sqs_client.get_queue_url(
        QueueName=queue_name,
        QueueOwnerAWSAccountId=account_id,
    )["QueueUrl"]


def get_objects(
    s3_client: BotoClient,
    bucket: str
) -> list[str]:
    return sorted([
        f["Key"] for f in s3_client.list_objects(Bucket=bucket)['Contents']
    ])


def rerun(
    service: FetcherService,
    profile: str = "mats",
    region: str = "eu-north-1",
):
    session = boto3.session.Session(profile_name=profile)

    s3_client = session.client('s3')
    files = get_objects(s3_client, service.bucket)

    cfn_client = session.client('cloudformation', region_name=region)
    queue_arn = get_queue_arn(cfn_client, service.queue_key)

    sqs_client = session.client("sqs", region_name=region)
    queue_url = get_queue_url(sqs_client, queue_arn)

    notify_queue(sqs_client, queue_url, files, service.bucket)
