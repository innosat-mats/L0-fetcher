
import pytest  # type: ignore
from aws_cdk import App, Duration
from aws_cdk.assertions import Match, Template
from aws_cdk.aws_events import Schedule

from fetcher.l0_fetcher_stack import L0FetcherStack


@pytest.fixture
def template():
    app = App()

    stack = L0FetcherStack(
        app,
        "raclambda",
        "output-bucket",
        "config-ssm",
    )

    return Template.from_stack(stack)


class TestL0FetcherStack:

    def test_has_rclone_layer(self, template):
        template.has_resource_properties(
            "AWS::Lambda::LayerVersion",
            {
                "CompatibleArchitectures": [
                    "arm64"
                ]
            }
        )

    def test_has_lambda_policy(self, template):
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

    @pytest.mark.parametrize("full_sync,timeout", (
        (True, 100),
        (False, 20),
    ))
    def test_has_lambda_function(self, full_sync, timeout):
        stack = L0FetcherStack(
            App(),
            "raclambda",
            "output-bucket",
            "config-ssm",
            full_sync,
            Duration.seconds(timeout),
        )

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::Lambda::Function",
            {
                "Architectures": ["arm64"],
                "Environment": {
                    "Variables": {
                        "RCLONE_CONFIG_SSM_NAME": "config-ssm",
                        "OUTPUT_BUCKET": "output-bucket",
                        "FULL_SYNC": str(full_sync),
                    }
                },
                "Handler": "l0_fetcher.lambda_handler",
                "Layers": [{
                    "Ref": Match.string_like_regexp(r"^RcloneLayer.*$")
                }],
                "Runtime": "python3.9",
                "Timeout": timeout,
            }
        )

    @pytest.mark.parametrize("rate", (
        100,
        20,
    ))
    def test_has_lambda_event(self, rate):
        stack = L0FetcherStack(
            App(),
            "raclambda",
            "output-bucket",
            "config-ssm",
            lambda_schedule=Schedule.rate(Duration.hours(rate)),
        )
        template = Template.from_stack(stack)

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
