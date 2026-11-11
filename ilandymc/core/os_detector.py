import platform, shutil
from pathlib import Path
from pydantic import BaseModel, ConfigDict

class OSInfo(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    name: str
    pretty_name: str
    version_id: str | None
    package_manager: str | None
    architecture: str
    kernel: str
    systemd_available: bool
    supported: bool

def detect_os(release=Path("/etc/os-release"), systemd_dir=Path("/run/systemd/system")):
    data = {}
    try:
        for line in release.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.startswith("#"):
                k,v=line.split("=",1); data[k]=v.strip().strip('"').strip("'")
    except OSError:
        pass
    ident=data.get("ID","unknown").lower()
    likes=data.get("ID_LIKE","").lower().split()
    supported=ident in ("ubuntu","debian") or bool({"ubuntu","debian"} & set(likes))
    apt=shutil.which("apt-get") is not None and supported
    systemd=systemd_dir.exists() and shutil.which("systemctl") is not None
    return OSInfo(id=ident,name=data.get("NAME",platform.system()),
        pretty_name=data.get("PRETTY_NAME",data.get("NAME","Unknown")),
        version_id=data.get("VERSION_ID"),package_manager="apt" if apt else None,
        architecture=platform.machine(),kernel=platform.release(),
        systemd_available=systemd,supported=supported)
