import os
import sys

# Reuse the same helpers pytest uses (env seeding, src/ on path, moto table factories).
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tests"))

from _helpers import seed_env  # noqa: E402


def before_all(context):
    seed_env()


def before_scenario(context, scenario):
    from moto import mock_aws
    context.mock_aws = mock_aws()
    context.mock_aws.start()


def after_scenario(context, scenario):
    context.mock_aws.stop()
