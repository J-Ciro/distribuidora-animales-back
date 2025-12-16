from helpers import backend_health_ok

ERROR_HINTS = (
    "error",
    "missing",
    "constraint",
    "violat",
)


def test_seeding_logs_error_but_backend_stays_up(read_backend_logs):
    logs = read_backend_logs()
    assert logs
    assert any(hint.lower() in logs.lower() for hint in ERROR_HINTS)
    assert backend_health_ok() is True
