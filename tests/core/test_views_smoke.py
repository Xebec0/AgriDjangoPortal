from django.urls import reverse

from tests.factories import program_factory


def test_health_check_ok(client, db):
    resp = client.get(reverse("health_check"))
    assert resp.status_code == 200


def test_program_list_ok(client, db):
    program_factory(title="Program A")
    resp = client.get(reverse("program_list"))
    assert resp.status_code == 200
    assert b"Program A" in resp.content


def test_login_required_profile_redirects(client, db):
    resp = client.get(reverse("profile"))
    assert resp.status_code in (301, 302)

