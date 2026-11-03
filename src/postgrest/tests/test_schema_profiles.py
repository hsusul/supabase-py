import pytest
from httpx import AsyncClient, Client, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession

from postgrest import AsyncPostgrestClient, SyncPostgrestClient


def _transport(requests: list[Request]) -> MockTransport:
    def handler(request: Request) -> Response:
        requests.append(request)
        return Response(200, json=[{"id": 1}])

    return MockTransport(handler)


@pytest.mark.parametrize("initial_schema", ["public", "private"])
@pytest.mark.parametrize("operation", ["select", "insert"])
def test_sync_schema_switch_replaces_profile(
    initial_schema: str, operation: str
) -> None:
    requests: list[Request] = []
    with Client(transport=_transport(requests)) as http:
        original = SyncPostgrestClient(
            "https://example.com",
            http_session=HttpxSession(client=http),
            schema=initial_schema,
            headers={"Authorization": "Bearer token", "X-App-Name": "schema-test"},
        )
        switched = original.schema("analytics")
        chained = switched.schema("public")

        for client in (original, switched, chained, original):
            table = client.table("items")
            query = table.select() if operation == "select" else table.insert({"id": 1})
            assert query.execute().data == [{"id": 1}]

    assert [request.headers.get_list("Authorization") for request in requests] == [
        ["Bearer token"]
    ] * 4
    assert [request.headers["X-App-Name"] for request in requests] == [
        "schema-test"
    ] * 4
    profile = "Accept-Profile" if operation == "select" else "Content-Profile"
    assert [request.headers.get_list(profile) for request in requests] == [
        [initial_schema],
        ["analytics"],
        ["public"],
        [initial_schema],
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("initial_schema", ["public", "private"])
@pytest.mark.parametrize("operation", ["select", "insert"])
async def test_async_schema_switch_replaces_profile(
    initial_schema: str, operation: str
) -> None:
    requests: list[Request] = []
    async with AsyncClient(transport=_transport(requests)) as http:
        original = AsyncPostgrestClient(
            "https://example.com",
            http_session=AsyncHttpxSession(client=http),
            schema=initial_schema,
            headers={"Authorization": "Bearer token", "X-App-Name": "schema-test"},
        )
        switched = original.schema("analytics")
        chained = switched.schema("public")

        for client in (original, switched, chained, original):
            table = client.table("items")
            query = table.select() if operation == "select" else table.insert({"id": 1})
            assert (await query.execute()).data == [{"id": 1}]

    assert [request.headers.get_list("Authorization") for request in requests] == [
        ["Bearer token"]
    ] * 4
    assert [request.headers["X-App-Name"] for request in requests] == [
        "schema-test"
    ] * 4
    profile = "Accept-Profile" if operation == "select" else "Content-Profile"
    assert [request.headers.get_list(profile) for request in requests] == [
        [initial_schema],
        ["analytics"],
        ["public"],
        [initial_schema],
    ]
