import os

import boto3

_table = None


def get_table():
    global _table
    if _table is None:
        dynamodb = boto3.resource("dynamodb")
        _table = dynamodb.Table(os.environ["DYNAMODB_TABLE"])
    return _table
