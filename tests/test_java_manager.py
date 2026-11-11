import pytest

from ilandymc.core.java_manager import required_java_major


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        ("1.16.5", 8),
        ("1.17.1", 16),
        ("1.18.2", 17),
        ("1.20.4", 17),
        ("1.20.5", 21),
        ("1.21.11", 21),
        ("26.1", 25),
        ("26.1.1", 25),
        ("26.2", 25),
        ("26.3", 25),
        ("26.1-rc-1", 25),
    ],
)
def test_required_java_major(version, expected):
    assert required_java_major(version) == expected


@pytest.mark.parametrize("version", ["", "latest", "25w14a", "2.0", "100.1", "1.x"])
def test_rejects_unknown_version_formats(version):
    with pytest.raises(ValueError):
        required_java_major(version)
