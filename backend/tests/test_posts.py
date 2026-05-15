import json

import pytest
from moto import mock_aws

from handlers.posts import create_post, delete_post, get_post, list_posts, search_posts


def make_event(route_key, body=None, path_params=None, token=None, user=None, query_params=None):
    event = {
        "routeKey": route_key,
        "pathParameters": path_params or {},
        "queryStringParameters": query_params or {},
        "headers": {},
        "body": json.dumps(body) if body else None,
    }
    if token:
        event["headers"]["authorization"] = f"Bearer {token}"
    if user:
        event["user"] = user
    return event


TEST_USER = {"sub": "01JTEST000000000000000000", "email": "test@example.com", "role": "admin"}


@mock_aws
def test_list_posts_empty(dynamodb_table):
    event = make_event("GET /posts")
    response = list_posts(event, {})
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["posts"] == []


@mock_aws
def test_create_post_success(dynamodb_table):
    event = make_event(
        "POST /posts",
        body={"title": "Hello Labari", "content": "First post content", "published": True},
        user=TEST_USER,
    )
    response = create_post(event, {})
    assert response["statusCode"] == 201
    body = json.loads(response["body"])
    assert body["post"]["title"] == "Hello Labari"
    assert body["post"]["slug"] == "hello-labari"
    assert body["post"]["published"] is True


@mock_aws
def test_create_post_missing_fields(dynamodb_table):
    event = make_event("POST /posts", body={"title": "No content"}, user=TEST_USER)
    response = create_post(event, {})
    assert response["statusCode"] == 400


@mock_aws
def test_get_post_not_found(dynamodb_table):
    event = make_event("GET /posts/{id}", path_params={"id": "NONEXISTENT"})
    response = get_post(event, {})
    assert response["statusCode"] == 404


@mock_aws
def test_get_post_success(dynamodb_table):
    create_event = make_event(
        "POST /posts",
        body={"title": "Test Post", "content": "Content here"},
        user=TEST_USER,
    )
    created = json.loads(create_post(create_event, {})["body"])
    post_id = created["post"]["id"]

    get_event = make_event("GET /posts/{id}", path_params={"id": post_id})
    response = get_post(get_event, {})
    assert response["statusCode"] == 200
    assert json.loads(response["body"])["post"]["id"] == post_id


@mock_aws
def test_list_posts_shows_published_only(dynamodb_table):
    create_post(make_event("POST /posts", body={"title": "Published", "content": "x", "published": True}, user=TEST_USER), {})
    create_post(make_event("POST /posts", body={"title": "Draft", "content": "x", "published": False}, user=TEST_USER), {})

    response = list_posts(make_event("GET /posts"), {})
    body = json.loads(response["body"])
    assert len(body["posts"]) == 1
    assert body["posts"][0]["title"] == "Published"


@mock_aws
def test_list_posts_filter_by_category(dynamodb_table):
    create_post(make_event("POST /posts", body={"title": "AWS Post", "content": "x", "published": True, "categories": ["aws", "cloud"]}, user=TEST_USER), {})
    create_post(make_event("POST /posts", body={"title": "Python Post", "content": "x", "published": True, "categories": ["python"]}, user=TEST_USER), {})

    response = list_posts(make_event("GET /posts", query_params={"category": "aws"}), {})
    body = json.loads(response["body"])
    assert len(body["posts"]) == 1
    assert body["posts"][0]["title"] == "AWS Post"


@mock_aws
def test_search_posts(dynamodb_table):
    create_post(make_event("POST /posts", body={"title": "Terraform tutorial", "content": "Learn IaC", "published": True}, user=TEST_USER), {})
    create_post(make_event("POST /posts", body={"title": "Docker guide", "content": "Containers", "published": True}, user=TEST_USER), {})

    response = search_posts({"routeKey": "GET /search", "queryStringParameters": {"q": "terraform"}, "headers": {}}, {})
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert len(body["posts"]) == 1
    assert "terraform" in body["posts"][0]["title"].lower()


@mock_aws
def test_search_posts_short_query(dynamodb_table):
    response = search_posts({"routeKey": "GET /search", "queryStringParameters": {"q": "a"}, "headers": {}}, {})
    assert response["statusCode"] == 400


@mock_aws
def test_create_post_with_categories(dynamodb_table):
    event = make_event(
        "POST /posts",
        body={"title": "Cats Post", "content": "x", "categories": ["AWS", "devops "], "published": True},
        user=TEST_USER,
    )
    response = create_post(event, {})
    body = json.loads(response["body"])
    # Categories are lowercased and trimmed
    assert set(body["post"]["categories"]) == {"aws", "devops"}


@mock_aws
def test_delete_post(dynamodb_table):
    created = json.loads(
        create_post(make_event("POST /posts", body={"title": "To Delete", "content": "x"}, user=TEST_USER), {})["body"]
    )
    post_id = created["post"]["id"]

    response = delete_post(make_event("DELETE /posts/{id}", path_params={"id": post_id}, user=TEST_USER), {})
    assert response["statusCode"] == 200

    response = get_post(make_event("GET /posts/{id}", path_params={"id": post_id}), {})
    assert response["statusCode"] == 404
