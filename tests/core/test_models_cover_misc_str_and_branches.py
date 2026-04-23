from datetime import date, timedelta

from django.utils import timezone

from core.models import ActivityLog, Notification, Registration, University, UploadedFile
from tests.factories import (
    candidate_factory,
    make_pdf,
    program_factory,
    registration_factory,
    university_factory,
    user_factory,
)


def test_model_strs_and_simple_branches(db):
    user = user_factory(username="u1")
    uni = university_factory(code="U1", name="Uni One", country="X")
    assert str(uni) == "Uni One"

    program = program_factory(title="P1")
    assert str(program) == "P1"

    reg = registration_factory(user=user, program=program, status=Registration.PENDING)
    assert "u1 - P1" in str(reg)

    cand = candidate_factory(created_by=user, program=program, passport_number="PASS", first_name="A", last_name="B")
    assert "A B (PASS)" in str(cand)

    notif = Notification.add_notification(user=user, message="Hello world", notification_type=Notification.INFO)
    assert user.username in str(notif)


def test_candidate_deadline_helpers_none(db):
    user = user_factory(username="u1")
    program = program_factory()
    cand = candidate_factory(created_by=user, program=program)
    cand.document_deadline = None
    cand.save(update_fields=["document_deadline"])
    assert cand.is_deadline_passed() is False
    assert cand.days_until_deadline() is None


def test_registration_copy_documents_to_candidate_copies_when_missing(db):
    user = user_factory(username="u1")
    program = program_factory()
    tor = make_pdf("tor.pdf", b"tor")
    reg = registration_factory(user=user, program=program, tor=tor)

    cand = candidate_factory(created_by=user, program=program)
    assert not cand.tor
    reg.copy_documents_to_candidate(cand)
    cand.refresh_from_db()
    assert bool(cand.tor) is True


def test_program_get_image_url_uses_image_url_attr(db):
    program = program_factory()

    class Img:
        url = "/media/x.png"

    program.image = Img()
    assert program.get_image_url() == "/media/x.png"


def test_activitylog_model_from_label_invalid_and_rollback_none(db):
    assert ActivityLog.model_from_label("not.a.model") is None

    log = ActivityLog.objects.create(
        user=None,
        action_type=ActivityLog.ACTION_SYSTEM,
        model_name="core.Candidate",
        object_id=None,
        before_data=None,
        after_data=None,
    )
    assert log.rollback() is None


def test_uploadedfile_str(db):
    user = user_factory(username="u1")
    program = program_factory()
    cand = candidate_factory(created_by=user, program=program)
    rec = UploadedFile.register_upload(
        user=user,
        document_type="tor",
        file_obj=make_pdf("tor.pdf", b"t"),
        model_name="Candidate",
        model_id=cand.id,
    )
    s = str(rec)
    assert user.username in s
    assert "TOR" in s or "tor" in s

