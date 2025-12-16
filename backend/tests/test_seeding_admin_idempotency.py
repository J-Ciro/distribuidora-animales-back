from helpers import admin_count


def test_no_duplicate_admin_on_restart():
    # Assumes backend has been restarted via script before running tests
    assert admin_count() == 1
