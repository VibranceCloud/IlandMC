"""Typed and documented Minecraft server.properties catalogue."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PropertySpec:
    key: str
    label: str
    kind: str
    description: str
    default: str
    choices: tuple[str, ...] = ()
    minimum: int | None = None
    maximum: int | None = None


# key: (Russian label, control type, explanation, choices, minimum, maximum)
_INFO = {
"accepts-transfers": ("Принимать переносы игроков", "bool", "Разрешает другим серверам передавать игроков на этот сервер."),
"allow-flight": ("Разрешить полёт", "bool", "Не кикает игроков за полёт. Полезно для модов и некоторых механик."),
"broadcast-console-to-ops": ("Показывать консольные сообщения операторам", "bool", "Отправляет операторам игровые сообщения, введённые в консоли."),
"broadcast-rcon-to-ops": ("Показывать RCON-команды операторам", "bool", "Отправляет операторам сообщения о командах, выполненных через RCON."),
"bug-report-link": ("Ссылка на сообщения об ошибках", "text", "Ссылка, отображаемая игрокам для отправки отчётов об ошибках."),
"chat-spam-threshold-seconds": ("Порог спама в чате", "int", "Порог частоты сообщений в чате; точное поведение зависит от версии сервера.", (), 0, 3600),
"command-spam-threshold-seconds": ("Порог спама командами", "int", "Порог частоты выполнения команд; точное поведение зависит от версии сервера.", (), 0, 3600),
"difficulty": ("Сложность", "enum", "Уровень сложности мира: мирный, лёгкий, обычный или сложный.", ("peaceful", "easy", "normal", "hard")),
"enable-code-of-conduct": ("Включить правила поведения", "bool", "Включает поддержку правил поведения, если она реализована сборкой."),
"enable-jmx-monitoring": ("JMX-мониторинг", "bool", "Открывает JMX-интерфейс мониторинга Java. Включайте только при необходимости."),
"enable-query": ("Включить Query", "bool", "Открывает GameSpy4 Query для получения сведений о сервере внешними инструментами."),
"enable-rcon": ("Включить RCON", "bool", "Разрешает удалённое управление сервером. IlandyMC настраивает RCON на loopback."),
"enable-status": ("Показывать сервер в списке мультиплеера", "bool", "Разрешает отвечать на запрос статуса и показывать сервер в списке серверов."),
"enforce-secure-profile": ("Требовать защищённый профиль", "bool", "Требует криптографически подписанный профиль чата от клиента."),
"enforce-whitelist": ("Строго применять белый список", "bool", "Не пускает игроков, которых нет в whitelist, даже при обходных механизмах."),
"entity-broadcast-range-percentage": ("Дальность отправки сущностей (%)", "int", "Множитель дистанции, на которой сервер отправляет сущности клиентам.", (), 10, 1000),
"force-gamemode": ("Принудительно применять режим игры", "bool", "При входе игрока устанавливает режим игры, заданный параметром gamemode."),
"function-permission-level": ("Уровень прав функций", "int", "Максимальный уровень прав команд, выполняемых функциями datapack.", (), 1, 4),
"gamemode": ("Режим игры по умолчанию", "enum", "Режим для новых игроков: выживание, творческий, приключение или наблюдатель.", ("survival", "creative", "adventure", "spectator")),
"generate-structures": ("Генерировать структуры", "bool", "Создаёт деревни, крепости и другие структуры при генерации чанков."),
"generator-settings": ("Настройки генератора мира", "text", "JSON-параметры генератора мира. Оставьте {} для стандартной генерации."),
"hardcore": ("Хардкор", "bool", "Включает хардкорный режим: смерть игрока приводит к блокировке/режиму наблюдателя."),
"hide-online-players": ("Скрывать список игроков", "bool", "Не раскрывает список подключённых игроков в ответе статуса сервера."),
"initial-disabled-packs": ("Отключённые datapack при старте", "text", "Список datapack, которые нужно отключить при создании/загрузке мира."),
"initial-enabled-packs": ("Включённые datapack при старте", "text", "Список datapack, которые нужно включить при создании/загрузке мира."),
"level-name": ("Название папки мира", "text", "Имя каталога, в котором хранятся файлы мира."),
"level-seed": ("Сид мира", "text", "Число или строка для генерации мира. Пустое значение создаёт случайный сид."),
"level-type": ("Тип генерации мира", "text", "Идентификатор генератора/типа мира, поддерживаемый текущей версией."),
"log-ips": ("Записывать IP-адреса в лог", "bool", "Разрешает включать IP-адреса игроков в журналы сервера."),
"management-server-allowed-origins": ("Разрешённые источники Management API", "text", "Список разрешённых Origin для встроенного интерфейса управления."),
"management-server-enabled": ("Встроенный Management API", "bool", "Включает встроенный API управления. Не открывайте его наружу без отдельной защиты."),
"management-server-host": ("Адрес Management API", "text", "Сетевой адрес привязки Management API. Для локального доступа используйте 127.0.0.1."),
"management-server-port": ("Порт Management API", "int", "TCP-порт встроенного API управления.", (), 1024, 65535),
"management-server-secret": ("Секрет Management API", "text", "Секрет доступа к Management API. Храните его приватно; пустое значение отключает заданный секрет."),
"management-server-tls-enabled": ("TLS для Management API", "bool", "Включает TLS для встроенного API управления."),
"management-server-tls-keystore": ("Файл TLS-хранилища", "text", "Путь к Java keystore с сертификатом для Management API."),
"management-server-tls-keystore-password": ("Пароль TLS-хранилища", "text", "Пароль Java keystore. Не используйте пароль от других сервисов."),
"max-chained-neighbor-updates": ("Лимит связанных обновлений блоков", "int", "Ограничивает цепочки обновлений соседних блоков для защиты от зависаний.", (), -1, 10000000),
"max-players": ("Максимум игроков", "int", "Максимальное число одновременно подключённых игроков.", (), 1, 10000),
"max-tick-time": ("Лимит времени тика (мс)", "int", "Время до watchdog-остановки сервера при слишком долгом тике. -1 отключает лимит.", (), -1, 3600000),
"max-world-size": ("Максимальный размер мира", "int", "Ограничивает радиус границы мира в блоках.", (), 1, 29999984),
"motd": ("Описание сервера (MOTD)", "text", "Текст под названием сервера в списке мультиплеера. Поддерживает форматирование Minecraft."),
"network-compression-threshold": ("Порог сжатия сети", "int", "Пакеты больше этого размера сжимаются. -1 отключает сжатие.", (), -1, 65536),
"online-mode": ("Проверка лицензии (online-mode)", "bool", "Проверяет игроков через сервисы авторизации Minecraft. Выключено по умолчанию по запросу администратора; без защищённого прокси возможна подмена ника."),
"op-permission-level": ("Уровень прав оператора", "int", "Уровень прав, выдаваемый игрокам со статусом OP.", (), 1, 4),
"pause-when-empty-seconds": ("Пауза при пустом сервере (сек.)", "int", "Через сколько секунд без игроков сервер может приостанавливать игровое время.", (), -1, 86400),
"player-idle-timeout": ("Кик за бездействие (мин.)", "int", "Отключает игрока после указанного времени бездействия. 0 отключает таймер.", (), 0, 10080),
"prevent-proxy-connections": ("Запретить прокси-подключения", "bool", "Включает проверку прокси-подключений; может конфликтовать с легитимным прокси."),
"previews-chat": ("Предпросмотр чата", "bool", "Включает предварительный просмотр форматирования сообщений чата."),
"query.port": ("Порт Query", "int", "UDP-порт для GameSpy4 Query.", (), 1, 65535),
"rate-limit": ("Ограничение частоты подключений", "int", "Лимит частоты подключений с одного IP; 0 отключает ограничение.", (), 0, 100000),
"rcon.ip": ("IP привязки RCON", "text", "Адрес интерфейса RCON. Оставляйте 127.0.0.1, чтобы не открывать удалённую консоль в интернет."),
"rcon.password": ("Пароль RCON", "text", "Пароль удалённой консоли. Используйте длинный случайный секрет; IlandyMC синхронизирует его с внутренним секретом остановки."),
"rcon.port": ("Порт RCON", "int", "TCP-порт удалённой консоли.", (), 1, 65535),
"region-file-compression": ("Сжатие файлов регионов", "enum", "Алгоритм сжатия файлов регионов мира.", ("deflate", "gzip", "none")),
"require-resource-pack": ("Обязательный ресурс-пак", "bool", "Не пускает игрока, если он отказывается загрузить обязательный ресурс-пак."),
"resource-pack": ("URL ресурс-пака", "text", "Прямая HTTPS-ссылка на архив ресурс-пака."),
"resource-pack-id": ("UUID ресурс-пака", "text", "Уникальный идентификатор ресурс-пака."),
"resource-pack-prompt": ("Сообщение о ресурс-паке", "text", "Текст приглашения загрузить ресурс-пак."),
"resource-pack-sha1": ("SHA-1 ресурс-пака", "text", "SHA-1 архива для проверки целостности ресурс-пака."),
"server-ip": ("IP привязки сервера", "text", "IP-адрес интерфейса для прослушивания. Пустое значение слушает все интерфейсы."),
"server-port": ("Игровой порт", "int", "TCP-порт, на котором игроки подключаются к Minecraft-серверу.", (), 1024, 65535),
"simulation-distance": ("Дистанция симуляции", "int", "Радиус чанков, в которых сервер рассчитывает сущности и механику.", (), 2, 32),
"spawn-protection": ("Защита спавна", "int", "Радиус защиты блоков вокруг точки появления от игроков без OP. 0 отключает защиту.", (), 0, 1024),
"status-heartbeat-interval": ("Интервал status heartbeat", "int", "Интервал heartbeat статуса в секундах; 0 использует поведение по умолчанию.", (), 0, 86400),
"sync-chunk-writes": ("Синхронная запись чанков", "bool", "Синхронно записывает чанки на диск. Может влиять на производительность и надёжность."),
"text-filtering-config": ("Конфигурация фильтрации текста", "text", "Параметры внешней фильтрации текста, если она используется."),
"text-filtering-version": ("Версия фильтрации текста", "int", "Версия протокола конфигурации фильтрации текста.", (), 0, 100),
"use-native-transport": ("Нативный сетевой транспорт", "bool", "Использует оптимизированный сетевой транспорт ОС, если он доступен."),
"view-distance": ("Дальность прорисовки (чанки)", "int", "Сколько чанков вокруг игрока сервер отправляет клиенту.", (), 2, 32),
"white-list": ("Белый список", "bool", "Если включено, подключаться могут только игроки из whitelist."),
}


def _read_template() -> dict[str, str]:
    template = Path(__file__).resolve().parents[1] / "data" / "server.properties"
    values, _ = parse_properties(template.read_text(encoding="utf-8"))
    return values


def parse_properties(text: str) -> tuple[dict[str, str], list[str]]:
    values: dict[str, str] = {}
    comments: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "!")):
            comments.append(line)
            continue
        sep = next((i for i, char in enumerate(line) if char in "=:"), -1)
        key, value = (line.strip(), "") if sep < 0 else (line[:sep].strip(), line[sep + 1:].strip())
        if key:
            values[key] = value
    return values, comments


_DEFAULTS = _read_template()
SPECS = tuple(
    PropertySpec(key, info[0], info[1], info[2], _DEFAULTS.get(key, ""),
                 info[3] if len(info) > 3 else (),
                 info[4] if len(info) > 4 else None,
                 info[5] if len(info) > 5 else None)
    for key, info in _INFO.items()
)
SPEC_BY_KEY = {spec.key: spec for spec in SPECS}


def serialize_properties(values: dict[str, str]) -> str:
    lines = [f"{spec.key}={values[spec.key]}" for spec in SPECS if spec.key in values]
    lines.extend(f"{key}={values[key]}" for key in sorted(set(values) - set(SPEC_BY_KEY)))
    return "# Managed by IlandyMC — Minecraft server properties\n" + "\n".join(lines) + "\n"


def serialize_detected_properties(values: dict[str, str], supported_keys: list[str]) -> str:
    """Serialize only keys emitted by the target server, retaining native order."""
    ordered = list(dict.fromkeys(supported_keys))
    ordered.extend(key for key in values if key not in set(ordered))
    return "# Generated by the installed Minecraft server; managed by IlandyMC\n" + "\n".join(
        f"{key}={values[key]}" for key in ordered if key in values
    ) + "\n"
