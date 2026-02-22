"""SafetyFilter – blocks searches targeting sensitive domains.

Prevents the OSINT agents from querying or scraping domains that belong to
government, education, or military organisations.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


# Domains that must never be searched or scraped.
_BLOCKED_TLDS: tuple[str, ...] = (".gov", ".edu", ".mil")


@dataclass
class SafetyFilter:
    """Block reconnaissance queries that target sensitive domains."""

    blocked_tlds: tuple[str, ...] = field(default_factory=lambda: _BLOCKED_TLDS)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def is_safe(self, query: str) -> bool:
        """Return ``True`` when *query* does **not** reference a blocked TLD."""
        return not self._contains_blocked_domain(query)

    def validate(self, query: str) -> str:
        """Return the query unchanged if safe, otherwise raise ``ValueError``."""
        if not self.is_safe(query):
            blocked = self._find_blocked_domains(query)
            raise ValueError(
                f"Query blocked – references sensitive domain(s): {', '.join(blocked)}"
            )
        return query

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #
    def _contains_blocked_domain(self, text: str) -> bool:
        lower = text.lower()
        for tld in self.blocked_tlds:
            # Match "example.gov", "sub.example.edu", etc.
            if re.search(rf"[a-z0-9\-]+\{tld}\b", lower):
                return True
        return False

    def _find_blocked_domains(self, text: str) -> list[str]:
        lower = text.lower()
        found: list[str] = []
        for tld in self.blocked_tlds:
            matches = re.findall(rf"[a-z0-9\-]+\{tld}\b", lower)
            found.extend(matches)
        return found
