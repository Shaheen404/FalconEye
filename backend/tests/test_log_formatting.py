"""Tests for _format_log_message in crew_routes."""

import json

import pytest

from backend.routes.crew_routes import _format_log_message


class TestFormatLogMessagePlainText:
    def test_returns_plain_string_unchanged(self):
        assert _format_log_message("hello world") == "hello world"

    def test_returns_empty_string_unchanged(self):
        assert _format_log_message("") == ""


class TestFormatLogMessageSerperJSON:
    def test_formats_organic_results(self):
        data = {
            "organic": [
                {
                    "title": "Example Page",
                    "link": "https://example.com",
                    "snippet": "An example snippet.",
                }
            ]
        }
        result = _format_log_message(json.dumps(data))
        assert "Example Page" in result
        assert "https://example.com" in result
        assert "An example snippet." in result

    def test_formats_results_key(self):
        data = {
            "results": [
                {
                    "title": "Result Title",
                    "link": "https://result.com",
                    "snippet": "A snippet.",
                }
            ]
        }
        result = _format_log_message(json.dumps(data))
        assert "Result Title" in result
        assert "https://result.com" in result

    def test_formats_list_of_dicts(self):
        data = [
            {
                "title": "Item 1",
                "url": "https://item1.com",
                "description": "First item.",
            }
        ]
        result = _format_log_message(json.dumps(data))
        assert "Item 1" in result
        assert "https://item1.com" in result
        assert "First item." in result

    def test_multiple_results(self):
        data = {
            "organic": [
                {"title": "A", "link": "https://a.com", "snippet": "alpha"},
                {"title": "B", "link": "https://b.com", "snippet": "beta"},
            ]
        }
        result = _format_log_message(json.dumps(data))
        assert "A" in result
        assert "B" in result

    def test_missing_fields_use_na(self):
        data = {"organic": [{"title": "Only Title"}]}
        result = _format_log_message(json.dumps(data))
        assert "Only Title" in result
        assert "N/A" in result

    def test_output_uses_markdown_headers(self):
        data = {
            "organic": [
                {
                    "title": "Example",
                    "link": "https://example.com",
                    "snippet": "desc",
                }
            ]
        }
        result = _format_log_message(json.dumps(data))
        assert "###" in result
        assert "**URL:**" in result
        assert "**Details:**" in result


class TestFormatLogMessageFallback:
    def test_dict_without_results_returns_raw(self):
        data = {"status": "ok"}
        raw = json.dumps(data)
        assert _format_log_message(raw) == raw

    def test_non_list_results_returns_raw(self):
        data = {"organic": "not a list"}
        raw = json.dumps(data)
        assert _format_log_message(raw) == raw

    def test_empty_results_returns_raw(self):
        data = {"organic": []}
        raw = json.dumps(data)
        assert _format_log_message(raw) == raw

    def test_python_repr_dict_parsed(self):
        raw = "{'organic': [{'title': 'Test', 'link': 'https://test.com', 'snippet': 'hello'}]}"
        result = _format_log_message(raw)
        assert "Test" in result
        assert "https://test.com" in result
