#!/usr/bin/env python3

from aws_cdk import App, Duration

from fetcher.l0_fetcher_stack import L0FetcherStack

app = App()

L0FetcherStack(
    app,
    "L0RACFetcherStack",
    output_bucket_name="ops-payload-level0-source",
    config_ssm_name="/rclone/l0-fetcher",
    source_path="/pub/OPS/TM/Level0/VC1/APID100/",
    rclone_arn="arn:aws:lambda:eu-north-1:671150066425:layer:rclone-amd64:1",
    full_sync=False,
)

L0FetcherStack(
    app,
    "L0PlatformFetcherStack",
    output_bucket_name="ops-platform-level1a-source",
    config_ssm_name="/rclone/l0-fetcher",
    source_path="/pub/OPS/TM/Level1A/Platform/",
    rclone_arn="arn:aws:lambda:eu-north-1:671150066425:layer:rclone-amd64:1",
    full_sync=False,
)

app.synth()
