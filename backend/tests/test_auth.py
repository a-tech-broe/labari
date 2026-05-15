import json

import pytest
from moto import mock_aws

from handlers.auth import login, register


def reg_event(email="test@example.com", password="password123", name="Test User"):
    return {
        "routeKey": "POST /auth/register",
        "body": json.dumps({"email": email, "password": password, "name": name}),
        "headers": {},
    }


def login_event(email="test@example.com", password="password123"):
    return {
        "routeKey": "POST /auth/login",
        "body": json.dumps({"email": email, "password": password}),
        "headers": {},
    }


@mock_aws
def test_register_success(dynamodb_table, ssm_jwt_secret):
    response = register(reg_event(), {})
    assert response["statusCode"] == 201
    body = json.loads(response["body"])
    assert "token" in body
    assert body["user"]["email"] == "test@example.com"
    assert "password_hash" not in body["user"]


@mock_aws
def test_register_duplicate_email(dynamodb_table, ssm_jwt_secret):
    register(reg_event(), {})
    response = register(reg_event(), {})
    assert response["statusCode"] == 409


@mock_aws
def test_register_short_password(dynamodb_table, ssm_jwt_secret):
    response = register(reg_event(password="short"), {})
    assert response["statusCode"] == 400


@mock_aws
def test_login_success(dynamodb_table, ssm_jwt_secret):
    register(reg_event(), {})
    response = login(login_event(), {})
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert "token" in body


@mock_aws
def test_login_wrong_password(dynamodb_table, ssm_jwt_secret):
    register(reg_event(), {})
    response = login(login_event(password="wrongpassword"), {})
    assert response["statusCode"] == 401


@mock_aws
def test_login_unknown_email(dynamodb_table, ssm_jwt_secret):
    response = login(login_event(email="nobody@example.com"), {})
    assert response["statusCode"] == 401
