import json
from importlib.resources import files

class LocalizationError(RuntimeError): pass

class Localization:
    def __init__(self, language: str, data: dict):
        self.language, self.data = language, data

    @classmethod
    def load(cls, language="en"):
        if language not in ("en", "ru"):
            raise LocalizationError(f"Unsupported language: {language}")
        path = files("ilandymc.localization").joinpath("locales", f"{language}.json")
        try:
            return cls(language, json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError) as exc:
            raise LocalizationError(str(exc)) from exc

    def t(self, key, **kwargs):
        value = self.data
        for part in key.split("."):
            if not isinstance(value, dict) or part not in value:
                raise LocalizationError(f"Missing translation {key!r} ({self.language})")
            value = value[part]
        if not isinstance(value, str):
            raise LocalizationError(f"Translation {key!r} is not text")
        return value.format(**kwargs)
