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
        assert "Resource: Example Page" in result
        assert "URL: https://example.com" in result
        assert "Info: An example snippet." in result

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
        assert "Resource: Result Title" in result
        assert "URL: https://result.com" in result

    def test_formats_list_of_dicts(self):
        data = [
            {
                "title": "Item 1",
                "url": "https://item1.com",
                "description": "First item.",
            }
        ]
        result = _format_log_message(json.dumps(data))
        assert "Resource: Item 1" in result
        assert "URL: https://item1.com" in result
        assert "Info: First item." in result

    def test_multiple_results(self):
        data = {
            "organic": [
                {"title": "A", "link": "https://a.com", "snippet": "alpha"},
                {"title": "B", "link": "https://b.com", "snippet": "beta"},
            ]
        }
        result = _format_log_message(json.dumps(data))
        assert "Resource: A" in result
        assert "Resource: B" in result

    def test_missing_fields_use_na(self):
        data = {"organic": [{"title": "Only Title"}]}
        result = _format_log_message(json.dumps(data))
        assert "Resource: Only Title" in result
        assert "URL: N/A" in result
        assert "Info: N/A" in result


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
        assert "Resource: Test" in result
