"""
Translation service for context-aware translations.
"""

from lute.translation.deepl_client import DeepLClient


class TranslationService:
    """
    Service for generating context-aware translations.
    """

    def __init__(self, api_key=None):
        """
        Initialize service.

        Args:
            api_key: Optional DeepL API key. If not provided, uses environment variable.
        """
        self.deepl_client = DeepLClient(api_key)

    def generate_translation(self, selected_text, context_text, source_lang="DE", target_lang="EN"):
        """
        Generate translation for selected text with context.

        Args:
            selected_text: The text selected by the user (word or phrase)
            context_text: The full sentence containing the selection
            source_lang: Source language code (default: DE)
            target_lang: Target language code (default: EN)

        Returns:
            dict: {
                "success": bool,
                "translation": str or None,
                "error": str or None,
                "debug": dict with request/response info
            }
        """
        # Validation for debugging
        if not selected_text or not selected_text.strip():
            return {
                "success": False,
                "translation": None,
                "error": "No text selected",
                "debug": {"input": {"selected_text": selected_text, "context_text": context_text}}
            }

        if not context_text or not context_text.strip():
            return {
                "success": False,
                "translation": None,
                "error": "No context provided",
                "debug": {"input": {"selected_text": selected_text, "context_text": context_text}}
            }

        # Clean up inputs
        selected_text = selected_text.strip()
        context_text = context_text.strip()

        # Ensure selected text is within context (for debugging)
        # Normalize by removing zero-width spaces for comparison
        zws = "\u200B"
        selected_normalized = selected_text.replace(zws, "").replace("  ", " ").strip()
        context_normalized = context_text.replace(zws, "").replace("  ", " ").strip()
        
        if selected_normalized not in context_normalized:
            return {
                "success": False,
                "translation": None,
                "error": f"Selected text '{selected_text}' not found in context",
                "debug": {
                    "input": {"selected_text": selected_text, "context_text": context_text},
                    "validation": "selected_text not in context_text",
                    "selected_normalized": selected_normalized,
                    "context_preview": context_normalized[:100]
                }
            }

        # Call DeepL
        result = self.deepl_client.translate(
            text=selected_text,
            context=context_text,
            source_lang=source_lang,
            target_lang=target_lang
        )

        return result

    def is_configured(self):
        """Check if DeepL API is configured."""
        return self.deepl_client.is_configured()
