from core.utils import admin_dashboard
from core.models import Candidate, Notification, Registration
from tests.factories import candidate_factory, program_factory, registration_factory, user_factory


def test_admin_dashboard_counts(db):
    # one staff (excluded), two normal users
    staff = user_factory(username="staff", is_staff=True, is_superuser=True)
    u1 = user_factory(username="u1")
    u2 = user_factory(username="u2")

    program = program_factory()

    registration_factory(user=u1, program=program, status=Registration.PENDING)
    registration_factory(user=u2, program=program, status=Registration.APPROVED)

    candidate_factory(created_by=u1, program=program, status=Candidate.DRAFT)
    candidate_factory(created_by=u1, program=program, status=Candidate.VALIDATED)
    candidate_factory(created_by=u2, program=program, status=Candidate.APPROVED)

    ctx = {}
    out = admin_dashboard(request=None, context=ctx)
    assert out["total_users"] == 2
    assert out["total_programs"] >= 1
    assert out["total_registrations"] == 2
    assert out["total_candidates"] == 3
    assert out["pending_registrations"] == 1
    assert out["approved_registrations"] == 1
    assert out["draft_candidates"] == 1
    assert out["validated_candidates"] == 1
    assert out["approved_candidates"] == 1

