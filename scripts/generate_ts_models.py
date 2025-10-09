# A script that generates TypeScript models from the Pydantic models in va-spec

from pydantic2ts import generate_typescript_defs
from pathlib import Path

root = Path(__file__).resolve().parent.parent
output_file = root / "client" / "models" / "domain.ts"

ts_code = generate_typescript_defs("ga4gh.va_spec.base.core", str(output_file))
print(f"[ok] Wrote {output_file}")
