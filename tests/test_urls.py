from django.urls import resolve, reverse


def test_reverse_core_routes():
    assert reverse("index") == "/"
    assert reverse("login") == "/login/"
    assert reverse("register") == "/register/"
    assert reverse("profile") == "/profile/"
    assert reverse("program_list") == "/programs/"
    assert reverse("candidate_list") == "/candidates/"
    assert reverse("health_check") == "/health/"


def test_resolve_core_routes():
    assert resolve("/").url_name == "index"
    assert resolve("/login/").url_name == "login"
    assert resolve("/register/").url_name == "register"
    assert resolve("/profile/").url_name == "profile"
    assert resolve("/programs/").url_name == "program_list"
    assert resolve("/candidates/").url_name == "candidate_list"
    assert resolve("/health/").url_name == "health_check"

