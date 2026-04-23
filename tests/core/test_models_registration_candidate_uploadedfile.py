from datetime import timedelta

import pytest
from django.utils import timezone

from core.models import Candidate, Registration, UploadedFile
from tests.factories import (
    candidate_factory,
    make_pdf,
    make_png,
    program_factory,
    registration_factory,
    user_factory,
)


def test_registration_copy_documents_to_candidate_only_if_missing(db):
    user = user_factory(username="u1")
    program = program_factory()
    tor = make_pdf("tor.pdf", b"tor")
    reg = registration_factory(user=user, program=program, tor=tor)

    cand = candidate_factory(created_by=user, program=program, tor=make_pdf("existing.pdf", b"existing"))
    reg.copy_documents_to_candidate(cand)
    cand.refresh_from_db()
    # candidate already had tor, should remain unchanged
    assert cand.tor.name.endswith("existing.pdf")


def test_candidate_validate_application_missing_docs_sets_deadline_once(db):
    user = user_factory(username="u1")
    program = program_factory(requires_license=False)
    cand = candidate_factory(created_by=user, program=program, status=Candidate.DRAFT)

    is_full, missing = cand.validate_application(deadline_days=3)
    cand.refresh_from_db()

    assert is_full is False
    assert cand.status == Candidate.MISSING_DOCS
    assert cand.document_deadline is not None
    first_deadline = cand.document_deadline

    # run again: should not move the deadline forward if already set
    is_full2, _ = cand.validate_application(deadline_days=7)
    cand.refresh_from_db()
    assert is_full2 is False
    assert cand.document_deadline == first_deadline


def test_candidate_validate_application_docs_complete_fields_missing_validated(db):
    user = user_factory(username="u1")
    program = program_factory(requires_license=False)

    # Provide required docs, but omit some required fields (e.g. phone_number/address/etc.)
    cand = candidate_factory(
        created_by=user,
        program=program,
        passport_scan=make_pdf("passport.pdf", b"p"),
        tor=make_pdf("tor.pdf", b"t"),
        diploma=make_pdf("diploma.pdf", b"d"),
        good_moral=make_pdf("moral.pdf", b"m"),
        nbi_clearance=make_pdf("nbi.pdf", b"n"),
        profile_image=make_png("img.png"),
        status=Candidate.DRAFT,
    )

    is_full, missing = cand.validate_application()
    cand.refresh_from_db()
    assert is_full is False
    assert cand.status == Candidate.VALIDATED
    assert "Required fields missing:" in (cand.missing_documents_note or "")
    assert cand.document_deadline is None
    assert len(missing) > 0


def test_candidate_validate_application_fully_complete_approved(db):
    user = user_factory(username="u1")
    program = program_factory(requires_license=False)

    cand = candidate_factory(
        created_by=user,
        program=program,
        passport_scan=make_pdf("passport.pdf", b"p"),
        tor=make_pdf("tor.pdf", b"t"),
        diploma=make_pdf("diploma.pdf", b"d"),
        good_moral=make_pdf("moral.pdf", b"m"),
        nbi_clearance=make_pdf("nbi.pdf", b"n"),
        profile_image=make_png("img.png"),
        phone_number="09123456789",
        address="Home",
        health_condition="Excellent",
        shirt_size="M",
        shoes_size="42",
        university="Not Specified",
        field_of_study="Agronomy",
        graduation_year=2015,
        place_of_issue="Manila",
        status=Candidate.DRAFT,
    )

    is_full, missing = cand.validate_application()
    cand.refresh_from_db()
    assert is_full is True
    assert missing == []
    assert cand.status == Candidate.APPROVED
    assert cand.document_deadline is None
    assert cand.missing_documents_note == ""


def test_candidate_license_required_adds_missing_doc(db):
    user = user_factory(username="u1")
    program = program_factory(requires_license=True)
    cand = candidate_factory(
        created_by=user,
        program=program,
        passport_scan=make_pdf("passport.pdf", b"p"),
        tor=make_pdf("tor.pdf", b"t"),
        diploma=make_pdf("diploma.pdf", b"d"),
        good_moral=make_pdf("moral.pdf", b"m"),
        nbi_clearance=make_pdf("nbi.pdf", b"n"),
        profile_image=make_png("img.png"),
        status=Candidate.DRAFT,
    )

    is_full, missing = cand.validate_application(deadline_days=1)
    cand.refresh_from_db()
    assert is_full is False
    assert cand.status == Candidate.MISSING_DOCS
    assert any("Driver's License" in m for m in missing)


def test_candidate_deadline_helpers(db):
    user = user_factory(username="u1")
    program = program_factory()
    cand = candidate_factory(created_by=user, program=program)

    cand.document_deadline = timezone.now() - timedelta(days=1)
    cand.save(update_fields=["document_deadline"])
    assert cand.is_deadline_passed() is True
    assert cand.days_until_deadline() == 0

    cand.document_deadline = timezone.now() + timedelta(days=3)
    cand.save(update_fields=["document_deadline"])
    assert cand.is_deadline_passed() is False
    assert cand.days_until_deadline() >= 2


def test_uploadedfile_calculate_file_hash_resets_pointer(db):
    user = user_factory(username="u1")
    file_obj = make_pdf("a.pdf", b"abc123")
    # SimpleUploadedFile exposes chunks(); seek(0) works too.
    h1 = UploadedFile.calculate_file_hash(file_obj)
    # reading should still yield content (pointer reset)
    assert file_obj.read()  # non-empty
    file_obj.seek(0)
    h2 = UploadedFile.calculate_file_hash(file_obj)
    assert h1 == h2

