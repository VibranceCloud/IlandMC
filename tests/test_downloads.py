import hashlib, pytest, httpx
from ilandymc.utils.downloads import download_verified
import ilandymc.utils.downloads as downloads

def mocked_client(monkeypatch, response):
    real_client=httpx.AsyncClient
    transport=httpx.MockTransport(lambda request: response)
    monkeypatch.setattr(downloads.httpx,"AsyncClient",
        lambda **kwargs: real_client(transport=transport, **kwargs))

def test_verified_download_is_atomic_and_hash_checked(tmp_path,monkeypatch):
    body=b"minecraft-server-jar"
    mocked_client(monkeypatch,httpx.Response(200,content=body))
    dest=tmp_path/"server.jar"
    digest=__import__("asyncio").run(download_verified(
        "https://downloads.example/server.jar",dest,
        hashlib.sha256(body).hexdigest()))
    assert dest.read_bytes()==body
    assert digest==hashlib.sha256(body).hexdigest()
    assert dest.stat().st_mode & 0o777 == 0o640

def test_checksum_mismatch_leaves_no_destination(tmp_path,monkeypatch):
    mocked_client(monkeypatch,httpx.Response(200,content=b"bad"))
    dest=tmp_path/"server.jar"
    with pytest.raises(ValueError,match="checksum mismatch"):
        __import__("asyncio").run(download_verified(
            "https://downloads.example/server.jar",dest,"0"*64))
    assert not dest.exists()
    assert not list(tmp_path.glob(".download-*"))

def test_download_size_limit(tmp_path,monkeypatch):
    mocked_client(monkeypatch,httpx.Response(200,content=b"too large"))
    with pytest.raises(ValueError,match="size limit"):
        __import__("asyncio").run(download_verified(
            "https://downloads.example/server.jar",tmp_path/"server.jar",max_bytes=2))
