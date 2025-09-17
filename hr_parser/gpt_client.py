from openai import OpenAI
from .config import OPENAI_API_KEY, MAX_INPUT_CHARS, MAX_OUTPUT_TOKENS
from .schemas import CanonicalResume

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = (
    "You are a resume parser for HyperRecruit. "
    "Return ONLY a JSON object that matches the provided JSON Schema exactly. "
    "Use null for unknown fields. Dates must be YYYY or YYYY-MM. "
    "Normalize skills (e.g., JS -> JavaScript)."
)

USER_PROMPT = (
    "Extract and normalize this resume into the Canonical JSON. "
    "Preserve bullet achievements for each role."
)

RESUME_JSON_SCHEMA = {
    "name": "resume_canonical_v1",
    "schema": CanonicalResume.model_json_schema(),
    "strict": True
}

def parse_with_gpt(text: str, source_file: str) -> dict:
    clipped = text[:MAX_INPUT_CHARS]

    response = client.responses.create(
        model="gpt-4o-mini",   # 👈 exactly here
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": [
                {"type":"text","text": USER_PROMPT},
                {"type":"input_text","text": clipped}
            ]}
        ],
        max_output_tokens=MAX_OUTPUT_TOKENS,
        response_format={"type": "json_schema", "json_schema": RESUME_JSON_SCHEMA},
    )

    return response.output_json