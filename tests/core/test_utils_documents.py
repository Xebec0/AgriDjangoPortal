from django.core.files.uploadedfile import SimpleUploadedFile

from core.utils import find_user_documents, get_available_documents, import_document_to_candidate

from tests.factories import (
    candidate_factory,
    make_pdf,
    program_factory,
    registration_factory,
    university_factory,
    user_factory,
)


def test_find_user_documents_empty(db):
    user = user_factory(username="u1")
    assert find_user_documents(user) == {}


def test_find_user_documents_picks_first_registration_per_doc_type(db):
    user = user_factory(username="u1")
    program = program_factory(title="P1")
    program2 = program_factory(title="P2")

    tor1 = make_pdf("tor1.pdf", b"tor one")
    tor2 = make_pdf("tor2.pdf", b"tor two")

    r1 = registration_factory(user=user, program=program, tor=tor1)
    registration_factory(user=user, program=program2, tor=tor2)

    docs = find_user_documents(user)
    assert docs["tor"]["registration_id"] == r1.id
    assert "Registration for" in docs["tor"]["source"]


def test_get_available_documents_marks_uploaded_and_available(db):
    user = user_factory(username="u1")
    program = program_factory(title="P1")

    # doc available via registration
    tor = make_pdf("tor.pdf", b"tor bytes")
    reg = registration_factory(user=user, program=program, tor=tor)

    # candidate already has a diploma uploaded
    diploma = make_pdf("diploma.pdf", b"diploma bytes")
    cand = candidate_factory(created_by=user, program=program, diploma=diploma)

    docs = get_available_documents(cand)

    assert docs["diploma"]["status"] == "uploaded"
    assert docs["tor"]["status"] == "available"
    assert docs["tor"]["registration_id"] == reg.id


def test_get_available_documents_no_created_by_only_uploaded_not_uploaded(db):
    # Candidate.created_by is NOT NULL in the DB, so exercise this branch using a
    # candidate-like object rather than forcing an invalid DB write.
    from types import SimpleNamespace
    from django.utils import timezone

    cand = SimpleNamespace(
        created_by=None,
        updated_at=timezone.now(),
        tor=None,
        nc2_tesda=None,
        diploma=None,
        good_moral=None,
        nbi_clearance=None,
        passport_scan=None,
    )

    docs = get_available_documents(cand)
    assert docs["tor"]["status"] in {"uploaded", "not_uploaded"}
    assert "registration_id" not in docs["tor"]


def test_import_document_to_candidate_success(db):
    user = user_factory(username="u1")
    program = program_factory(title="P1")

    tor = make_pdf("tor.pdf", b"tor bytes")
    reg = registration_factory(user=user, program=program, tor=tor)

    cand = candidate_factory(created_by=user, program=program)
    assert not cand.tor

    assert import_document_to_candidate(cand, "tor", reg.id) is True
    cand.refresh_from_db()
    assert bool(cand.tor) is True


def test_import_document_to_candidate_invalid_registration(db):
    user = user_factory(username="u1")
    program = program_factory(title="P1")
    cand = candidate_factory(created_by=user, program=program)
    assert import_document_to_candidate(cand, "tor", 999999) is False


def test_import_document_to_candidate_missing_document(db):
    user = user_factory(username="u1")
    program = program_factory(title="P1")
    reg = registration_factory(user=user, program=program)  # no tor
    cand = candidate_factory(created_by=user, program=program)

    assert import_document_to_candidate(cand, "tor", reg.id) is False

