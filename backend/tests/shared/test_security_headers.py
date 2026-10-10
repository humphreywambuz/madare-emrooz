"""What the API serves may never be shown as a page that loads or runs anything."""
from app.shared.api.security import API_POLICY


def test_json_and_errors_get_the_strict_policy(client, signed_in):
    _, headers = signed_in()
    for response in (
        client.get("/api/v1/health"),
        client.get("/api/v1/me", headers=headers),
        client.get("/api/v1/me"),  # 401
        client.get("/api/v1/no-such-thing"),  # 404
    ):
        assert response.headers["Content-Security-Policy"] == API_POLICY
    assert "default-src 'none'" in API_POLICY and "frame-ancestors 'none'" in API_POLICY
