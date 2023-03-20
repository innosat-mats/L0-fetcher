#!/usr/bin/env python3

from aws_cdk import App

from fetcher.l0_fetcher_stack import (
    L0FetcherStack,
    RAC_BUCKET,
    RAC_STACK,
    PLATFORM_BUCKET,
    PLATFORM_STACK,
    SCHEDULE_BUCKET,
    SCHEDULE_STACK,
)

app = App()

L0FetcherStack(
    app,
    RAC_STACK,
    output_bucket_name=RAC_BUCKET,
    config_ssm_name="/rclone/l0-fetcher",
    source_path="/pub/OPS/TM/Level0/VC1/APID100/",
    rclone_arn="arn:aws:lambda:eu-north-1:671150066425:layer:rclone-amd64:1",
    full_sync=True,
)

L0FetcherStack(
    app,
    PLATFORM_STACK,
    output_bucket_name=PLATFORM_BUCKET,
    config_ssm_name="/rclone/l0-fetcher",
    source_path="/pub/OPS/TM/Level1A/Platform_v1/",
    rclone_arn="arn:aws:lambda:eu-north-1:671150066425:layer:rclone-amd64:1",
    full_sync=True,
)

L0FetcherStack(
    app,
    SCHEDULE_STACK,
    output_bucket_name=SCHEDULE_BUCKET,
    config_ssm_name="/rclone/l0-fetcher",
    source_path="/pub/Timeline/Schedule/",
    rclone_arn="arn:aws:lambda:eu-north-1:671150066425:layer:rclone-amd64:1",
    full_sync=True,
)

app.synth()
