import base64
import hashlib
import json
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from openai import OpenAI

from wardrobe.models import CareAnalysis, UsageLog


# Cost constants for GPT-4o (as of 2026)
INPUT_COST_PER_TOKEN = Decimal('0.0000025')   # $2.50 / 1M input tokens
OUTPUT_COST_PER_TOKEN = Decimal('0.00001')    # $10.00 / 1M output tokens

DAILY_LIMIT = 10
BUDGET_GUARD_USD = Decimal('9.00')


class RateLimitExceeded(Exception):
    pass


class BudgetGuardTripped(Exception):
    pass


class AnalysisError(Exception):
    pass


# Lazy client — instantiated on first API call so the module can be imported
# without OPENAI_API_KEY set (e.g., during Django system checks, tests)
_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI()  # reads OPENAI_API_KEY from environment
    return _client


def _daily_count(user) -> int:
    """Return number of API calls made by user today."""
    return UsageLog.objects.filter(
        user=user,
        created_at__date=timezone.now().date(),
    ).count()


def _budget_exceeded() -> bool:
    """Return True if cumulative spend has reached BUDGET_GUARD_USD."""
    total = UsageLog.objects.aggregate(t=Sum('cost_usd'))['t'] or Decimal('0')
    return total >= BUDGET_GUARD_USD


def _image_hash(image_bytes: bytes) -> str:
    """Return SHA-256 hex digest of image bytes."""
    return hashlib.sha256(image_bytes).hexdigest()


def budget_guard_active() -> bool:
    """Public helper for views/context — True when budget limit reached."""
    return _budget_exceeded()


def get_daily_count(user) -> int:
    """Public helper for context processor — daily API call count for user."""
    return _daily_count(user)


def _call_api(image_bytes: bytes, fabric_hint: str = "") -> tuple:
    """Call GPT-4o Vision API and return (parsed_dict, usage).

    Returns:
        tuple: (parsed response dict, usage object with token counts)

    Raises:
        AnalysisError: on any OpenAI API error
    """
    encoded = base64.b64encode(image_bytes).decode('utf-8')

    system_prompt = (
        "You are a laundry care expert. Analyze the care label in the image. "
        "Return a JSON object with exactly these keys: summary, washing, drying, ironing, "
        "bleach, is_delicate, failure_reason. "
        "For any care field you cannot determine from the label, use the string 'Unable to determine'. "
        "is_delicate must be a boolean (true if the item requires special/delicate handling, false otherwise). "
        "failure_reason must be null when the care label was successfully read. "
        "If the label cannot be read at all, set failure_reason to one of these exact strings: "
        "'No care label detected in image', "
        "'Care label text was not readable', "
        "'Image is too blurry to read the label', "
        "'Care label is partially obscured or cut off'. "
        "Return clean, direct instructions only."
    )

    user_content = "Analyze this care label."
    if fabric_hint:
        user_content += f" Fabric: {fabric_hint}."

    try:
        response = _get_client().chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            max_tokens=500,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_content},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{encoded}",
                            },
                        },
                    ],
                },
            ],
        )
    except Exception as e:
        raise AnalysisError(str(e)) from e

    parsed = json.loads(response.choices[0].message.content)
    return parsed, response.usage


def analyze_care_label(garment, user) -> CareAnalysis:
    """Analyze care label image for a garment using GPT-4o Vision.

    Flow:
        1. Budget guard check
        2. Rate limit check
        3. Read image bytes (once — FieldFile is a stream)
        4. Compute SHA-256 hash
        5. Dedup check against existing CareAnalysis records
        6. Call API if no cache hit
        7. Save CareAnalysis + UsageLog in transaction

    Args:
        garment: Garment instance with care_label_photo set
        user: User instance making the request

    Returns:
        CareAnalysis: newly created (or updated) analysis record

    Raises:
        BudgetGuardTripped: cumulative spend >= $9.00
        RateLimitExceeded: user has hit 10 calls today
        AnalysisError: OpenAI API failure
    """
    # 1. Budget guard
    if _budget_exceeded():
        raise BudgetGuardTripped()

    # 2. Rate limit
    if _daily_count(user) >= DAILY_LIMIT:
        raise RateLimitExceeded()

    # 3. Read image bytes ONCE — FieldFile is a stream
    garment.care_label_photo.open('rb')
    image_bytes = garment.care_label_photo.read()
    garment.care_label_photo.close()

    # 4. Compute image hash
    img_hash = _image_hash(image_bytes)

    # 5. Dedup check
    cached = CareAnalysis.objects.filter(image_hash=img_hash).first()
    from_cache = False
    parsed_dict = None
    usage = None

    if cached is not None and cached.garment == garment:
        # Same garment, same image — mark from_cache and return immediately
        cached.from_cache = True
        cached.save(update_fields=['from_cache'])
        return cached
    elif cached is not None:
        # Different garment, same image — copy AI fields, skip API call
        parsed_dict = cached.raw_ai_json
        from_cache = True
    else:
        # No cache — call the API
        parsed_dict, usage = _call_api(image_bytes, fabric_hint=garment.fabric or "")
        from_cache = False

    # 6. Save in transaction
    with transaction.atomic():
        # Delete existing analysis for this garment (re-analyze case)
        CareAnalysis.objects.filter(garment=garment).delete()

        failure_reason = parsed_dict.get('failure_reason') or None

        analysis = CareAnalysis.objects.create(
            garment=garment,
            image_hash=img_hash,
            raw_ai_json=parsed_dict,
            # Immutable AI fields
            ai_washing=parsed_dict.get('washing', 'Unable to determine'),
            ai_drying=parsed_dict.get('drying', 'Unable to determine'),
            ai_ironing=parsed_dict.get('ironing', 'Unable to determine'),
            ai_bleach=parsed_dict.get('bleach', 'Unable to determine'),
            ai_is_delicate=bool(parsed_dict.get('is_delicate', False)),
            ai_summary=parsed_dict.get('summary', 'Unable to determine'),
            # User-editable fields — initial copy of AI values
            washing=parsed_dict.get('washing', 'Unable to determine'),
            drying=parsed_dict.get('drying', 'Unable to determine'),
            ironing=parsed_dict.get('ironing', 'Unable to determine'),
            bleach=parsed_dict.get('bleach', 'Unable to determine'),
            is_delicate=bool(parsed_dict.get('is_delicate', False)),
            summary=parsed_dict.get('summary', 'Unable to determine'),
            from_cache=from_cache,
            failure_reason=failure_reason,
        )

        # Log usage only for real API calls (not cache hits)
        if not from_cache and usage is not None:
            cost = (
                Decimal(usage.prompt_tokens) * INPUT_COST_PER_TOKEN
                + Decimal(usage.completion_tokens) * OUTPUT_COST_PER_TOKEN
            )
            UsageLog.objects.create(
                user=user,
                garment=garment,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                cost_usd=cost,
            )

    return analysis
