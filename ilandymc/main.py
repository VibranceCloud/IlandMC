import json, typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from ilandymc import __version__
from ilandymc.core.os_detector import detect_os
from ilandymc.core.hardware import collect_hardware
from ilandymc.core.server_manager import ServerManager
from ilandymc.core.installer import install_server
from ilandymc.core.backup_manager import BackupManager
from ilandymc.core.config_manager import ConfigManager,AppConfig
from ilandymc.system.systemd import SystemdManager
from ilandymc.core.update_manager import UpdateManager
from ilandymc.localization.manager import Localization

app=typer.Typer(help="IlandyMC — Your Minecraft Server. One Command Away.")
console=Console()

@app.callback(invoke_without_command=True)
def common(ctx:typer.Context,language:Optional[str]=typer.Option(None,"--language"),yes:bool=typer.Option(False,"--yes","-y"),
 dry_run:bool=typer.Option(False,"--dry-run"),as_json:bool=typer.Option(False,"--json"),
 non_interactive:bool=typer.Option(False,"--non-interactive")):
 ctx.ensure_object(dict); ctx.obj.update(language=language,yes=yes,dry_run=dry_run,json=as_json,non_interactive=non_interactive)
 if ctx.invoked_subcommand is None:
  if non_interactive: raise typer.Exit(2)
  from ilandymc.tui.app import run_tui
  run_tui(language)

@app.command()
def version(): console.print(__version__)

@app.command()
def doctor(ctx:typer.Context):
 o=detect_os(); h=collect_hardware()
 d={"os":o.model_dump(),"hardware":h.model_dump()}
 if ctx.obj["json"]: console.print_json(json.dumps(d)); return
 l=Localization.load(ctx.obj["language"] or "en"); t=Table(title=l.t("doctor.title"))
 t.add_column("Item"); t.add_column("Value")
 for k,v in [(l.t("doctor.os"),o.pretty_name),(l.t("doctor.arch"),h.architecture),(l.t("doctor.cpu"),h.cpu_model),
  (l.t("doctor.cores"),f"{h.physical_cores}/{h.logical_threads}"),(l.t("doctor.ram"),f"{h.ram_total_mb}/{h.ram_available_mb} MB"),
  (l.t("doctor.disk"),f"{h.disk_free_bytes//1073741824} GiB"),(l.t("doctor.systemd"),str(o.systemd_available)),(l.t("doctor.package"),o.package_manager or "—")]:
  t.add_row(k,str(v))
 console.print(t)
 if not o.supported: console.print(l.t("msg.unsupported"),style="yellow")

@app.command("list")
def list_servers(ctx:typer.Context):
 names=ServerManager().list()
 if ctx.obj["json"]: console.print_json(json.dumps({"servers":names}))
 elif names:
  for n in names: console.print(n)
 else: console.print(Localization.load(ctx.obj["language"] or "en").t("msg.none"))

@app.command()
def config(ctx:typer.Context, language:Optional[str]=None,
           auto_update: Optional[bool] = typer.Option(None, "--auto-update/--no-auto-update"),
           manifest_url: Optional[str] = typer.Option(None, help="HTTPS release manifest URL")):
 m=ConfigManager(); c=m.load(); values=c.model_dump()
 if language is not None:
  if language not in ("en","ru"): raise typer.BadParameter("Choose en or ru")
  values["language"] = language
 if auto_update is not None: values["auto_update"] = auto_update
 if manifest_url is not None: values["update_manifest_url"] = manifest_url
 c=AppConfig.model_validate(values); m.save(c)
 console.print_json(json.dumps({"path":str(m.path),**c.model_dump()}))

@app.command()
def install(server: str, ctx:typer.Context,
            software: str = typer.Option("paper", help="vanilla, paper, purpur, fabric"),
            version: str = typer.Option(..., help="Minecraft version, e.g. 1.21.11 or 26.3"),
            memory: int = typer.Option(2048, min=512, max=1_000_000, help="RAM in MiB"),
            port: int = typer.Option(25565, min=1024, max=65535, help="Minecraft TCP port"),
            java: str = typer.Option("java", help="Java executable"),
            accept_eula: bool = typer.Option(False, "--accept-eula", help="Confirm Minecraft EULA"),
            dry_run: bool = typer.Option(False, "--dry-run")):
    """Install a Minecraft server into the managed server directory."""
    path = install_server(server, software.lower(), version, memory,
                          java=java, dry_run=(dry_run or ctx.obj.get("dry_run", False)),
                          accept_eula=accept_eula, game_port=port)
    console.print(f"Installation {'plan' if dry_run else 'completed'}: {path}")

@app.command()
def providers():
    console.print("vanilla, paper, purpur, fabric")

@app.command()
def status(server:str):
 sm=SystemdManager()
 console.print(sm.status(server) if sm.installed(server) else ServerManager().status(server))

@app.command()
def start(server:str,ctx:typer.Context):
 sm=SystemdManager()
 if sm.installed(server): sm.start(server)
 else: ServerManager().start(server)
 console.print("Start requested")

@app.command()
def stop(server:str):
 sm=SystemdManager()
 if sm.installed(server): sm.stop(server)
 else: ServerManager().stop(server)
 console.print("Stop requested")

