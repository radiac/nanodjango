import pytest


@pytest.fixture(autouse=True)
def _dj_autoclear_mailbox():
    """
    See:
        - https://github.com/pytest-dev/pytest-django/pull/1033
        - https://github.com/pytest-dev/pytest-django/issues/993
    """
    pass
