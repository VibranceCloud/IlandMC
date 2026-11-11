import json
from pathlib import Path
import pytest
from ilandymc.core.server_manager import ServerManager, ServerError
from ilandymc.core.config_manager import AppConfig, ConfigManager
from ilandymc.core.update_manager import UpdateManager, UpdateError


def make_server(tmp_path):
    root = tmp_path / 'servers'
    path = root / 'survival'
    path.mkdir(parents=True)
    (path / 'ilandy.json').write_text(json.dumps({
        'schema_version': 1, 'name': 'survival', 'software': 'paper',
        'minecraft_version': '1.21.1', 'jar': 'server.jar', 'java': 'java',
        'memory_mb': 2048, 'game_port': 25565
    }))
    (path / 'server.properties').write_text('motd=Hello\nserver-port=25565\nmax-players=20\nonline-mode=false\nwhite-list=false\nrcon.port=25575\nrcon.password=secret\n')
    return ServerManager(root), path


def test_server_config_changes_memory_and_port_atomically(tmp_path):
    manager, path = make_server(tmp_path)
    result = manager.configure('survival', memory_mb=4096, game_port=25575)
    assert result['memory_mb'] == 4096
    assert result['game_port'] == 25575
    assert 'server-port=25575' in (path / 'server.properties').read_text()
    assert 'server-port=25565' not in (path / 'server.properties').read_text()
    assert 'motd=Hello' in (path / 'server.properties').read_text()
    assert manager.metadata('survival')['memory_mb'] == 4096


@pytest.mark.parametrize('memory,port', [(511, None), (None, 1023), (True, None), (None, 65536)])
def test_server_config_rejects_invalid_values(tmp_path, memory, port):
    manager, _ = make_server(tmp_path)
    with pytest.raises(ValueError): manager.configure('survival', memory_mb=memory, game_port=port)


def test_server_config_refuses_running_server(tmp_path, monkeypatch):
    manager, _ = make_server(tmp_path)
    monkeypatch.setattr(manager, 'status', lambda _name: 'running')
    with pytest.raises(ServerError): manager.configure('survival', memory_mb=4096)


def test_app_config_auto_update_defaults_off_and_roundtrips(tmp_path):
    path = tmp_path / 'config.yml'
    manager = ConfigManager(path)
    config = AppConfig(language='ru', auto_update=True,
                       update_manifest_url='https://updates.example/manifest.json')
    manager.save(config)
    loaded = manager.load()
    assert loaded.auto_update is True
    assert loaded.update_manifest_url == 'https://updates.example/manifest.json'


def test_updater_requires_https_manifest():
    with pytest.raises(UpdateError): UpdateManager('http://updates.example/manifest.json').fetch_manifest()


def test_updater_requires_configured_manifest():
    with pytest.raises(UpdateError): UpdateManager(None).fetch_manifest()


def test_updater_semver_ordering():
    assert UpdateManager._version_key('0.7.1') > UpdateManager._version_key('0.7.0')


def test_auto_update_requires_manifest_url():
    with pytest.raises(Exception):
        AppConfig(auto_update=True)


def test_config_rejects_non_https_update_manifest():
    with pytest.raises(Exception):
        AppConfig(update_manifest_url='http://updates.example/manifest.json')


def test_ily_tui_console_entrypoint_is_registered():
    import tomllib
    project = tomllib.loads((Path(__file__).parents[1] / 'pyproject.toml').read_text())
    assert project['project']['scripts']['ily'] == 'ilandymc.main:tui_entry'
    assert project['project']['scripts']['ilandy'] == 'ilandymc.main:app'


def test_server_properties_defaults_and_documented_schema(tmp_path):
    from ilandymc.core.properties import SPECS
    manager, path = make_server(tmp_path)
    values = manager.properties('survival')
    assert len(SPECS) >= 65
    assert values['online-mode'] == 'false'
    assert {spec.key for spec in manager.supported_specs('survival')} == set(values)
    assert values['server-port'] == '25565'
    assert len({spec.key for spec in SPECS}) == len(SPECS)
    assert all(spec.description for spec in SPECS)


