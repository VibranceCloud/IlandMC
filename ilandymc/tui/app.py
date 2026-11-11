from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Header, Footer, Label, Select, Input, Button, Static, Switch
from ilandymc.core.config_manager import ConfigManager
from ilandymc.core.server_manager import ServerManager, ServerError
from ilandymc.core.properties import SPECS
from ilandymc.core.update_manager import UpdateManager, UpdateError
from ilandymc.system.systemd import SystemdManager

class IlandyApp(App):
    TITLE = "IlandyMC"
    SUB_TITLE = "Minecraft Server Manager"
    CSS = """
    Screen { background: #10151f; color: #e6edf3; }
    #body { padding: 1 2; height: 1fr; }
    .row { height: auto; margin: 1 0; }
    .field { width: 1fr; }
    #message { height: auto; min-height: 3; color: #4fc3d7; padding: 1; }
    Button { margin-right: 1; }
    #properties-list { height: 1fr; border: round #34445a; padding: 1; }
    .property { height: auto; padding: 1 0; border-bottom: solid #263449; }
    .property-description { color: #9aa9ba; }
    """
    BINDINGS = [("q", "quit", "Quit"), ("r", "refresh", "Refresh")]

    def __init__(self, language=None):
        super().__init__()
        self.config = ConfigManager()
        self.manager = ServerManager()
        self.language = language

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="body"):
            yield Label("I L A N D Y M C  —  Your Minecraft Server. One Command Away.")
            yield Label("Server")
            yield Select([], prompt="Select a server", id="server", classes="field")
            with Horizontal(classes="row"):
                yield Button("Start", id="start", variant="success")
                yield Button("Stop", id="stop", variant="error")
                yield Button("Refresh", id="refresh")
            yield Label("Server settings (stop the server before editing)")
            with Horizontal(classes="row"):
                with Vertical(classes="field"):
                    yield Label("RAM limit (MiB)")
                    yield Input(placeholder="2048", id="memory", type="integer")
            yield Label("server.properties — значение и описание каждой настройки")
            with VerticalScroll(id="properties-list"):
                for spec in SPECS:
                    control_id = "prop-" + spec.key.replace(".", "-")
                    with Vertical(classes="property"):
                        yield Label(spec.label)
                        if spec.kind == "bool":
                            yield Switch(value=(spec.default.lower() == "true"), id=control_id)
                        elif spec.kind == "enum":
                            yield Select([(choice, choice) for choice in spec.choices],
                                         value=spec.default, id=control_id, allow_blank=False)
                        else:
                            secret = spec.key in {"rcon.password", "management-server-secret",
                                                  "management-server-tls-keystore-password"}
                            yield Input(value=spec.default, placeholder=spec.default,
                                        id=control_id, type="integer" if spec.kind == "int" else "text",
                                        password=secret)
                        yield Static(spec.description, classes="property-description")
            with Horizontal(classes="row"):
                yield Button("Save all settings", id="save", variant="primary")
                yield Button("Check updates", id="updates")
                yield Button("Apply update", id="apply-update")
            yield Static("Ready", id="message")
        yield Footer()

    def on_mount(self):
        self.refresh_servers()

    def _message(self, value):
        self.query_one("#message", Static).update(value)

    def refresh_servers(self):
        names = self.manager.list()
        self.query_one("#server", Select).set_options([(n, n) for n in names])
        if names:
            self.query_one("#server", Select).value = names[0]
            self.load_selected(names[0])
        else:
            self._message("No managed servers found. Install one with: ilandy install NAME ...")

    def action_refresh(self):
        self.refresh_servers()

    def on_select_changed(self, event: Select.Changed):
        if event.select.id == "server" and event.value is not Select.BLANK:
            self.load_selected(str(event.value))

    def load_selected(self, name):
        try:
            meta = self.manager.metadata(name)
            self.query_one("#memory", Input).value = str(meta["memory_mb"])
            values = self.manager.properties(name)
            supported = {spec.key for spec in self.manager.supported_specs(name)}
            for spec in SPECS:
                control_id = "#prop-" + spec.key.replace(".", "-")
                control = self.query_one(control_id)
                control.display = spec.key in supported
                # The enclosing property card is hidden too, including its description.
                card = control.parent
                if card is not None:
                    card.display = spec.key in supported
                if spec.key not in supported:
                    continue
                value = values.get(spec.key, spec.default)
                if spec.kind == "bool":
                    self.query_one(control_id, Switch).value = value.lower() == "true"
                elif spec.kind == "enum":
                    selector = self.query_one(control_id, Select)
                    if value not in spec.choices:
                        selector.set_options([(choice, choice) for choice in (*spec.choices, value)])
                    selector.value = value
                else:
                    self.query_one(control_id, Input).value = value
            service = SystemdManager()
            state = service.status(name) if service.installed(name) else self.manager.status(name)
            self._message(f"{name}: {state} · {meta['software']} {meta['minecraft_version']}")
        except Exception as exc:
            self._message(f"Error: {exc}")

    def _selected(self):
        value = self.query_one("#server", Select).value
        if value is Select.BLANK: raise ValueError("Select a server first")
        return str(value)

    def on_button_pressed(self, event: Button.Pressed):
        try:
            name = self._selected() if event.button.id not in ("updates", "apply-update") else None
            if event.button.id == "start":
                service = SystemdManager()
                service.start(name) if service.installed(name) else self.manager.start(name)
                self._message(f"Start requested: {name}")
            elif event.button.id == "stop":
                service = SystemdManager()
                service.stop(name) if service.installed(name) else self.manager.stop(name)
                self._message(f"Stop requested: {name}")
            elif event.button.id == "save":
                memory = int(self.query_one("#memory", Input).value)
                updates = {}
                for spec in self.manager.supported_specs(name):
                    control_id = "#prop-" + spec.key.replace(".", "-")
                    if spec.kind == "bool":
                        value = self.query_one(control_id, Switch).value
                        updates[spec.key] = "true" if value else "false"
                    elif spec.kind == "enum":
                        updates[spec.key] = str(self.query_one(control_id, Select).value)
                    else:
                        updates[spec.key] = self.query_one(control_id, Input).value
                service = SystemdManager()
                if service.installed(name) and service.status(name) == "active":
                    raise RuntimeError("Stop the systemd service before changing settings")
                data = self.manager.configure(name, memory_mb=memory)
                self.manager.set_properties(name, updates)
                if service.installed(name):
                    service.refresh(name, self.manager.server_path(name), java=data.get("java", "java"),
                                    memory_mb=data["memory_mb"], jar=data["jar"])
                self._message(f"Settings saved: {name}")
            elif event.button.id == "refresh":
                self.refresh_servers()
            elif event.button.id in ("updates", "apply-update"):
                cfg = self.config.load()
                updater = UpdateManager(cfg.update_manifest_url)
                release = updater.check()
                if event.button.id == "apply-update":
                    if not cfg.auto_update: raise UpdateError("Enable auto_update in config.yml first")
                    updater.apply(release)
                self._message(f"Latest: {release['version']} · update available: {release['update_available']}")
            if name: self.load_selected(name)
        except Exception as exc:
            self._message(f"Error: {exc}")

def run_tui(language=None):
    IlandyApp(language).run()
