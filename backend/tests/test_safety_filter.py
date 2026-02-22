"""Tests for SafetyFilter."""

import pytest

from backend.services.safety_filter import SafetyFilter


@pytest.fixture
def sf() -> SafetyFilter:
    return SafetyFilter()


# ------------------------------------------------------------------ #
# is_safe
# ------------------------------------------------------------------ #
class TestIsSafe:
    def test_safe_query(self, sf: SafetyFilter):
        assert sf.is_safe("example.com") is True

    def test_blocks_gov(self, sf: SafetyFilter):
        assert sf.is_safe("whitehouse.gov") is False

    def test_blocks_edu(self, sf: SafetyFilter):
        assert sf.is_safe("mit.edu") is False

    def test_blocks_mil(self, sf: SafetyFilter):
        assert sf.is_safe("army.mil") is False

    def test_blocks_subdomain(self, sf: SafetyFilter):
        assert sf.is_safe("mail.whitehouse.gov") is False

    def test_safe_with_keyword(self, sf: SafetyFilter):
        assert sf.is_safe("find social media for John Doe") is True

    def test_blocks_in_sentence(self, sf: SafetyFilter):
        assert sf.is_safe("search for info on cia.gov site") is False


# ------------------------------------------------------------------ #
# validate
# ------------------------------------------------------------------ #
class TestValidate:
    def test_returns_query_when_safe(self, sf: SafetyFilter):
        query = "example.com"
        assert sf.validate(query) == query

    def test_raises_on_blocked(self, sf: SafetyFilter):
        with pytest.raises(ValueError, match="sensitive domain"):
            sf.validate("whitehouse.gov")

    def test_error_lists_blocked_domains(self, sf: SafetyFilter):
        with pytest.raises(ValueError, match="army.mil"):
            sf.validate("look up army.mil records")
