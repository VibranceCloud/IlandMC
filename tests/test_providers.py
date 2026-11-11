import pytest
from ilandymc.providers.registry import provider_for
from ilandymc.providers.base import Artifact

def test_provider_registry_known_and_unknown():
    for name in ("vanilla", "paper", "purpur", "fabric"):
        assert provider_for(name).name == name
    with pytest.raises(ValueError):
        provider_for("forge")

def test_artifact_rejects_non_https():
    with pytest.raises(Exception):
        Artifact(software="paper", minecraft_version="1.21.1", build="1",
                 download_url="http://example.org/server.jar")

def test_artifact_checksum_algorithm_is_explicit():
    a = Artifact(software="vanilla", minecraft_version="1.21.1", build="release",
                 download_url="https://example.org/server.jar", checksum="a"*40,
                 checksum_algorithm="sha1")
    assert a.checksum_algorithm == "sha1"


def test_artifact_rejects_credentials_and_checksum_without_algorithm():
    with pytest.raises(Exception):
        Artifact(software="paper", minecraft_version="1.21.1", build="1",
                 download_url="https://user:pass@example.org/a.jar")
    with pytest.raises(Exception):
        Artifact(software="paper", minecraft_version="1.21.1", build="1",
                 download_url="https://example.org/a.jar", checksum="a"*64)


def test_vanilla_version_list_excludes_snapshots_and_old_weekly_ids():
    import asyncio
    from ilandymc.providers.vanilla import VanillaProvider

    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {"versions": [
                {"id": "26.3", "type": "release"},
                {"id": "26.4-snapshot-1", "type": "snapshot"},
                {"id": "25w14a", "type": "snapshot"},
            ]}

    class Client:
        async def get(self, url):
            return Response()

    assert asyncio.run(VanillaProvider(client=Client()).versions()) == ["26.3"]
