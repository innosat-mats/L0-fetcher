
from aws_cdk import CfnOutput, Duration, Stack
from aws_cdk.aws_events import Rule, Schedule
from aws_cdk.aws_events_targets import LambdaFunction
from aws_cdk.aws_iam import Effect, PolicyStatement
from aws_cdk.aws_lambda import (
    Architecture,
    Code,
    Function,
    InlineCode,
    LayerVersion,
    Runtime,
)
from aws_cdk.aws_s3 import Bucket
from aws_cdk.aws_sqs import Queue
from constructs import Construct


class L0FetcherStack(Stack):

    def __init__(
        self,
        scope: Construct,
        id: str,
        output_bucket_name: str,
        config_ssm_name: str,
        source_path: str,
        full_sync: bool = False,
        lambda_timeout: Duration = Duration.seconds(300),
        lambda_schedule: Schedule = Schedule.rate(Duration.hours(12)),
        queue_retention: Duration = Duration.days(14),
        **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)

        output_bucket = Bucket.from_bucket_name(
            self,
            "L0FetcherOutputBucket",
            output_bucket_name,
        )

        notification_queue = Queue(
            self,
            "L0FetcherNotificationQueue",
            retention_period=queue_retention,
        )

        rclone_layer = LayerVersion(
            self,
            "RcloneLayer",
            code=Code.from_asset("dist/layer-arm64.zip"),
            compatible_architectures=[Architecture.ARM_64],
            license="MIT",
            description="Rclone"
        )

        sync_lambda = Function(
            self,
            "L0FetcherLambda",
            code=InlineCode.from_asset("./fetcher/handlers"),
            handler="l0_fetcher.lambda_handler",
            timeout=lambda_timeout,
            architecture=Architecture.ARM_64,
            runtime=Runtime.PYTHON_3_9,
            environment={
                "RCLONE_CONFIG_SSM_NAME": config_ssm_name,
                "SOURCE_PATH": source_path,
                "OUTPUT_BUCKET": output_bucket_name,
                "FULL_SYNC": str(full_sync),
                "NOTIFICATION_QUEUE": notification_queue.queue_name,
            },
            layers=[rclone_layer]
        )

        rule = Rule(
            self,
            "L0FetcherLambdaSchedule",
            schedule=lambda_schedule,
        )

        rule.add_target(LambdaFunction(sync_lambda))

        output_bucket.grant_put(sync_lambda)
        notification_queue.grant_send_messages(sync_lambda)
        sync_lambda.add_to_role_policy(PolicyStatement(
            effect=Effect.ALLOW,
            actions=["ssm:GetParameter"],
            resources=[f"arn:aws:ssm:*:*:parameter{config_ssm_name}"]
        ))

        CfnOutput(
            self,
            "QueueOutput",
            value=notification_queue.queue_arn,
            export_name=f"{id}OutputQueue",
        )
