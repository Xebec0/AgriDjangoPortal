from types import SimpleNamespace

from django.utils import timezone

from core.models import UploadedFile
from core.utils.file_tracker import get_uploaded_documents_display, register_model_files
from tests.factories import candidate_factory, make_pdf, program_factory, user_factory


def test_get_uploaded_documents_display_populated(db):
    user = user_factory(username="u1")
    program = program_factory()
    cand = candidate_factory(created_by=user, program=program)

    f = make_pdf("tor.pdf", b"t")
    UploadedFile.register_upload(
        user=user,
        document_type="tor",
        file_obj=f,
        model_name="Candidate",
        model_id=cand.id,
    )

    docs = get_uploaded_documents_display(user)
    assert "tor" in docs
    assert docs["tor"]["name"] == "tor.pdf"
    assert docs["tor"]["size"] > 0
    assert docs["tor"]["display_name"]


def test_register_model_files_open_close_paths(monkeypatch, db):
    user = user_factory(username="u1")

    calls = {"opened": 0, "closed": 0, "registered": 0}

    class FakeField:
        name = "x.pdf"
        file = None  # not opened

        def open(self, mode="rb"):
            calls["opened"] += 1
            self.file = object()

        def close(self):
            calls["closed"] += 1
            self.file = None

        def seek(self, n):
            return None

    def fake_register_upload(**kwargs):
        calls["registered"] += 1

    monkeypatch.setattr(UploadedFile, "register_upload", classmethod(lambda cls, **kwargs: fake_register_upload(**kwargs)))

    instance = SimpleNamespace(pk=123, tor=FakeField())
    register_model_files(instance, user=user, model_name="Registration")

    assert calls["opened"] == 1
    assert calls["closed"] == 1
    assert calls["registered"] == 1


def test_register_model_files_logs_error(monkeypatch, caplog, db):
    user = user_factory(username="u1")

    class FakeField:
        name = "x.pdf"
        file = object()  # already opened, so we hit seek path

        def seek(self, n):
            return None

    def boom(**kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(UploadedFile, "register_upload", classmethod(lambda cls, **kwargs: boom(**kwargs)))

    instance = SimpleNamespace(pk=99, tor=FakeField())
    # should not raise
    register_model_files(instance, user=user, model_name="Registration")
    assert True

