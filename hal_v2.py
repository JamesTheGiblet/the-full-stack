#!/usr/bin/env python3
"""hal_v2.py — strict layer over hal.py: exit 1 on failure.

Function:
    HAL layer v2. The original hal.py seal has a silent-pass bug: it
    prints `FAILED` when the authoriser score signature is invalid,
    but then exits 0. A pipeline calling hal.py seal believes a seal
    was created.

    v2 delegates to hal.py's seal logic but intercepts the exit code.
    If the original logic prints a `FAILED` line to stdout or stderr,
    v2 returns 1. Otherwise v2 returns whatever hal.py returned.

    Usage: python3 hal_v2.py seal [same args as hal.py seal]
           python3 hal_v2.py verify-seal ...
           python3 hal_v2.py pin-seal ...

Tier:     P15 (HAL), v2 layer
Depends:  hal.py
Version:  1.0.0
Licence:  MSL-1.0
"""

import io
import sys
import contextlib
import argparse

import hal


def main() -> int:
    # Capture both stdout and stderr from hal.main()
    buf_out = io.StringIO()
    buf_err = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
            rc = hal.main()
    except SystemExit as e:
        rc = e.code if isinstance(e.code, int) else 1
    finally:
        out = buf_out.getvalue()
        err = buf_err.getvalue()
        # Replay to the real streams so the user sees them
        sys.stdout.write(out)
        sys.stderr.write(err)

    # If the original logic printed a FAILED line, force exit 1
    combined = (out + "\n" + err).upper()
    if "FAILED" in combined:
        return 1

    return rc


if __name__ == "__main__":
    sys.exit(main())
