"""
Translation API routes.
"""

from flask import Blueprint, request, jsonify
from lute.translation.service import TranslationService

bp = Blueprint("translation", __name__, url_prefix="/translation")


@bp.route("/generate", methods=["POST"])
def generate_translation():
    """
    Generate contextual translation using DeepL.

    Request JSON:
    {
        "selectedText": "the word or phrase to translate",
        "contextText": "the full sentence containing the selection",
        "sourceLang": "DE",  # optional, defaults to DE
        "targetLang": "EN"   # optional, defaults to EN
    }

    Response JSON:
    {
        "success": true/false,
        "translation": "translated text",
        "error": "error message if failed",
        "debug": { ... }  # detailed info for debugging
    }
    """
    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "translation": None,
            "error": "No request data provided",
            "debug": {"request": "empty"}
        }), 400

    selected_text = data.get("selectedText", "")
    context_text = data.get("contextText", "")
    source_lang = data.get("sourceLang", "DE")
    target_lang = data.get("targetLang", "EN")

    # Log for debugging (will appear in console/logs)
    print(f"[Translation] Request: selected='{selected_text}', source={source_lang}, target={target_lang}")
    print(f"[Translation] Context length: {len(context_text)} chars")

    service = TranslationService()
    result = service.generate_translation(
        selected_text=selected_text,
        context_text=context_text,
        source_lang=source_lang,
        target_lang=target_lang
    )

    status_code = 200 if result["success"] else 500

    # Always include debug info for easier debugging
    print(f"[Translation] Result: success={result['success']}, error={result.get('error')}")
    if not result["success"]:
        print(f"[Translation] Debug: {result.get('debug')}")

    return jsonify(result), status_code


@bp.route("/status", methods=["GET"])
def translation_status():
    """
    Check if DeepL API is configured and test the key.

    Returns:
    {
        "configured": true/false,
        "api_key_present": true/false,
        "api_key_ends_with": "...abc" (last 6 chars),
        "test_result": "success/error message" (if configured)
    }
    """
    service = TranslationService()
    from lute.translation.deepl_client import DeepLClient
    client = DeepLClient()
    
    result = {
        "configured": service.is_configured(),
        "api_key_present": client.is_configured(),
    }
    
    if client.api_key:
        result["api_key_ends_with"] = "..." + client.api_key[-6:]
        
        # Make a tiny test call to verify the key works
        try:
            import requests
            test_response = requests.post(
                "https://api-free.deepl.com/v2/translate",
                headers={"Authorization": f"DeepL-Auth-Key {client.api_key}"},
                json={"text": ["hi"], "target_lang": "DE"},
                timeout=5
            )
            result["test_http_status"] = test_response.status_code
            if test_response.status_code == 200:
                result["test_result"] = "API key is valid and working"
            else:
                result["test_result"] = f"API error: {test_response.status_code} - {test_response.text[:100]}"
        except Exception as e:
            result["test_result"] = f"Connection error: {str(e)}"
    else:
        result["test_result"] = "No API key configured"
    
    return jsonify(result)
