def test_app_starts(client):
    assert client.get("/docs").status_code == 200
