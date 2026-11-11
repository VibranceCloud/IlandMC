import struct
import pytest
from ilandymc.core.rcon import RCONClient, RCONError
import ilandymc.core.rcon as rcon

class FakeSocket:
    def __init__(self, auth_ok=True):
        self.auth_ok=auth_ok
        self.pending=b""
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def settimeout(self, value): pass
    def sendall(self, packet):
        length=struct.unpack("<i",packet[:4])[0]
        request_id, kind=struct.unpack("<ii",packet[4:12])
        if kind == 3:
            self.pending=RCONClient._packet(1 if self.auth_ok else -1, 2, "")
        elif kind == 2:
            self.pending=RCONClient._packet(2, 0, "Server stopping")
    def recv(self, count):
        result=self.pending[:count]
        self.pending=self.pending[count:]
        return result

def test_rcon_auth_and_command(monkeypatch):
    monkeypatch.setattr(rcon.socket,"create_connection",lambda *a,**k:FakeSocket())
    assert RCONClient("127.0.0.1",25575,"secret").command("stop") == "Server stopping"

def test_rcon_rejects_auth_failure(monkeypatch):
    monkeypatch.setattr(rcon.socket,"create_connection",lambda *a,**k:FakeSocket(auth_ok=False))
    with pytest.raises(RCONError,match="authentication"):
        RCONClient("127.0.0.1",25575,"wrong").command("stop")

def test_rcon_rejects_empty_command():
    with pytest.raises(ValueError):
        RCONClient("127.0.0.1",25575,"secret").command("")