def test_server_properties_update_and_metadata_sync(tmp_path):
    manager, path = make_server(tmp_path)
    values = manager.set_properties('survival', {
        'online-mode': 'true', 'white-list': 'true', 'max-players': '42',
        'server-port': '25577', 'rcon.port': '25576', 'rcon.password': 'a-long-test-secret'
    })
    assert values['online-mode'] == 'true'
    assert values['white-list'] == 'true'
    assert values['max-players'] == '42'
    assert manager.metadata('survival')['game_port'] == 25577
    assert manager.metadata('survival')['rcon_port'] == 25576
    assert (path / 'rcon.secret').read_text().strip() == 'a-long-test-secret'
    assert 'server-port=25577' in (path / 'server.properties').read_text()


@pytest.mark.parametrize('key,value', [
    ('online-mode', 'yes'), ('max-players', '0'), ('difficulty', 'nightmare'),
    ('server-port', '65536'), ('unknown-property', '1'),
])
def test_server_properties_reject_invalid_values(tmp_path, key, value):
    manager, _ = make_server(tmp_path)
    with pytest.raises(ValueError):
        manager.set_properties('survival', {key: value})


def test_server_properties_refuse_running_server(tmp_path, monkeypatch):
    manager, _ = make_server(tmp_path)
    monkeypatch.setattr(manager, 'status', lambda _name: 'running')
    with pytest.raises(ServerError):
        manager.set_properties('survival', {'online-mode': 'true'})


def test_default_26_3_template_is_sanitized_and_online_mode_off():
    from pathlib import Path
    from ilandymc.core.properties import parse_properties, SPECS
    template = Path(__file__).parents[1] / 'ilandymc' / 'data' / 'server.properties'
    values, _ = parse_properties(template.read_text())
    assert values['online-mode'] == 'false'
    assert values['management-server-enabled'] == 'false'
    assert values['management-server-secret'] == ''
    assert values['rcon.password'] == ''
    assert values['motd'] == 'A Minecraft Server'
    assert set(values) == {spec.key for spec in SPECS}


def test_server_properties_preserve_unknown_keys(tmp_path):
    manager, path = make_server(tmp_path)
    with (path / 'server.properties').open('a') as stream:
        stream.write('custom-provider-option=keep-me\n')
    manager.set_properties('survival', {'max-players': '32'})
    assert 'custom-provider-option=keep-me' in (path / 'server.properties').read_text()


def test_server_properties_refuse_unverifiable_systemd_service(tmp_path, monkeypatch):
    import ilandymc.system.systemd as systemd
    manager, _ = make_server(tmp_path)
    class FakeSystemd:
        def installed(self, _name): return True
        def status(self, _name): raise RuntimeError('systemctl unavailable')
    monkeypatch.setattr(systemd, 'SystemdManager', FakeSystemd)
    with pytest.raises(ServerError, match='Cannot verify systemd'):
        manager.set_properties('survival', {'online-mode': 'true'})


def test_unsupported_properties_are_hidden_and_rejected(tmp_path):
    manager, path = make_server(tmp_path)
    (path / 'server.properties').write_text('motd=Old\nserver-port=25565\n')
    assert {spec.key for spec in manager.supported_specs('survival')} == {'motd', 'server-port'}
    with pytest.raises(ValueError, match='not supported'):
        manager.set_properties('survival', {'online-mode': 'false'})


def test_configure_does_not_invent_missing_server_port(tmp_path):
    manager, path = make_server(tmp_path)
    (path / 'server.properties').write_text('motd=Old\n')
    with pytest.raises(ValueError, match='does not expose server-port'):
        manager.configure('survival', game_port=25580)


def test_bootstrap_reads_properties_generated_by_server(tmp_path):
    from ilandymc.core.installer import _bootstrap_properties
    staging = tmp_path / 'stage'; staging.mkdir()
    (staging / 'server.jar').write_bytes(b'fake jar')
    fake_java = tmp_path / 'fake-java'
    fake_java.write_text("""#!/bin/sh
printf 'motd=Legacy\\nserver-port=25565\\nonline-mode=true\\n' > server.properties
printf 'Done (0.5s)! For help, type help\n'
while IFS= read -r line; do [ "$line" = stop ] && exit 0; done
""")
    fake_java.chmod(0o755)
    values = _bootstrap_properties(staging, str(fake_java), 512, timeout=5)
    assert set(values) == {'motd', 'server-port', 'online-mode'}
    assert values['online-mode'] == 'true'
