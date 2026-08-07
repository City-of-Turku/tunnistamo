import pytest
import responses


@pytest.fixture
def httpretty():
    with responses.RequestsMock() as rsps:
        yield rsps