@app.command()
def restart(server:str):
 sm=SystemdManager()
 if sm.installed(server): sm.restart(server)
 else:
  m=ServerManager(); m.stop(server); m.start(server)
 console.print("Restart requested")

@app.command()
def info(server:Optional[str]=None):
 if server: console.print_json(json.dumps(ServerManager().metadata(server)))
 else: doctor(typer.Context(app, obj={"json":False,"language":"en"}))

@app.command()
def backup(server:str):
 p=BackupManager().create(server); console.print(str(p))

@app.command()
def restore(server:str,archive:Path):
 BackupManager().restore(archive,server); console.print("Restore completed")

@app.command()
def logs(server:str,follow:bool=False):
 p=ServerManager().server_path(server)/"server.log"
 if not p.is_file(): raise typer.BadParameter("Log file does not exist")
 if follow:
  import subprocess
  subprocess.run(["tail","-f",str(p)],check=False)
 else: console.print(p.read_text(errors="replace")[-20000:])


@app.command("service-install")
def service_install(server: str, user: str = typer.Option("minecraft", help="Unprivileged system account"),
                    java: str = typer.Option("java"), enable: bool = typer.Option(True, "--enable/--no-enable")):
    """Install a hardened systemd unit and optionally enable/start it (requires root)."""
    manager = ServerManager(); meta = manager.metadata(server)
    unit = SystemdManager().install(server, manager.server_path(server), user=user,
        java=java if java != "java" else meta.get("java", "java"),
        memory_mb=meta["memory_mb"], jar=meta["jar"], enable=enable)
    console.print(f"Installed systemd unit: {unit}")

@app.command("service-uninstall")
def service_uninstall(server: str):
    """Disable and remove a managed systemd unit (requires root)."""
    path = SystemdManager().uninstall(server); console.print(f"Removed systemd unit: {path}")

@app.command("service-status")
def service_status(server: str):
    """Show systemd service state."""
    console.print(SystemdManager().status(server))

@app.command("server-config")
def server_config(server: str, memory: Optional[int] = typer.Option(None, min=512, max=1_000_000),
                  port: Optional[int] = typer.Option(None, min=1024, max=65535)):
    """Change server memory and/or game port while the server is stopped."""
    if memory is None and port is None:
        console.print_json(json.dumps(ServerManager().metadata(server))); return
    manager = ServerManager()
    service = SystemdManager()
    if service.installed(server) and service.status(server) == "active":
        raise typer.BadParameter("Stop the systemd service before changing server settings")
    result = manager.configure(server, memory_mb=memory, game_port=port)
    if service.installed(server):
        service.refresh(server, manager.server_path(server), java=result.get("java", "java"),
                       memory_mb=result["memory_mb"], jar=result["jar"])
    console.print_json(json.dumps(result))

@app.command("server-properties")
def server_properties(server: str, set_values: list[str] = typer.Option([], "--set", help="Set KEY=VALUE (repeatable)")):
    """View or edit documented server.properties settings while the server is stopped."""
    manager = ServerManager()
    if set_values:
        updates = {}
        for item in set_values:
            if "=" not in item:
                raise typer.BadParameter("Each --set value must use KEY=VALUE")
            key, value = item.split("=", 1)
            if key in updates:
                raise typer.BadParameter(f"Duplicate property: {key}")
            updates[key] = value
        values = manager.set_properties(server, updates)
        console.print(f"Saved {len(updates)} setting(s) for {server}")
    else:
        values = manager.properties(server)
    table = Table(title=f"{server} — server.properties")
    table.add_column("Setting")
    table.add_column("Value")
    table.add_column("Description")
    for spec in manager.supported_specs(server):
        value = values.get(spec.key, spec.default)
        if spec.kind == "bool": value = "ON" if str(value).lower() == "true" else "OFF"
        if spec.key in {"rcon.password", "management-server-secret", "management-server-tls-keystore-password"}:
            value = "********" if value else "(empty)"
        table.add_row(spec.label, str(value), spec.description)
    if not manager.supported_specs(server):
        console.print("This server version exposes no documented editable properties.")
    console.print(table)


@app.command("update-check")
def update_check():
    cfg = ConfigManager().load()
    result = UpdateManager(cfg.update_manifest_url).check()
    console.print_json(json.dumps(result))
    if not result["update_available"]: console.print("Already up to date")

@app.command("self-update")
def self_update():
    cfg = ConfigManager().load()
    if not cfg.auto_update:
        raise typer.BadParameter("Automatic updates are disabled. Enable auto_update in config.yml first.")
    updater = UpdateManager(cfg.update_manifest_url)
    release = updater.check()
    if updater.apply(release): console.print(f"Updated IlandyMC to {release['version']}")
    else: console.print("Already up to date")

def tui_entry():
    cfg = ConfigManager().load()
    if cfg.auto_update and cfg.update_manifest_url:
        try:
            updater = UpdateManager(cfg.update_manifest_url)
            updater.apply(updater.check())
        except Exception as exc:
            console.print(f"Automatic update skipped: {exc}", style="yellow")
    from ilandymc.tui.app import run_tui
    run_tui(cfg.language)

def main(): app()
if __name__=="__main__": main()
