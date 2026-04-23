import types

from core.utils.file_tracker import (
    check_file_already_uploaded,
    deactivate_file_record,
    get_uploaded_documents_display,
    register_model_files,
)

from core.models import UploadedFile
from tests.factories import make_pdf, program_factory, registration_factory, user_factory


def test_get_uploaded_documents_display_empty(db):
    user = user_factory(username="u1")
    assert get_uploaded_documents_display(user) == {}


def test_check_file_already_uploaded_not_duplicate(monkeypatch, db):
    user = user_factory(username="u1")
    new_file = make_pdf("x.pdf", b"x")

    def fake_check_duplicate_upload(u, document_type, file_obj):
        return False, None, None

    monkeypatch.setattr(UploadedFile, "check_duplicate_upload", classmethod(lambda cls, u, document_type, file_obj: fake_check_duplicate_upload(u, document_type, file_obj)))
    is_dup, existing_type, msg = check_file_already_uploaded(user, "tor", new_file)
    assert is_dup is False
    assert existing_type is None
    assert msg is None


def test_check_file_already_uploaded_duplicate(monkeypatch, db):
    user = user_factory(username="u1")
    new_file = make_pdf("x.pdf", b"x")

    class Existing:
        def get_document_type_display(self):
            return "NBI Clearance"

    def fake_check_duplicate_upload(u, document_type, file_obj):
        return True, Existing(), "dup"

    monkeypatch.setattr(UploadedFile, "check_duplicate_upload", classmethod(lambda cls, u, document_type, file_obj: fake_check_duplicate_upload(u, document_type, file_obj)))
    is_dup, existing_type, msg = check_file_already_uploaded(user, "tor", new_file)
    assert is_dup is True
    assert existing_type == "NBI Clearance"
    assert msg == "dup"


def test_deactivate_file_record_updates_queryset(monkeypatch, db):
    user = user_factory(username="u1")

    calls = {"updated": False}

    class FakeQS:
        def filter(self, **kwargs):
            return self

        def update(self, **kwargs):
            calls["updated"] = True
            assert kwargs == {"is_active": False}
            return 1

    monkeypatch.setattr(UploadedFile, "objects", FakeQS())
    deactivate_file_record(user, "tor")
    assert calls["updated"] is True


def test_register_model_files_registers_present_file_fields(monkeypatch, db):
    user = user_factory(username="u1")
    program = program_factory(title="P1")
    tor = make_pdf("tor.pdf", b"tor bytes")
    reg = registration_factory(user=user, program=program, tor=tor)

    called = {"n": 0}

    def fake_register_upload(*, user, document_type, file_obj, model_name, model_id):
        called["n"] += 1
        assert user is not None
        assert document_type == "tor"
        assert model_name == "Registration"
        assert model_id == reg.pk
        assert hasattr(file_obj, "read") or hasattr(file_obj, "chunks")

    monkeypatch.setattr(UploadedFile, "register_upload", classmethod(lambda cls, **kwargs: fake_register_upload(**kwargs)))

    register_model_files(reg, user=user, model_name="Registration")
    assert called["n"] == 1

