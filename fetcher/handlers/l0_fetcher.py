import json
import logging
import os
import subprocess
import tempfile
from typing import Any, Dict, List

import boto3

BotoClient = Any
Event = Dict[str, Any]
Context = Any


class SyncError(Exception):
    pass


def get_or_raise(variable_name: str) -> str:
    var = os.environ.get(variable_name)
    if var is None:
        raise EnvironmentError(
            f"{variable_name} is a required environment variable"
        )
    return var


def get_rclone_config_path(
    ssm_client: BotoClient,
    rclone_config_ssm_name: str
) -> str:

    rclone_config = ssm_client.get_parameter(
        Name=rclone_config_ssm_name, WithDecryption=True
    )["Parameter"]["Value"]

    f = tempfile.NamedTemporaryFile(buffering=0, delete=False)
    f.write(rclone_config.encode())

    return f.name


def format_command(
    config_path: str,
    source_path: str,
    bucket: str,
    full_sync: bool,
) -> List[str]:
    cmd = [
        "rclone",
        "--config",
        config_path,
        "sync",
        f"FTP:{source_path}",
        f"S3:{bucket}",
        "-v",
        "--use-json-log",
        "--stats-one-line",
    ]

    if not full_sync:
        cmd += ["--update", "--use-server-modtime", "--max-age", "7d"]

    return cmd


def parse_log(log: str) -> List[str]:
    def keep(row: Dict[str, str]) -> bool:
        return row["msg"] != "Deleted"

    return [
        parsed_row["object"]
        for parsed_row in [json.loads(row) for row in log.splitlines()]
        if "object" in parsed_row and keep(parsed_row)
    ]


def notify_queue(
    sqs_client: BotoClient,
    notification_queue: str,
    modified_files: List[str],
    bucket: str,
) -> None:
    response = sqs_client.send_message(
        QueueUrl=notification_queue,
        MessageBody=json.dumps({
            "objects": modified_files,
            "bucket": bucket,
        })
    )
    if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
        msg = f"Failed to notify queue: {response}"
        logging.error(msg)
        raise SyncError(msg)


def lambda_handler(event: Event, context: Context):
    ssm_client: BotoClient = boto3.client("ssm")
    sqs_client: BotoClient = boto3.client("sqs")

    config_path = get_rclone_config_path(
        ssm_client,
        os.environ.get("RCLONE_CONFIG_SSM_NAME", "config")
    )
    bucket = get_or_raise("OUTPUT_BUCKET")
    source_path = get_or_raise("SOURCE_PATH")
    notification_queue = get_or_raise("NOTIFICATION_QUEUE")
    full_sync = os.environ.get("FULL_SYNC", "FALSE").upper() != "FALSE"

    cmd = format_command(config_path, source_path, bucket, full_sync)

    out = subprocess.run(cmd, capture_output=True)
    if out.returncode != 0:
        logging.error(out.stderr)
        raise SyncError(out.stderr.decode())

    logging.info("Files successfully synced")

    modified_files = parse_log(out.stderr.decode())
    notify_queue(sqs_client, notification_queue, modified_files, bucket)
    logging.info("Notified queue")
