from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from core.models import AgricultureProgram, Candidate, Registration, University


def make_pdf(name: str = "doc.pdf", content: bytes = b"%PDF-1.4 test") -> SimpleUploadedFile:
    return SimpleUploadedFile(name, content, content_type="application/pdf")


def make_png(name: str = "img.png", content: bytes = b"\x89PNG\r\n\x1a\n") -> SimpleUploadedFile:
    return SimpleUploadedFile(name, content, content_type="image/png")


def user_factory(
    *,
    username: str = "user",
    password: str = "TestPass123!",
    is_staff: bool = False,
    is_superuser: bool = False,
    email: str = "user@example.com",
) -> User:
    return User.objects.create_user(
        username=username,
        password=password,
        is_staff=is_staff,
        is_superuser=is_superuser,
        email=email,
    )


def university_factory(
    *,
    code: str = "DEFAULT",
    name: str = "Not Specified",
    country: str = "Not Specified",
) -> University:
    uni, _ = University.objects.get_or_create(
        code=code,
        defaults={"name": name, "country": country},
    )
    return uni


def program_factory(
    *,
    title: str = "Test Program",
    description: str = "Test Description",
    country: str = "Israel",
    location: str = "Israel",
    start_date: Optional[date] = None,
    capacity: int = 10,
    required_gender: str = "Any",
    requires_license: bool = False,
) -> AgricultureProgram:
    if start_date is None:
        start_date = date.today() + timedelta(days=30)
    return AgricultureProgram.objects.create(
        title=title,
        description=description,
        country=country,
        location=location,
        start_date=start_date,
        capacity=capacity,
        required_gender=required_gender,
        requires_license=requires_license,
    )


def registration_factory(
    *,
    user: User,
    program: AgricultureProgram,
    status: str = Registration.PENDING,
    tor=None,
    nc2_tesda=None,
    diploma=None,
    good_moral=None,
    nbi_clearance=None,
) -> Registration:
    return Registration.objects.create(
        user=user,
        program=program,
        status=status,
        tor=tor,
        nc2_tesda=nc2_tesda,
        diploma=diploma,
        good_moral=good_moral,
        nbi_clearance=nbi_clearance,
    )


def candidate_factory(
    *,
    created_by: User,
    program: AgricultureProgram | None = None,
    passport_number: str = "P123",
    first_name: str = "Test",
    last_name: str = "User",
    email: str = "test@example.com",
    date_of_birth: date = date(1995, 1, 1),
    country_of_birth: str = "Philippines",
    nationality: str = "Filipino",
    gender: str = "Male",
    passport_issue_date: Optional[date] = None,
    passport_expiry_date: Optional[date] = None,
    university: str = "Not Specified",
    specialization: str = "Agronomy",
    status: str = Candidate.DRAFT,
    **files,
) -> Candidate:
    if passport_issue_date is None:
        passport_issue_date = date.today()
    if passport_expiry_date is None:
        passport_expiry_date = date.today() + timedelta(days=3650)
    return Candidate.objects.create(
        passport_number=passport_number,
        first_name=first_name,
        last_name=last_name,
        email=email,
        date_of_birth=date_of_birth,
        country_of_birth=country_of_birth,
        nationality=nationality,
        gender=gender,
        passport_issue_date=passport_issue_date,
        passport_expiry_date=passport_expiry_date,
        university=university,
        specialization=specialization,
        status=status,
        program=program,
        created_by=created_by,
        **files,
    )

