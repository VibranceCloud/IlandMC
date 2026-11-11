const translations = {
  ru: {
    navFeatures:"Возможности",navHow:"Как работает",navCommands:"Команды",navFaq:"О проекте",
    eyebrow:"СТАБИЛЬНАЯ БАЗА · ВЕРСИЯ 1.0.0",heroTitle:"Твой Minecraft-сервер.<br><em>Под полным контролем.</em>",
    heroLead:"IlandyMC — менеджер Minecraft Java-серверов для Linux. Устанавливай ядра, управляй процессами, настраивай миры и создавай резервные копии из одного инструмента.",
    installNow:"Установить IlandyMC",viewSource:"Исходный код",verified:"Проверка целостности",
    installTitle:"Начни за минуту.",installText:"Одна команда — и установщик сделает остальное.",httpsLabel:"HTTPS INSTALLER",copy:"Копировать",
    installFoot:"Для Debian / Ubuntu и совместимых Linux-систем",installationGuide:"Инструкции и исходный код",
    featuresTitle:"Всё для управления<br><em>серверной инфраструктурой.</em>",
    featuresLead:"Не перегруженная панель, а понятный инструмент администратора — от первой установки до ежедневного обслуживания.",
    f1Title:"Установка серверов",f1Text:"Vanilla, Paper, Purpur и Fabric. Выбор версии Minecraft, Java, памяти и порта. Безопасная установка во временную директорию.",
    f2Title:"Автосоздание мира",f2Text:"Сервер сам создаёт мир и server.properties. IlandyMC определяет доступные настройки по фактической версии.",f2Foot:"Только поддерживаемые параметры",
    f3Title:"Редактор настроек",f3Text:"Логические, числовые и текстовые значения. Описания параметров, маскировка секретов и сохранение неизвестных ключей.",
    f4Title:"CLI и TUI",f4Text:"Управляй серверами командами или через интерактивный интерфейс прямо в терминале. Без отдельного графического приложения.",
    f5Title:"Процессы и systemd",f5Text:"Start, Stop, Restart, Status и логи. Использование systemd, если сервис установлен, или встроенного менеджера процессов.",
    f6Title:"Резервные копии",f6Text:"Архивы с SHA-256, проверка целостности и безопасное восстановление без перезаписи существующего сервера.",f6Foot:"Защита от опасных путей в архиве",
    f7Title:"Безопасность",f7Text:"Проверки PID, HTTPS, права 0600 для RCON-секретов, ограничения systemd и безопасная работа с архивами.",
    f8Title:"Обновления и диагностика",f8Text:"Проверка релизов IlandyMC, контроль SHA-256 пакета и диагностика ОС, CPU, RAM, диска и systemd.",
    workflowTitle:"Сначала проверка.<br><em>Потом — установка.</em>",workflowText:"IlandyMC не предполагает, какие настройки должны быть у сервера. Он запускает выбранное ядро, ждёт создания конфигурации и показывает только реально существующие параметры.",
    readSource:"Изучить проект",s1Title:"Выбери ядро и версию",s1Text:"Задай Java, объём памяти и игровой порт.",
    s2Title:"Создание в изоляции",s2Text:"Загрузка и первый запуск проходят во временной директории.",
    s3Title:"Обнаружение настроек",s3Text:"Менеджер анализирует server.properties и каталог параметров.",
    s4Title:"Готовый сервер",s4Text:"После корректной остановки установка переносится в рабочую папку.",
    commandsTitle:"Терминал — твоя панель.",commandsLead:"Все основные операции доступны через команду ilandy. TUI запускается короткой командой ily.",
    cmdInstall:"Установка",cmdStatus:"Состояние",cmdLogs:"Логи",cmdBackup:"Резервная копия",cmdDoctor:"Диагностика",cmdUpdate:"Обновление",
    codeComment:"Установить сервер Paper",codeComment2:"Проверить состояние сервера",codeComment3:"Создать резервную копию",
    securityTitle:"Безопасность — не опция.",securityText:"Не открывай RCON и управляющие порты в публичный интернет. online-mode=false отключает штатную проверку аккаунтов Minecraft: для такого сценария нужен корректно настроенный прокси с авторизацией, например Velocity.",
    detailsTitle:"Честно о возможностях.",detailsLead:"IlandyMC 1.0.0 — стабильная функциональная база. Некоторые функции пока не входят в релиз.",
    includedTitle:"Входит в 1.0.0",notIncludedTitle:"Пока не реализовано",
    inc1:"Установка Vanilla, Paper, Purpur, Fabric",inc2:"Управление процессами и systemd",inc3:"Редактор server.properties",inc4:"Резервное копирование и восстановление",inc5:"CLI, TUI, диагностика и обновление",inc6:"Русский и английский языки",
    not1:"Forge и NeoForge",not2:"Веб-панель и многосерверная панель",not3:"Автоустановка плагинов и модов",not4:"Планировщик и очистка старых бэкапов",not5:"Обновление Minecraft JAR и rollback",not6:"Автоматическое управление firewall",
    reqTitle:"Минимальная среда",ctaTitle:"Меньше рутины.<br><em>Больше контроля.</em>",ctaText:"Управляй Minecraft-серверами так, как удобно тебе — из терминала, быстро и предсказуемо."
  },
  en: {
    navFeatures:"Features",navHow:"How it works",navCommands:"Commands",navFaq:"About",
    eyebrow:"STABLE FOUNDATION · VERSION 1.0.0",heroTitle:"Your Minecraft server.<br><em>Fully under control.</em>",
    heroLead:"IlandyMC is a Minecraft Java server manager for Linux. Install server software, manage processes, configure worlds and create backups — all from one tool.",
    installNow:"Install IlandyMC",viewSource:"Source code",verified:"Integrity verification",
    installTitle:"Get started in a minute.",installText:"One command. The installer handles the rest.",httpsLabel:"HTTPS INSTALLER",copy:"Copy",
    installFoot:"For Debian / Ubuntu and compatible Linux systems",installationGuide:"Instructions & source code",
    featuresTitle:"Everything to manage<br><em>your server infrastructure.</em>",
    featuresLead:"Not an overloaded dashboard, but a focused admin tool — from the first installation to everyday maintenance.",
    f1Title:"Server installation",f1Text:"Vanilla, Paper, Purpur and Fabric. Choose Minecraft version, Java runtime, memory and port. Installs safely in a temporary directory.",
    f2Title:"Automatic world setup",f2Text:"The server creates its own world and server.properties. IlandyMC detects available settings from the actual server version.",f2Foot:"Only supported settings",
    f3Title:"Configuration editor",f3Text:"Boolean, numeric and text values. Setting descriptions, secret masking and preservation of unknown keys.",
    f4Title:"CLI and TUI",f4Text:"Manage servers with commands or an interactive interface right in your terminal. No separate desktop application.",
    f5Title:"Processes and systemd",f5Text:"Start, Stop, Restart, Status and logs. Uses systemd when a service exists, otherwise its built-in process manager.",
    f6Title:"Backups",f6Text:"SHA-256 archive checksums, integrity verification and safe restore without overwriting an existing server.",f6Foot:"Protection against unsafe archive paths",
    f7Title:"Security",f7Text:"PID verification, HTTPS, 0600 permissions for RCON secrets, systemd hardening and safe archive handling.",
    f8Title:"Updates and diagnostics",f8Text:"IlandyMC release checks, package SHA-256 verification and diagnostics for OS, CPU, RAM, disk and systemd.",
    workflowTitle:"Verify first.<br><em>Install second.</em>",workflowText:"IlandyMC does not assume which settings a server supports. It launches the selected server software, waits for its configuration and exposes only parameters that actually exist.",
    readSource:"Explore the project",s1Title:"Choose software and version",s1Text:"Set Java, memory allocation and game port.",
    s2Title:"Isolated setup",s2Text:"Download and first launch happen in a temporary directory.",
    s3Title:"Discover settings",s3Text:"The manager reads server.properties and compares it with the settings catalogue.",
    s4Title:"Server is ready",s4Text:"After a clean shutdown, the installation moves to its permanent directory.",
    commandsTitle:"Your terminal is the dashboard.",commandsLead:"Core operations are available through ilandy. Launch the TUI with the shorter ily command.",
    cmdInstall:"Install",cmdStatus:"Status",cmdLogs:"Logs",cmdBackup:"Backup",cmdDoctor:"Diagnostics",cmdUpdate:"Update",
    codeComment:"Install a Paper server",codeComment2:"Check server status",codeComment3:"Create a backup",
    securityTitle:"Security is not optional.",securityText:"Do not expose RCON or management ports to the public internet. online-mode=false disables Minecraft's built-in account authentication. If you use it, put a correctly configured authenticated proxy such as Velocity in front of the backend.",
    detailsTitle:"Clear about what is included.",detailsLead:"IlandyMC 1.0.0 is a stable functional foundation. Some features are not part of this release yet.",
    includedTitle:"Included in 1.0.0",notIncludedTitle:"Not implemented yet",
    inc1:"Vanilla, Paper, Purpur and Fabric installation",inc2:"Process and systemd management",inc3:"server.properties editor",inc4:"Backup and restore",inc5:"CLI, TUI, diagnostics and self-update",inc6:"Russian and English localization",
    not1:"Forge and NeoForge",not2:"Web panel or multi-server web dashboard",not3:"Automated plugin and mod installation",not4:"Backup scheduler and old-backup cleanup",not5:"Minecraft JAR updates and rollback",not6:"Automatic firewall management",
    reqTitle:"Requirements",ctaTitle:"Less busywork.<br><em>More control.</em>",ctaText:"Manage Minecraft servers your way — from the terminal, with speed and predictability."
  }
};

