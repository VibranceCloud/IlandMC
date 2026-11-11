import asyncio
import httpx
import pytest

from ilandymc.providers.paper import PaperProvider


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


class FakeClient:
    def __init__(self, responses):
        self.responses = responses
        self.urls = []

    async def get(self, url):
        self.urls.append(url)
        return FakeResponse(self.responses[url])


def test_paper_v3_flattens_grouped_versions_in_service_order():
    provider = PaperProvider(client=FakeClient({
        PaperProvider.API: {"versions": {"26": ["26.3", "26.2"], "1.21": ["1.21.11"]}}
    }))
    assert asyncio.run(provider.versions()) == ["26.3", "26.2", "1.21.11"]


def test_paper_v3_selects_stable_build_and_sha256():
    url = f"{PaperProvider.API}/versions/26.3/builds"
    client = FakeClient({url: [
        {"id": 99, "channel": "EXPERIMENTAL", "downloads": {}},
        {"id": 98, "channel": "STABLE", "downloads": {
            "server:default": {
                "name": "paper-26.3-98.jar",
                "url": "https://fill-data.papermc.io/server.jar",
                "checksums": {"sha256": "a" * 64},
                "size": 1234,
            }
        }},
    ]})
    artifact = asyncio.run(PaperProvider(client=client).latest_artifact("26.3"))
    assert artifact.build == "98"
    assert artifact.checksum == "a" * 64
    assert artifact.checksum_algorithm == "sha256"
    assert artifact.filename == "paper-26.3-98.jar"


def test_paper_v3_fails_closed_without_stable_build():
    url = f"{PaperProvider.API}/versions/26.3/builds"
    provider = PaperProvider(client=FakeClient({url: [{"id": 1, "channel": "EXPERIMENTAL"}]}))
    with pytest.raises(ValueError, match="No stable Paper build"):
        asyncio.run(provider.latest_artifact("26.3"))


def test_paper_v3_rejects_malformed_versions_document():
    provider = PaperProvider(client=FakeClient({PaperProvider.API: {"versions": []}}))
    with pytest.raises(ValueError, match="invalid versions"):
        asyncio.run(provider.versions())
