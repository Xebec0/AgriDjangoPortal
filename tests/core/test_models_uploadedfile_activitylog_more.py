from datetime import date, timedelta

from django.utils import timezone

from core.models import ActivityLog, Candidate, UploadedFile
from tests.factories import candidate_factory, make_pdf, program_factory, user_factory


def test_uploadedfile_check_duplicate_upload_across_fields(db):
    user = user_factory(username="u1")
    program = program_factory()
    cand = candidate_factory(created_by=user, program=program)

    f = make_pdf("same.pdf", b"same-bytes")
    existing = UploadedFile.register_upload(
        user=user,
        document_type="nbi_clearance",
        file_obj=f,
        model_name="Candidate",
        model_id=cand.id,
    )

    f2 = make_pdf("same.pdf", b"same-bytes")
    is_dup, existing_upload, msg = UploadedFile.check_duplicate_upload(user, "tor", f2)
    assert is_dup is True
    assert existing_upload.id == existing.id
    assert "already been uploaded" in msg


def test_uploadedfile_check_duplicate_upload_same_field_allowed(db):
    user = user_factory(username="u1")
    program = program_factory()
    cand = candidate_factory(created_by=user, program=program)

    f = make_pdf("doc.pdf", b"bytes1")
    UploadedFile.register_upload(
        user=user,
        document_type="tor",
        file_obj=f,
        model_name="Candidate",
        model_id=cand.id,
    )

    f2 = make_pdf("doc.pdf", b"bytes1")
    is_dup, existing_upload, msg = UploadedFile.check_duplicate_upload(user, "tor", f2)
    assert is_dup is False
    assert msg is None


def test_uploadedfile_register_upload_deactivates_previous_hash(db):
    user = user_factory(username="u1")
    program = program_factory()
    cand = candidate_factory(created_by=user, program=program)

    f1 = make_pdf("a.pdf", b"a")
    r1 = UploadedFile.register_upload(
        user=user,
        document_type="tor",
        file_obj=f1,
        model_name="Candidate",
        model_id=cand.id,
    )
    assert r1.is_active is True

    f2 = make_pdf("b.pdf", b"b")
    r2 = UploadedFile.register_upload(
        user=user,
        document_type="tor",
        file_obj=f2,
        model_name="Candidate",
        model_id=cand.id,
    )
    r1.refresh_from_db()
    r2.refresh_from_db()
    assert r1.is_active is False
    assert r2.is_active is True


def test_uploadedfile_cleanup_orphaned_records_marks_inactive(monkeypatch, db, settings):
    user = user_factory(username="u1")
    program = program_factory()
    cand = candidate_factory(created_by=user, program=program)

    f = make_pdf("a.pdf", b"a")
    rec = UploadedFile.register_upload(
        user=user,
        document_type="tor",
        file_obj=f,
        model_name="Candidate",
        model_id=cand.id,
    )

    # Pretend the storage path doesn't exist
    monkeypatch.setattr("os.path.exists", lambda p: False)
    n = UploadedFile.cleanup_orphaned_records()
    rec.refresh_from_db()
    assert n >= 1
    assert rec.is_active is False


def test_activitylog_rollback_restores_before_data(db):
    user = user_factory(username="u1")
    program = program_factory()
    cand = candidate_factory(created_by=user, program=program, first_name="Old", last_name="Name")

    before = {"first_name": "Old", "last_name": "Name"}
    cand.first_name = "New"
    cand.last_name = "Person"
    cand.save(update_fields=["first_name", "last_name"])

    log = ActivityLog.objects.create(
        user=None,
        action_type=ActivityLog.ACTION_UPDATE,
        model_name="core.Candidate",
        object_id=str(cand.pk),
        before_data=before,
        after_data={"first_name": "New", "last_name": "Person"},
    )

    restored = log.rollback()
    cand.refresh_from_db()
    assert restored is not None
    assert cand.first_name == "Old"
    assert cand.last_name == "Name"

