import os, platform, shutil, socket
from pathlib import Path
from pydantic import BaseModel, ConfigDict

class HardwareInfo(BaseModel):
    model_config=ConfigDict(frozen=True)
    cpu_model: str
    logical_threads: int
    physical_cores: int | None
    architecture: str
    ram_total_mb: int
    ram_available_mb: int
    swap_total_mb: int
    swap_free_mb: int
    disk_total_bytes: int
    disk_free_bytes: int
    hostname: str
    local_ip: str | None

def collect_hardware(path=Path("/")):
    mem={}
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            k,_,v=line.partition(":")
            if k in ("MemTotal","MemAvailable","SwapTotal","SwapFree"):
                mem[k]=int(v.split()[0])*1024
    except (OSError,ValueError,IndexError): pass
    cpu="Unknown"; physical=None
    try:
        lines=Path("/proc/cpuinfo").read_text().splitlines()
        cpu=next((x.split(":",1)[1].strip() for x in lines if x.lower().startswith(("model name","hardware"))),platform.processor() or "Unknown")
        physical=len({x.split(":",1)[1].strip() for x in lines if x.startswith("physical id")}) or None
    except OSError: pass
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.connect(("192.0.2.1",80)); ip=s.getsockname()[0]; s.close()
    except OSError: ip=None
    disk=shutil.disk_usage(path)
    return HardwareInfo(cpu_model=cpu,logical_threads=os.cpu_count() or 1,physical_cores=physical,
      architecture=platform.machine(),ram_total_mb=mem.get("MemTotal",0)//1048576,
      ram_available_mb=mem.get("MemAvailable",0)//1048576,swap_total_mb=mem.get("SwapTotal",0)//1048576,
      swap_free_mb=mem.get("SwapFree",0)//1048576,disk_total_bytes=disk.total,disk_free_bytes=disk.free,
      hostname=socket.gethostname(),local_ip=ip)
