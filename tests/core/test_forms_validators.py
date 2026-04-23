from datetime import date, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from core.forms import (
    ComprehensiveRegisterForm,
    validate_file_extension,
    validate_file_size,
)
from tests.factories import make_pdf


def test_validate_file_extension_rejects(db):
    f = make_pdf("x.exe", b"x")
    with pytest.raises(ValidationError):
        validate_file_extension(f, [".pdf"])


def test_validate_file_size_rejects_large(monkeypatch, db):
    f = make_pdf("x.pdf", b"x")
    # Simulate > 5MB without allocating big bytes
    monkeypatch.setattr(f, "size", 6 * 1024 * 1024)
    with pytest.raises(ValidationError):
        validate_file_size(f)


def test_comprehensive_register_form_email_mismatch(db):
    form = ComprehensiveRegisterForm(
        data={
            "username": "u1",
            "first_name": "A",
            "last_name": "B",
            "email": "a@example.com",
            "confirm_email": "b@example.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
            "date_of_birth": "1990-01-01",
            "gender": "Male",
            "nationality": "Filipino",
            "passport_number": "P1",
            "confirm_passport_number": "P1",
            "passport_issue_date": "2020-01-01",
            "passport_expiry_date": "2030-01-01",
            "highest_education_level": "bachelor",
            "graduation_year": "2010",
            "field_of_study": "Agronomy",
        }
    )
    assert form.is_valid() is False
    assert any("Email addresses do not match" in e for e in form.non_field_errors())


def test_comprehensive_register_form_passport_expiry_before_issue(db):
    form = ComprehensiveRegisterForm(
        data={
            "username": "u2",
            "first_name": "A",
            "last_name": "B",
            "email": "a@example.com",
            "confirm_email": "a@example.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
            "date_of_birth": "1990-01-01",
            "gender": "Male",
            "nationality": "Filipino",
            "passport_number": "P1",
            "confirm_passport_number": "P1",
            "passport_issue_date": "2030-01-01",
            "passport_expiry_date": "2020-01-01",
            "highest_education_level": "bachelor",
            "graduation_year": "2010",
            "field_of_study": "Agronomy",
        }
    )
    assert form.is_valid() is False
    assert any("Passport expiry date must be after issue date" in e for e in form.non_field_errors())


def test_comprehensive_register_form_dob_in_future(db):
    future = (timezone.now().date() + timedelta(days=1)).isoformat()
    form = ComprehensiveRegisterForm(
        data={
            "username": "u3",
            "first_name": "A",
            "last_name": "B",
            "email": "a@example.com",
            "confirm_email": "a@example.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
            "date_of_birth": future,
            "gender": "Male",
            "nationality": "Filipino",
            "passport_number": "P1",
            "confirm_passport_number": "P1",
            "passport_issue_date": "2020-01-01",
            "passport_expiry_date": "2030-01-01",
            "highest_education_level": "bachelor",
            "graduation_year": "2010",
            "field_of_study": "Agronomy",
        }
    )
    assert form.is_valid() is False
    assert any("Date of birth must be in the past" in e for e in form.non_field_errors())

