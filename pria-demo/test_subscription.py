from subscription_service import create_subscription


def test_create_subscription_returns_201():
    result = create_subscription({})

    assert result["status_code"] == 201
