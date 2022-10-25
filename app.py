#!/usr/bin/env python3

from aws_cdk import App

from fetcher.l0_fetcher_stack import L0FetcherStack

app = App()
L0FetcherStack(
    app,
    "L0FetcherStack",
    output_bucket_name="mats-l0-raw",
    config_ssm_name="/rclone/l0-fetcher",
    full_sync=False,
)

app.synth()
