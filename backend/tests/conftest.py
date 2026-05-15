import os

import boto3
import jwt
import pytest
from moto import mock_aws

os.environ.setdefault("DYNAMODB_TABLE", "labari-test")
os.environ.setdefault("IMAGES_BUCKET", "labari-images-test")
os.environ.setdefault("IMAGES_CDN_DOMAIN", "images.labari.test")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("PROJECT_NAME", "labari")

TEST_JWT_SECRET = "test-secret-key-for-unit-tests-only"


@pytest.fixture
def aws_credentials():
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture
def dynamodb_table(aws_credentials):
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        table = dynamodb.create_table(
            TableName="labari-test",
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
                {"AttributeName": "GSI1PK", "AttributeType": "S"},
                {"AttributeName": "GSI1SK", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[{
                "IndexName": "GSI1",
                "KeySchema": [
                    {"AttributeName": "GSI1PK", "KeyType": "HASH"},
                    {"AttributeName": "GSI1SK", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            }],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()

        import shared.db as db_module
        db_module._table = None  # Reset singleton between tests

        yield table

        db_module._table = None


@pytest.fixture
def ssm_jwt_secret(aws_credentials):
    with mock_aws():
        ssm = boto3.client("ssm", region_name="us-east-1")
        ssm.put_parameter(
            Name="/labari/test/jwt-secret",
            Value=TEST_JWT_SECRET,
            Type="SecureString",
        )
        from shared.auth import get_jwt_secret
        get_jwt_secret.cache_clear()
        yield TEST_JWT_SECRET
        get_jwt_secret.cache_clear()


@pytest.fixture
def auth_token(ssm_jwt_secret):
    from datetime import datetime, timedelta, timezone
    payload = {
        "sub": "01JTEST000000000000000000",
        "email": "test@example.com",
        "name": "Test User",
        "role": "admin",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(days=1),
    }
    return jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")
