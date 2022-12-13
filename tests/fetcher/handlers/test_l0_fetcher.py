import json
import os
from pathlib import Path
from unittest.mock import patch

import botocore
import pytest  # type: ignore
from botocore.stub import Stubber
from fetcher.handlers.l0_fetcher import (
    format_command,
    get_or_raise,
    get_rclone_config_path,
    notify_queue,
    parse_log,
)


@patch.dict(os.environ, {"DEFINITELY": "set"})
def test_get_or_raise():
    assert get_or_raise("DEFINITELY") == "set"


def test_get_or_raise_raises():
    with pytest.raises(
        EnvironmentError,
        match="DEFINITELYNOT is a required environment variable"
    ):
        get_or_raise("DEFINITELYNOT")


def test_rclone_config_path():
    ssm_parameter = "param"

    ssm_client = botocore.session.get_session().create_client(
        "ssm",
        region_name="eu-north-1"
    )
    stubber = Stubber(ssm_client)
    stubber.add_response(
        "get_parameter",
        {"Parameter": {"Value": "config"}},
        expected_params={"Name": ssm_parameter, "WithDecryption": True}
    )
    stubber.activate()

    name = get_rclone_config_path(ssm_client, ssm_parameter)

    path = Path(name)
    assert path.exists()
    assert path.read_text() == "config"
    path.unlink()


def test_format_command_full_sync():
    assert format_command("config", "path", "bucket", True) == [
        "rclone", "--config", "config", "sync", "FTP:path", "S3:bucket", "-v",
        "--use-json-log", "--stats-one-line",
    ]


def test_format_command_partial_sync():
    assert format_command("config", "path", "bucket", False) == [
        "rclone", "--config", "config", "sync", "FTP:path", "S3:bucket", "-v",
        "--use-json-log", "--stats-one-line", "--update",
        "--use-server-modtime", "--max-age", "7d",
    ]


def test_parse_log():
    log = '{"level":"info","msg":"Copied (new)","object":"added","objectType":"*local.Object","source":"operations/operations.go:537","time":"2022-11-03T11:30:06.105602+01:00"}\n{"level":"info","msg":"Updated modification time in destination","object":"modified","objectType":"*local.Object","source":"operations/operations.go:262","time":"2022-11-03T11:30:06.105604+01:00"}\n{"level":"info","msg":"Deleted","object":"deleted","objectType":"*local.Object","source":"operations/operations.go:686","time":"2022-11-03T11:30:06.105715+01:00"}\n{"level":"info","msg":"          0 B / 0 B, -, 0 B/s, ETA -\\n","source":"accounting/stats.go:480","stats":{"bytes":0,"checks":2,"deletedDirs":0,"deletes":1,"elapsedTime":0.029543744,"errors":0,"eta":null,"fatalError":false,"renames":0,"retryError":false,"speed":0,"totalBytes":0,"totalChecks":2,"totalTransfers":1,"transferTime":0,"transfers":1},"time":"2022-11-03T11:30:06.105767+01:00"}\n'  # noqa: E501
    assert parse_log(log) == ["added", "modified"]


def test_notify_queue():
    queue_url = "queueurl"
    list_of_files = ["file2", "file1"]
    bucket = "bucket"

    sqs_client = botocore.session.get_session().create_client(
        "sqs",
        region_name="eu-north-1"
    )
    stubber = Stubber(sqs_client)
    stubber.add_response(
        "send_message",
        {"ResponseMetadata": {"HTTPStatusCode": 200}},
        expected_params={"QueueUrl": queue_url, "MessageBody": json.dumps({
            "object": "bucket/file1",
        })}
    )
    stubber.add_response(
        "send_message",
        {"ResponseMetadata": {"HTTPStatusCode": 200}},
        expected_params={"QueueUrl": queue_url, "MessageBody": json.dumps({
            "object": "bucket/file2",
        })}
    )
    stubber.activate()

    res = notify_queue(sqs_client, queue_url, list_of_files, bucket)
    assert res == []


def test_notify_queue_returns_failed():
    queue_url = "queueurl"
    list_of_files = ["file2", "file1"]
    bucket = "bucket"

    sqs_client = botocore.session.get_session().create_client(
        "sqs",
        region_name="eu-north-1"
    )
    stubber = Stubber(sqs_client)
    response = {
        "MD5OfMessageBody": "Other useful information",
        "ResponseMetadata": {"HTTPStatusCode": 404}
    }
    stubber.add_response(
        "send_message",
        response,
        expected_params={"QueueUrl": queue_url, "MessageBody": json.dumps({
            "object": "bucket/file1",
        })}
    )
    stubber.add_response(
        "send_message",
        {"ResponseMetadata": {"HTTPStatusCode": 200}},
        expected_params={"QueueUrl": queue_url, "MessageBody": json.dumps({
            "object": "bucket/file2",
        })}
    )
    stubber.activate()

    res = notify_queue(sqs_client, queue_url, list_of_files, bucket)
    assert res == ["file1"]
