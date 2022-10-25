from pathlib import Path

import botocore
from botocore.stub import Stubber
from fetcher.handlers.l0_fetcher import (
    FTP_PATH,
    format_command,
    get_rclone_config_path,
)


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
    assert format_command("config", "bucket", True) == [
        "rclone", "--config", "config", "sync", f"FTP:{FTP_PATH}", "S3:bucket"
    ]


def test_format_command_partial_sync():
    assert format_command("config", "bucket", False) == [
        "rclone", "--config", "config", "sync", f"FTP:{FTP_PATH}", "S3:bucket",
        "--update", "--use-server-modtime", "--max-age", "7d"
    ]
