from datetime import date, timedelta

import pytest
from django.utils import timezone

from core.models import AgricultureProgram
from tests.factories import program_factory, user_factory


def test_profile_age_none_when_missing_dob(db):
    user = user_factory(username="u1")
    user.profile.date_of_birth = None
    user.profile.save(update_fields=["date_of_birth"])
    assert user.profile.age is None


def test_profile_age_boundary(monkeypatch, db):
    user = user_factory(username="u1")
    # pretend today is 2026-04-10
    fake_today = date(2026, 4, 10)

    class FakeNow:
        @staticmethod
        def date():
            return fake_today

    monkeypatch.setattr(timezone, "now", lambda: FakeNow())

    user.profile.date_of_birth = date(2000, 4, 10)
    user.profile.save(update_fields=["date_of_birth"])
    assert user.profile.age == 26

    user.profile.date_of_birth = date(2000, 4, 11)
    user.profile.save(update_fields=["date_of_birth"])
    assert user.profile.age == 25


def test_program_is_registration_open_deadline(monkeypatch, db):
    prog = program_factory()
    prog.registration_deadline = timezone.now() + timedelta(days=1)
    prog.save(update_fields=["registration_deadline"])
    assert prog.is_registration_open() is True

    prog.registration_deadline = timezone.now() - timedelta(seconds=1)
    prog.save(update_fields=["registration_deadline"])
    assert prog.is_registration_open() is False


def test_program_is_registration_open_no_deadline_uses_start_date(db):
    prog = program_factory(start_date=date.today() + timedelta(days=1))
    prog.registration_deadline = None
    prog.save(update_fields=["registration_deadline"])
    assert prog.is_registration_open() is True

    prog.start_date = date.today() - timedelta(days=1)
    prog.save(update_fields=["start_date"])
    assert prog.is_registration_open() is False


def test_program_get_image_url_fallbacks(monkeypatch, db, settings):
    import os

    prog = program_factory(location="Israel")
    prog.image = None

    # placeholder exists
    monkeypatch.setattr(os.path, "exists", lambda p: True)
    url = prog.get_image_url()
    assert url.startswith("/static/images/placeholders/")

    # placeholder missing
    monkeypatch.setattr(os.path, "exists", lambda p: False)
    url = prog.get_image_url()
    assert url.startswith("https://placehold.co/")

