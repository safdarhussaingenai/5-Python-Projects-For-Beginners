def create_subscription(request):
    """
    Demo subscription creation with partner validation.
    """

    if "partner_id" not in request:
        return {
            "status_code": 400,
            "message": "partner_id is required"
        }

    return {
        "status_code": 201,
        "message": "Subscription created successfully"
    }
