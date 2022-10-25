
import pytest  # type: ignore
from aws_cdk import App, Duration
from aws_cdk.assertions import Template
from aws_cdk.aws_events import Schedule

from fetcher.l0_fetcher_stack import L0FetcherStack


@pytest.mark.parametrize("full_sync,timeout,rate", (
    (True, 100, 5),
    (False, 20, 10),
))
def test_l0_fetcher_stack(full_sync: bool, timeout: int, rate: int):
    app = App()
    stack = L0FetcherStack(
        app,
        "raclambda",
        "output-bucket",
        "config-ssm",
        full_sync,
        Duration.seconds(timeout),
        Schedule.rate(Duration.hours(rate))
    )
    template = Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::Lambda::Function",
        {
            "Environment": {
                "Variables": {
                    "RCLONE_CONFIG_SSM_NAME": "config-ssm",
                    "OUTPUT_BUCKET": "output-bucket",
                    "FULL_SYNC": str(full_sync),
                }
            },
            "Handler": "l0_fetcher.lambda_handler",
            "Runtime": "python3.9",
            "Timeout": timeout,
        }
    )

    template.has_resource_properties(
        "AWS::Events::Rule",
        {
            "ScheduleExpression": f"rate({rate} hours)",
            "State": "ENABLED",
        }
    )

    template.has_resource_properties(
        "AWS::Lambda::Permission",
        {
            "Action": "lambda:InvokeFunction",
            "Principal": "events.amazonaws.com"
        }
    )

    template.has_resource_properties(
        "AWS::IAM::Policy",
        {
            "PolicyDocument": {
                "Statement": [
                    {
                        "Action": [
                            "s3:PutObject",
                            "s3:PutObjectLegalHold",
                            "s3:PutObjectRetention",
                            "s3:PutObjectTagging",
                            "s3:PutObjectVersionTagging",
                            "s3:Abort*",
                        ],
                        "Effect": "Allow",
                    },
                    {
                        "Action": "ssm:GetParameter",
                        "Effect": "Allow",
                    },
                ]
            }
        }
    )
