import os.path

import pytest

import scimma_aws_utils.auth

FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'fixtures',
)


def test_parse_uiuc(caplog):
    with open(os.path.join(FIXTURE_DIR, "uiuc_login_response.html")) as f:
        uiuc_login_response = f.read()
    with pytest.raises(ValueError):
        scimma_aws_utils.auth.parse_idp_login_response(uiuc_login_response)
    assert "It looks like your IDP uses Duo" in caplog.text
