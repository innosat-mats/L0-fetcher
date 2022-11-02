import logging
import subprocess
import tempfile
from typing import Any, List, Dict

import boto3


BotoClient = Any
Event = Dict[str, Any]


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
    ]

    if not full_sync:
        cmd += ["--update", "--use-server-modtime", "--max-age", "7d"]

    return cmd


def lambda_handler(event: Event, _):
    ssm_client: BotoClient = boto3.client("ssm")

    config_path = get_rclone_config_path(
        ssm_client,
        event.get("RCLONE_CONFIG_SSM_NAME", "config")
    )
    bucket = event.get("OUTPUT_BUCKET", "bucket")
    full_sync = event.get("FULL_SYNC", "FALSE").upper() != "FALSE"
    source_path = event.get("SOURCE_PATH", "/")

    cmd = format_command(config_path, source_path, bucket, full_sync)

    out = subprocess.run(cmd, capture_output=True)
    if out.returncode == 0:
        logging.info("Files successfully synced")
    else:
        logging.error(out.stderr)
