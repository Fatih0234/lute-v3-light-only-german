"""
Tests for translation routes.
"""

import pytest
import json
from unittest.mock import patch, MagicMock


class TestTranslationRoutes:
    """Tests for translation API endpoints."""

    def test_generate_endpoint_returns_translation_on_success(self, client):
        """Should return translation when DeepL call succeeds."""
        with patch('lute.translation.routes.TranslationService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.generate_translation.return_value = {
                "success": True,
                "translation": "house",
                "error": None,
                "debug": {"request": {}, "response": {}}
            }
            mock_service_class.return_value = mock_service

            response = client.post(
                "/translation/generate",
                data=json.dumps({
                    "selectedText": "Haus",
                    "contextText": "Das Haus ist groß.",
                    "sourceLang": "DE",
                    "targetLang": "EN"
                }),
                content_type="application/json"
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True
            assert data["translation"] == "house"

    def test_generate_endpoint_returns_error_on_failure(self, client):
        """Should return error when DeepL call fails."""
        with patch('lute.translation.routes.TranslationService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.generate_translation.return_value = {
                "success": False,
                "translation": None,
                "error": "DeepL API error",
                "debug": {"request": {}}
            }
            mock_service_class.return_value = mock_service

            response = client.post(
                "/translation/generate",
                data=json.dumps({
                    "selectedText": "Haus",
                    "contextText": "Das Haus ist groß."
                }),
                content_type="application/json"
            )

            assert response.status_code == 500
            data = json.loads(response.data)
            assert data["success"] is False
            assert "DeepL API error" in data["error"]

    def test_generate_endpoint_returns_error_for_missing_data(self, client):
        """Should return error when request data is missing."""
        response = client.post(
            "/translation/generate",
            data=json.dumps({}),
            content_type="application/json"
        )

        # With empty JSON object, it should process but fail validation
        assert response.status_code in [200, 400, 500]
        data = json.loads(response.data)
        assert data["success"] is False
        assert "error" in data

    def test_generate_endpoint_uses_default_languages(self, client):
        """Should use DE and EN as default languages."""
        with patch('lute.translation.routes.TranslationService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.generate_translation.return_value = {
                "success": True,
                "translation": "test",
                "error": None,
                "debug": {}
            }
            mock_service_class.return_value = mock_service

            response = client.post(
                "/translation/generate",
                data=json.dumps({
                    "selectedText": "word",
                    "contextText": "This is a sentence with word."
                }),
                content_type="application/json"
            )

            assert response.status_code == 200
            mock_service.generate_translation.assert_called_once_with(
                selected_text="word",
                context_text="This is a sentence with word.",
                source_lang="DE",
                target_lang="EN"
            )

    def test_status_endpoint_returns_configured_true(self, client):
        """Should return configured status."""
        with patch('lute.translation.routes.TranslationService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.is_configured.return_value = True
            mock_service_class.return_value = mock_service

            response = client.get("/translation/status")

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["configured"] is True

    def test_status_endpoint_returns_configured_false(self, client):
        """Should return not configured when API key missing."""
        with patch('lute.translation.routes.TranslationService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.is_configured.return_value = False
            mock_service_class.return_value = mock_service

            response = client.get("/translation/status")

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["configured"] is False
