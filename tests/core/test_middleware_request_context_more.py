from django.http import HttpResponse
from django.test import RequestFactory

from core.middleware import RequestContextMiddleware, get_request_ip, get_request_session_key, get_request_user
from tests.factories import user_factory


def test_request_context_middleware_client_ip_parses_forwarded_for(db):
    rf = RequestFactory()
    user = user_factory(username="u1")
    request = rf.get("/", HTTP_X_FORWARDED_FOR="1.2.3.4, 5.6.7.8")
    request.user = user
    request.session = type("S", (), {"session_key": "abc"})()

    mw = RequestContextMiddleware(lambda r: HttpResponse("ok"))
    mw.process_request(request)

    assert get_request_user().username == "u1"
    assert get_request_ip() == "1.2.3.4"
    assert get_request_session_key() == "abc"

    resp = mw.process_response(request, HttpResponse("ok"))
    assert resp.status_code == 200
    assert get_request_user() is None
    assert get_request_ip() is None
    assert get_request_session_key() is None


def test_request_context_middleware_no_ip_headers(db):
    rf = RequestFactory()
    user = user_factory(username="u2")
    request = rf.get("/")
    request.META.pop("REMOTE_ADDR", None)
    request.user = user
    request.session = type("S", (), {"session_key": None})()

    mw = RequestContextMiddleware(lambda r: HttpResponse("ok"))
    mw.process_request(request)
    # RequestFactory sets REMOTE_ADDR by default.
    assert get_request_ip() is None


def test_request_context_middleware_process_response_without_process_request(db):
    rf = RequestFactory()
    request = rf.get("/")
    mw = RequestContextMiddleware(lambda r: HttpResponse("ok"))
    resp = mw.process_response(request, HttpResponse("ok"))
    assert resp.status_code == 200


