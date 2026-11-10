"""Offline tests for multi-login account selection (authuser)."""

from types import SimpleNamespace

from gemini_webapi import GeminiClient
from gemini_webapi.constants import Endpoint
from gemini_webapi.utils.get_access_token import extract_email, init_url, served_authuser


def _response(url: str, text: str = "") -> SimpleNamespace:
    return SimpleNamespace(url=url, text=text)


def test_init_url():
    assert init_url() == Endpoint.INIT.value
    assert init_url(0) == "https://gemini.google.com/u/0/app"
    assert init_url(2) == "https://gemini.google.com/u/2/app"


def test_served_authuser():
    assert served_authuser(_response("https://gemini.google.com/u/1/app")) == 1
    assert served_authuser(_response("https://gemini.google.com/u/1/app?hl=en")) == 1
    # A missing index is redirected to the default account
    assert served_authuser(_response("https://gemini.google.com/u/0/app")) == 0
    assert served_authuser(_response("https://gemini.google.com/app")) == 0


def test_extract_email():
    assert extract_email(_response("", 'x,"oPEP7c":"someone@example.org",y')) == "someone@example.org"
    assert extract_email(_response("", '"oPEP7c":""')) is None
    assert extract_email(_response("", "guest page")) is None


def test_client_authuser_param():
    assert GeminiClient("psid", authuser=1).authuser == 1
    assert GeminiClient("psid", authuser="3").authuser == 3
    assert GeminiClient("psid").authuser is None
