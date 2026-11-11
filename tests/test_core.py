import json
from pathlib import Path
import pytest
from ilandymc.core.os_detector import detect_os
from ilandymc.core.config_manager import ConfigManager,AppConfig
from ilandymc.core.server_manager import ServerManager
from ilandymc.core.java_manager import required_java_major
from ilandymc.localization.manager import Localization

def test_locale_key_parity():
 a=Localization.load("en").data; b=Localization.load("ru").data
 def keys(x,p=""):
  out=set()
  for k,v in x.items():
   q=f"{p}.{k}" if p else k
   out |= keys(v,q) if isinstance(v,dict) else {q}
  return out
 assert keys(a)==keys(b)

def test_config_permissions(tmp_path):
 p=tmp_path/"c.yml"; m=ConfigManager(p); m.save(AppConfig(language="ru"))
 assert m.load().language=="ru" and p.stat().st_mode&0o777==0o600

def test_os_unknown_not_supported(tmp_path):
 p=tmp_path/"os-release"; p.write_text("ID=alpine\n")
 assert not detect_os(p,tmp_path/"none").supported

def test_server_name_traversal_blocked(tmp_path):
 m=ServerManager(tmp_path)
 with pytest.raises(ValueError): m.server_path("../escape")

@pytest.mark.parametrize("v,j", [("1.21.1",21),("1.20.4",17),("1.17.1",16),("1.16.5",8)])
def test_java_requirements(v,j): assert required_java_major(v)==j
