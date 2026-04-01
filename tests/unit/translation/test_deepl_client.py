"""
Tests for DeepL client.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from lute.translation.deepl_client import DeepLClient


class TestDeepLClient:
    """Tests for DeepLClient."""

    def test_client_is_configured_with_api_key(self):
        """Should report configured when API key is provided."""
        client = DeepLClient(api_key="test-key")
        assert client.is_configured() is True

    def test_client_is_not_configured_without_api_key(self, monkeypatch):
        """Should report not configured when no API key."""
        monkeypatch.delenv("DEEPL_API_KEY", raising=False)
        client = DeepLClient(api_key=None)
        assert client.is_configured() is False

    def test_client_reads_api_key_from_environment(self, monkeypatch):
        """Should read API key from DEEPL_API_KEY environment variable."""
        monkeypatch.setenv("DEEPL_API_KEY", "env-api-key")
        client = DeepLClient()
        assert client.api_key == "env-api-key"
        assert client.is_configured() is True

    def test_translate_returns_error_when_not_configured(self, monkeypatch):
        """Should return error when API key is not configured."""
        monkeypatch.delenv("DEEPL_API_KEY", raising=False)
        client = DeepLClient(api_key=None)
        result = client.translate("text", "context")
        
        assert result["success"] is False
        assert "not configured" in result["error"]
        assert result["debug"]["api_key_present"] is False

    @patch('lute.translation.deepl_client.requests.post')
    def test_translate_calls_api_with_correct_payload(self, mock_post):
        """Should call DeepL API with correct payload."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "translations": [{"text": "house", "detected_source_language": "DE"}]
        }
        mock_response.headers = {}
        mock_post.return_value = mock_response

        client = DeepLClient(api_key="test-key")
        result = client.translate(
            text="Haus",
            context="Das Haus ist groß.",
            source_lang="DE",
            target_lang="EN"
        )

        assert result["success"] is True
        assert result["translation"] == "house"
        
        # Verify the API was called correctly
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://api-free.deepl.com/v2/translate"
        
        headers = call_args[1]["headers"]
        assert headers["Authorization"] == "DeepL-Auth-Key test-key"
        assert headers["Content-Type"] == "application/json"
        
        payload = call_args[1]["json"]
        assert payload["text"] == ["Haus"]
        assert payload["context"] == "Das Haus ist groß."
        assert payload["source_lang"] == "DE"
        assert payload["target_lang"] == "EN"

    @patch('lute.translation.deepl_client.requests.post')
    def test_translate_handles_api_error_response(self, mock_post):
        """Should handle API error responses correctly."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = json.dumps({"message": "Authorization failed", "code": 403})
        mock_response.json.return_value = {"message": "Authorization failed", "code": 403}
        
        from requests.exceptions import HTTPError
        mock_response.raise_for_status.side_effect = HTTPError(
            response=mock_response
        )
        mock_post.return_value = mock_response

        client = DeepLClient(api_key="invalid-key")
        result = client.translate("text", "context")

        assert result["success"] is False
        assert "Authorization failed" in result["error"]
        assert result["debug"]["response"]["status_code"] == 403

    @patch('lute.translation.deepl_client.requests.post')
    def test_translate_handles_timeout(self, mock_post):
        """Should handle request timeout."""
        from requests.exceptions import Timeout
        mock_post.side_effect = Timeout("Request timed out")

        client = DeepLClient(api_key="test-key")
        result = client.translate("text", "context")

        assert result["success"] is False
        assert "timed out" in result["error"]

    @patch('lute.translation.deepl_client.requests.post')
    def test_translate_handles_connection_error(self, mock_post):
        """Should handle connection errors."""
        from requests.exceptions import ConnectionError
        mock_post.side_effect = ConnectionError("No connection")

        client = DeepLClient(api_key="test-key")
        result = client.translate("text", "context")

        assert result["success"] is False
        assert "failed" in result["error"]

    @patch('lute.translation.deepl_client.requests.post')
    def test_translate_handles_empty_translation_response(self, mock_post):
        """Should handle response with no translations."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"translations": []}
        mock_response.headers = {}
        mock_response.text = json.dumps({"translations": []})
        mock_post.return_value = mock_response

        client = DeepLClient(api_key="test-key")
        result = client.translate("text", "context")

        assert result["success"] is False
        assert "No translation returned" in result["error"]

    @patch('lute.translation.deepl_client.requests.post')
    def test_translate_stores_request_and_response_for_debugging(self, mock_post):
        """Should store request and response for debugging."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "translations": [{"text": "house", "detected_source_language": "DE"}]
        }
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = json.dumps({
            "translations": [{"text": "house", "detected_source_language": "DE"}]
        })
        mock_post.return_value = mock_response

        client = DeepLClient(api_key="test-key")
        result = client.translate("Haus", "Das Haus ist groß.")

        assert client.last_request is not None
        assert client.last_request["url"] == "https://api-free.deepl.com/v2/translate"
        assert "payload" in client.last_request
        
        assert client.last_response is not None
        assert client.last_response["status_code"] == 200

    def test_default_api_url_is_free_api(self):
        """Should use free DeepL API endpoint by default."""
        client = DeepLClient(api_key="test-key")
        assert client.DEEPL_API_URL == "https://api-free.deepl.com/v2/translate"
