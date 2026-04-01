"""
Tests for translation service.
"""

import pytest
from unittest.mock import patch, MagicMock
from lute.translation.service import TranslationService


class TestTranslationService:
    """Tests for TranslationService."""

    def test_service_is_configured_when_api_key_set(self):
        """Service should report configured when API key is provided."""
        service = TranslationService(api_key="test-key")
        assert service.is_configured() is True

    def test_service_is_not_configured_when_api_key_empty(self, monkeypatch):
        """Service should report not configured when API key is empty."""
        monkeypatch.delenv("DEEPL_API_KEY", raising=False)
        service = TranslationService(api_key="")
        assert service.is_configured() is False

    def test_generate_translation_returns_error_for_empty_text(self):
        """Should return error when selected text is empty."""
        service = TranslationService(api_key="test-key")
        result = service.generate_translation("", "some context")
        
        assert result["success"] is False
        assert "No text selected" in result["error"]
        assert result["debug"]["input"]["selected_text"] == ""

    def test_generate_translation_returns_error_for_empty_context(self):
        """Should return error when context is empty."""
        service = TranslationService(api_key="test-key")
        result = service.generate_translation("word", "")
        
        assert result["success"] is False
        assert "No context provided" in result["error"]

    def test_generate_translation_returns_error_when_text_not_in_context(self):
        """Should return error when selected text is not found in context."""
        service = TranslationService(api_key="test-key")
        result = service.generate_translation("word", "completely different sentence")
        
        assert result["success"] is False
        assert "not found in context" in result["error"]
        assert result["debug"]["validation"] == "selected_text not in context_text"

    @patch('lute.translation.service.DeepLClient')
    def test_generate_translation_calls_deepl_with_correct_params(self, mock_client_class):
        """Should call DeepL client with correct parameters."""
        mock_client = MagicMock()
        mock_client.translate.return_value = {
            "success": True,
            "translation": "translated text",
            "error": None,
            "debug": {}
        }
        mock_client_class.return_value = mock_client

        service = TranslationService(api_key="test-key")
        result = service.generate_translation(
            "Haus", 
            "Das Haus ist groß.",
            source_lang="DE",
            target_lang="EN"
        )

        assert result["success"] is True
        mock_client.translate.assert_called_once_with(
            text="Haus",
            context="Das Haus ist groß.",
            source_lang="DE",
            target_lang="EN"
        )

    @patch('lute.translation.service.DeepLClient')
    def test_generate_translation_passes_through_deepl_error(self, mock_client_class):
        """Should pass through error from DeepL client."""
        mock_client = MagicMock()
        mock_client.translate.return_value = {
            "success": False,
            "translation": None,
            "error": "DeepL API error: 403",
            "debug": {"request": {}, "response": {"status_code": 403}}
        }
        mock_client_class.return_value = mock_client

        service = TranslationService(api_key="test-key")
        result = service.generate_translation("word", "This is a sentence with word.")

        assert result["success"] is False
        assert "DeepL API error: 403" in result["error"]

    def test_generate_translation_strips_whitespace(self):
        """Should strip whitespace from inputs."""
        service = TranslationService(api_key="test-key")
        
        with patch.object(service.deepl_client, 'translate') as mock_translate:
            mock_translate.return_value = {
                "success": True,
                "translation": "house",
                "error": None,
                "debug": {}
            }
            
            result = service.generate_translation(
                "  Haus  ", 
                "  Das Haus ist groß.  "
            )
            
            mock_translate.assert_called_once_with(
                text="Haus",
                context="Das Haus ist groß.",
                source_lang="DE",
                target_lang="EN"
            )
