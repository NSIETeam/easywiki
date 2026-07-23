"""
EasyWiki — AI Content Generation Module
LLM-powered multi-language content generation via EasyRouter API
"""
import json, urllib.request, os
from typing import Dict, Optional
from orgmind.db import get_db
from orgmind.easywiki.products import get_product, get_templates, save_output

# EasyRouter config (from client's kb_server.py)
EASYROUTER_URL = os.getenv("EASYROUTER_URL", "https://easyrouter.cmcm.com/v1/chat/completions")
EASYROUTER_KEY = os.getenv("EASYROUTER_KEY", "sk-AKaZUBbgRCr4xPdzJnOo8ULoAFyc3loH816qDnyuGc2Ikur0")

# 60 languages (ISO 639-1)
LANGUAGES = {
    "zh":"Chinese","en":"English","ja":"Japanese","ko":"Korean","ar":"Arabic",
    "de":"German","fr":"French","es":"Spanish","pt":"Portuguese","ru":"Russian",
    "it":"Italian","nl":"Dutch","pl":"Polish","tr":"Turkish","vi":"Vietnamese",
    "th":"Thai","id":"Indonesian","ms":"Malay","hi":"Hindi","bn":"Bengali",
    "ur":"Urdu","fa":"Persian","he":"Hebrew","sw":"Swahili","zu":"Zulu",
    "am":"Amharic","ha":"Hausa","yo":"Yoruba","ig":"Igbo","ny":"Chichewa",
    "km":"Khmer","lo":"Lao","my":"Burmese","tl":"Filipino","ta":"Tamil",
    "te":"Telugu","kn":"Kannada","ml":"Malayalam","si":"Sinhala","ne":"Nepali",
    "mn":"Mongolian","ka":"Georgian","hy":"Armenian","az":"Azerbaijani",
    "fi":"Finnish","sv":"Swedish","no":"Norwegian","da":"Danish",
    "cs":"Czech","sk":"Slovak","hu":"Hungarian","ro":"Romanian",
    "bg":"Bulgarian","hr":"Croatian","sr":"Serbian","uk":"Ukrainian",
    "el":"Greek","ca":"Catalan","eu":"Basque","gl":"Galician",
}

# 10 article + 5 image + 5 video models
MODELS = {
    "article": [
        {"id":"kimi-k3","name":"Kimi K3","provider":"Moonshot","desc":"Latest model, strong Chinese NLP"},
        {"id":"gpt-4o","name":"GPT-4o","provider":"OpenAI","desc":"Best overall, multimodal"},
        {"id":"gpt-4o-mini","name":"GPT-4o Mini","provider":"OpenAI","desc":"Fast and affordable"},
        {"id":"claude-sonnet-5","name":"Claude Sonnet 5","provider":"Anthropic","desc":"Strong long-form writing"},
        {"id":"deepseek-v4-pro","name":"DeepSeek V4 Pro","provider":"DeepSeek","desc":"Best Chinese content"},
        {"id":"doubao-pro","name":"豆包 Pro","provider":"ByteDance","desc":"Chinese optimized, fast"},
        {"id":"gemini-2.5-pro","name":"Gemini 2.5 Pro","provider":"Google","desc":"Multilingual expert"},
        {"id":"gemini-2.5-flash","name":"Gemini 2.5 Flash","provider":"Google","desc":"Fast multilingual"},
        {"id":"qwen-max","name":"Qwen Max","provider":"Alibaba","desc":"Chinese+International"},
        {"id":"llama-4-maverick","name":"Llama 4 Maverick","provider":"Meta","desc":"Open source, strong reasoning"},
    ],
    "image": [
        {"id":"dall-e-3","name":"DALL-E 3","provider":"OpenAI","desc":"Text-to-image, photorealistic"},
        {"id":"midjourney-v7","name":"Midjourney V7","provider":"Midjourney","desc":"Best artistic quality"},
        {"id":"sd3","name":"Stable Diffusion 3","provider":"Stability AI","desc":"Open source, flexible"},
        {"id":"flux-pro","name":"Flux Pro","provider":"Black Forest","desc":"New gen, fast"},
        {"id":"imagen-3","name":"Imagen 3","provider":"Google","desc":"Photorealistic, safe"},
    ],
    "video": [
        {"id":"sora","name":"Sora","provider":"OpenAI","desc":"Text-to-video, cinematic"},
        {"id":"runway-gen4","name":"Runway Gen-4","provider":"Runway","desc":"Creative video, fast"},
        {"id":"kling","name":"Kling","provider":"Kuaishou","desc":"Chinese optimized"},
        {"id":"pika-2","name":"Pika 2","provider":"Pika Labs","desc":"Cartoon + cinematic"},
        {"id":"veo-2","name":"Veo 2","provider":"Google","desc":"High quality, long form"},
    ],
}


def get_models():
    """Return available AI models grouped by family"""
    return MODELS


def get_languages():
    """Return supported languages"""
    return LANGUAGES


def generate_content(
    template_id: str, product_key: str, model_id: str,
    language: str, org_id: str, user_id: str,
    highlights: list = None, specs: list = None
) -> Dict:
    """Generate content using EasyRouter LLM proxy"""
    db = get_db()
    templates = get_templates(org_id)
    template = next((t for t in templates if t['id'] == template_id), None)
    if not template:
        return {"ok": False, "error": "Template not found"}

    product = get_product(org_id, product_key)
    if not product:
        return {"ok": False, "error": "Product not found"}

    # Build context from product + selected references
    context_parts = [
        f"Product: {product['name']} ({product['name_zh']})",
        f"Description: {product['description']}",
    ]

    if product.get('specifications'):
        specs_dict = product['specifications']
        if isinstance(specs_dict, dict):
            context_parts.append(f"Specifications: {json.dumps(specs_dict, ensure_ascii=False)}")

    if product.get('highlights'):
        hl = product['highlights']
        if isinstance(hl, list) and hl:
            context_parts.append("Key Highlights:")
            for h in hl[:5]:
                context_parts.append(f"- {h}")

    if product.get('scenes'):
        scenes = product['scenes']
        if isinstance(scenes, list) and scenes:
            context_parts.append("Application Scenes:")
            for s in scenes[:3]:
                context_parts.append(f"- {s}")

    context = "\n".join(context_parts)

    # Build prompt
    lang_name = LANGUAGES.get(language, "English")
    lang_instr = f"\nWrite in {lang_name} language." if language != "zh" else ""

    prompt = template['prompt_template'].replace("{context}", context) + lang_instr

    # Call EasyRouter
    req = urllib.request.Request(
        EASYROUTER_URL,
        data=json.dumps({
            'model': model_id,
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 4000
        }).encode(),
        headers={
            'Authorization': f'Bearer {EASYROUTER_KEY}',
            'Content-Type': 'application/json'
        }
    )

    try:
        resp = urllib.request.urlopen(req, timeout=180)
        result = json.loads(resp.read())
        content = result['choices'][0]['message']['content']

        # Save output
        output = save_output(
            org_id, user_id, template['article_type'],
            model_id, language, prompt, content,
            product_key, template_id
        )

        return {
            "ok": True,
            "content": content,
            "output_id": output['id'],
            "model_used": model_id,
            "language": language,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}
