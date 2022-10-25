
from aws_cdk import App
from aws_cdk.assertions import Template

from fetcher.l0_fetcher_stack import L0FetcherStack


def test_l0_fetcher_stack(snapshot):
    app = App()
    stack = L0FetcherStack(
        app,
        "raclambda",
        "output-bucket",
        "config-ssm",
    )
    template = Template.from_stack(stack)

    assert template.to_json() == snapshot
