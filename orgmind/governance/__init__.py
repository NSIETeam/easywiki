from orgmind.governance.validators import ValidationError, validate_content, validate_file
from orgmind.governance.cleaners import clean_text
from orgmind.governance.pii import detect_pii, censor_pii, upgrade_sensitivity
from orgmind.governance.quality import compute_quality_score, QualityInput

# dedup must be imported lazily (depends on sqlalchemy models)

def __getattr__(name):
    if name in ("compute_content_hash", "check_memory_duplicate", "DupResult"):
        from orgmind.governance import dedup
        return getattr(dedup, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "ValidationError", "validate_content", "validate_file",
    "clean_text",
    "compute_content_hash", "check_memory_duplicate", "DupResult",
    "detect_pii", "censor_pii", "upgrade_sensitivity",
    "compute_quality_score", "QualityInput",
]