const langToggle = document.getElementById("langToggle");
const copyButton = document.getElementById("copyInstall");
const feedback = document.getElementById("copyFeedback");
let currentLang = (navigator.language || "en").toLowerCase().startsWith("ru") ? "ru" : "en";

function setLanguage(lang) {
  currentLang = lang;
  document.documentElement.lang = lang;
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    const key = node.dataset.i18n;
    if (translations[lang][key]) node.innerHTML = translations[lang][key];
  });
  langToggle.textContent = lang === "ru" ? "EN" : "RU";
  langToggle.setAttribute("aria-label", lang === "ru" ? "Switch to English" : "Переключить на русский");
  document.title = lang === "ru" ? "IlandyMC — менеджер Minecraft-серверов" : "IlandyMC — Minecraft Server Manager";
}
langToggle.addEventListener("click", () => setLanguage(currentLang === "ru" ? "en" : "ru"));

copyButton.addEventListener("click", async () => {
  const command = document.getElementById("installCommand").textContent.trim();
  try {
    await navigator.clipboard.writeText(command);
    feedback.textContent = currentLang === "ru" ? "Команда скопирована в буфер обмена" : "Command copied to clipboard";
  } catch {
    const range = document.createRange();
    range.selectNodeContents(document.getElementById("installCommand"));
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
    feedback.textContent = currentLang === "ru" ? "Выдели команду и скопируй вручную" : "Select the command and copy it manually";
  }
  feedback.classList.add("show");
  copyButton.querySelector("span").textContent = currentLang === "ru" ? "Готово" : "Copied";
  window.setTimeout(() => {
    feedback.classList.remove("show");
    copyButton.querySelector("span").textContent = translations[currentLang].copy;
  }, 2200);
});

setLanguage(currentLang);
