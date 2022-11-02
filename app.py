#!/usr/bin/env python3

from aws_cdk import App

from fetcher.l0_fetcher_stack import L0FetcherStack

app = App()

L0FetcherStack(
    app,
    "L0RACFetcherStack",
    output_bucket_name="mats-l0-raw-rac",
    config_ssm_name="/rclone/l0-fetcher",
    source_path="/pub/OPS/TM/Level0/",
    full_sync=False,
)

L0FetcherStack(
    app,
    "L0PlatformFetcherStack",
    output_bucket_name="mats-l0-raw-platform",
    config_ssm_name="/rclone/l0-fetcher",
    source_path="/pub/OPS/TM/Level1A/Platform/",
    full_sync=False,
)

app.synth()
