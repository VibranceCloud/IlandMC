import socket, struct

class RCONError(RuntimeError): pass

class RCONClient:
    """Minimal Minecraft-compatible Source RCON client."""
    def __init__(self, host, port, password, timeout=2.0):
        self.host, self.port, self.password, self.timeout = host, int(port), password, timeout
    @staticmethod
    def _packet(request_id, kind, body):
        payload = struct.pack("<ii", request_id, kind) + body.encode("utf-8") + b"\0\0"
        return struct.pack("<i", len(payload)) + payload
    @staticmethod
    def _read_exact(sock, count):
        chunks = bytearray()
        while len(chunks) < count:
            part = sock.recv(count - len(chunks))
            if not part: raise RCONError("RCON connection closed")
            chunks.extend(part)
        return bytes(chunks)
    def command(self, command):
        if not command or "\0" in command: raise ValueError("Invalid RCON command")
        with socket.create_connection((self.host, self.port), timeout=self.timeout) as sock:
            sock.settimeout(self.timeout)
            sock.sendall(self._packet(1, 3, self.password))
            length = struct.unpack("<i", self._read_exact(sock, 4))[0]
            if length < 10 or length > 65536: raise RCONError("Invalid RCON response length")
            response = self._read_exact(sock, length)
            auth_id, auth_type = struct.unpack("<ii", response[:8])
            if auth_id == -1 or auth_type != 2: raise RCONError("RCON authentication failed")
            sock.sendall(self._packet(2, 2, command))
            length = struct.unpack("<i", self._read_exact(sock, 4))[0]
            if length < 10 or length > 65536: raise RCONError("Invalid RCON response length")
            response = self._read_exact(sock, length)
            request_id, response_type = struct.unpack("<ii", response[:8])
            if request_id != 2 or response_type != 0: raise RCONError("Unexpected RCON response")
            return response[8:-2].decode("utf-8", errors="replace")
