#!/usr/bin/env python3
"""
Securely update the ANTHROPIC_API_KEY in .env without an editor.

Prompts for the key using getpass (input is hidden — nothing echoes to the
screen as you paste), strips any accidental whitespace/newlines, and
rewrites .env atomically.

Usage:
    .venv/bin/python scripts/set_api_key.py
"""
from __future__ import annotations

import getpass
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"


def main() -> int:
    print("This will update ANTHROPIC_API_KEY in:", ENV_PATH)
    print("Paste your new key, then press Enter. The key will NOT be echoed.")
    print()
    try:
        key = getpass.getpass("New API key: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        return 1

    if not key:
        print("ERROR: empty key, nothing written.", file=sys.stderr)
        return 2
    if not key.startswith("sk-ant-"):
        print(
            f"ERROR: key does not start with 'sk-ant-' — got {key[:8]!r}. "
            f"Did you paste the right thing?",
            file=sys.stderr,
        )
        return 3
    if len(key) < 50:
        print(
            f"ERROR: key is only {len(key)} characters. That's too short to be "
            f"a real Anthropic key (expected ~100+). Nothing written.",
            file=sys.stderr,
        )
        return 4

    ENV_PATH.write_text(f"ANTHROPIC_API_KEY={key}\n")
    print()
    print(f"Saved. Key length: {len(key)} characters.")
    print(f"Starts with: {key[:15]}...")
    print(f"Ends with:   ...{key[-5:]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
