"""
DeepL API client for translation.

Simple wrapper for DeepL API v2 for debugging purposes.
"""

import os
import json
import requests


class DeepLClient:
    """
    Simple DeepL API client.

    Uses environment variable DEEPL_API_KEY for authentication.
    """

    DEEPL_API_URL = "https://api-free.deepl.com/v2/translate"

    def __init__(self, api_key=None):
        """
        Initialize client.

        Args:
            api_key: Optional API key. If not provided, reads from DEEPL_API_KEY env var.
        """
        self.api_key = api_key or os.environ.get("DEEPL_API_KEY")
        self.last_request = None
        self.last_response = None
        self.last_error = None

    def is_configured(self):
        """Check if API key is available."""
        return bool(self.api_key)

    def translate(self, text, context, source_lang="DE", target_lang="EN"):
        """
        Translate text with context.

        Args:
            text: The text to translate (selected text)
            context: The surrounding context (current sentence)
            source_lang: Source language code (default: DE)
            target_lang: Target language code (default: EN)

        Returns:
            dict: {
                "success": bool,
                "translation": str or None,
                "error": str or None,
                "debug": dict with request/response info for debugging
            }
        """
        if not self.is_configured():
            return {
                "success": False,
                "translation": None,
                "error": "DeepL API key not configured (set DEEPL_API_KEY env var)",
                "debug": {"api_key_present": False}
            }

        payload = {
            "text": [text],
            "source_lang": source_lang.upper(),
            "target_lang": target_lang.upper(),
            "context": context
        }

        headers = {
            "Authorization": f"DeepL-Auth-Key {self.api_key}",
            "Content-Type": "application/json"
        }

        self.last_request = {
            "url": self.DEEPL_API_URL,
            "headers": {k: v for k, v in headers.items() if k != "Authorization"},
            "payload": payload
        }

        try:
            print(f"[DeepL] Making request to {self.DEEPL_API_URL}")
            print(f"[DeepL] Text length: {len(text)} chars")
            print(f"[DeepL] Context length: {len(context)} chars")
            print(f"[DeepL] API key present: {bool(self.api_key)}")
            print(f"[DeepL] API key ends with: ...{self.api_key[-6:] if self.api_key else 'N/A'}")
            
            response = requests.post(
                self.DEEPL_API_URL,
                headers=headers,
                json=payload,
                timeout=10
            )
            
            print(f"[DeepL] Response status: {response.status_code}")
            print(f"[DeepL] Response headers: {dict(response.headers)}")
            
            self.last_response = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.text
            }

            response.raise_for_status()
            data = response.json()

            translations = data.get("translations", [])
            if translations:
                translation = translations[0].get("text", "")
                print(f"[DeepL] Translation successful: '{translation}'")
                return {
                    "success": True,
                    "translation": translation,
                    "error": None,
                    "debug": {
                        "request": self.last_request,
                        "response": data
                    }
                }
            else:
                print(f"[DeepL] No translations in response: {data}")
                return {
                    "success": False,
                    "translation": None,
                    "error": "No translation returned from DeepL",
                    "debug": {
                        "request": self.last_request,
                        "response": data
                    }
                }

        except requests.exceptions.HTTPError as e:
            error_msg = f"DeepL API error: {e.response.status_code}"
            try:
                error_data = e.response.json()
                error_msg += f" - {error_data.get('message', 'Unknown error')}"
            except:
                error_msg += f" - {e.response.text}"

            self.last_error = error_msg
            print(f"[DeepL] HTTP Error: {error_msg}")
            return {
                "success": False,
                "translation": None,
                "error": error_msg,
                "debug": {
                    "request": self.last_request,
                    "response": {
                        "status_code": e.response.status_code,
                        "body": e.response.text
                    }
                }
            }

        except requests.exceptions.Timeout:
            self.last_error = "DeepL API request timed out"
            return {
                "success": False,
                "translation": None,
                "error": "Request timed out",
                "debug": {"request": self.last_request, "error": "timeout"}
            }

        except requests.exceptions.RequestException as e:
            self.last_error = f"DeepL API request failed: {str(e)}"
            return {
                "success": False,
                "translation": None,
                "error": self.last_error,
                "debug": {"request": self.last_request, "error": str(e)}
            }

        except Exception as e:
            self.last_error = f"Unexpected error: {str(e)}"
            return {
                "success": False,
                "translation": None,
                "error": self.last_error,
                "debug": {"request": self.last_request, "error": str(e)}
            }
