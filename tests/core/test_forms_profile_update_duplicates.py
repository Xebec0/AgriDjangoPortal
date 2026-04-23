import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from core.forms import ProfileUpdateForm
from core.models import UploadedFile
from tests.factories import make_pdf, user_factory


def test_profile_update_form_rejects_duplicate_file(monkeypatch, db):
    user = user_factory(username="u1")
    profile = user.profile

    def fake_check_duplicate_upload(u, document_type, file_obj):
        return True, object(), "This file has already been uploaded"

    monkeypatch.setattr(
        UploadedFile,
        "check_duplicate_upload",
        classmethod(lambda cls, u, document_type, file_obj: fake_check_duplicate_upload(u, document_type, file_obj)),
    )

    data = {}
    files = {"tor": make_pdf("tor.pdf", b"same")}
    form = ProfileUpdateForm(data=data, files=files, instance=profile)

    assert form.is_valid() is False
    assert "tor" in form.errors

