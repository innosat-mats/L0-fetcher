
from aws_cdk import App
from aws_cdk.assertions import Template

from fetcher.l0_fetcher_stack import L0FetcherStack
from syrupy.filters import paths


def test_l0_fetcher_stack(snapshot):
    app = App()
    stack = L0FetcherStack(
        app,
        "raclambda",
        "output-bucket",
        "config-ssm",
    )
    template = Template.from_stack(stack)

    template_json = template.to_json()

    del template_json["Resources"]["L0FetcherLambdaC2B4EF04"]["Properties"]["Code"]["S3Key"]  # noqa: E501

    assert template_json == snapshot(
        exclude=paths(
            'Resources.L0FetcherLambdaC2B4EF04.Properties.Code.S3Key',
        )
    )
