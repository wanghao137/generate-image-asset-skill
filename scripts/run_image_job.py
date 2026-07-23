#!/usr/bin/env python3
"""Prepare and verify Codex built-in image generation jobs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RISK_PATTERNS = {
    "sexualized_private": [
        r"\bintimate\b",
        r"\bprivate\b",
        r"\bsensual(?:ity)?\b",
        r"\bshy confidence\b",
        r"\bphone hides\b",
        r"\bmirror selfie\b.*\b(?:bikini|lingerie|underwear)\b",
    ],
    "explicit_body_focus": [
        r"\bbust\s*size\b",
        r"\b\d{2,4}\s*cc\b",
        r"\bfull bust\b",
        r"\bnatural gravity\b",
        r"\bupper thighs\b",
        r"\bcleavage\b",
        r"\bareola\b",
        r"\bnipples?\b",
    ],
    "missing_reference_inputs": [
        r"\battached file\b",
        r"\battached file\s*\d+\b",
        r"\bface from the attached\b",
        r"\bwear the top from attached\b",
    ],
    "impossible_identity_exactness": [
        r"\b100%\s*accuracy\b",
        r"\bmatch the reference\s*100%\b",
        r"\bdo not alter the face in any way\b",
    ],
    "underage_ambiguity": [
        r"\bteen\b",
        r"\bgirl\b",
        r"\byoung-looking\b",
        r"\bschool(?:girl)?\b",
    ],
    "unsupported_profile": [
        r"\bbackground\s*=\s*transparent\b",
        r"\binput_fidelity\b",
    ],
}

RECOVERY_GUIDANCE = {
    "sexualized_private": (
        "Replace private, sensual, or voyeuristic framing with public editorial, "
        "commercial, or studio framing while preserving composition and styling."
    ),
    "explicit_body_focus": (
        "Remove body measurements and explicit body-part focus; describe wardrobe, "
        "silhouette, fabric fit, pose, or non-explicit fashion intent instead."
    ),
    "missing_reference_inputs": (
        "Inspect the referenced local image before generation, or remove the "
        "unsupported reference dependency when the image is unavailable."
    ),
    "impossible_identity_exactness": (
        "Preserve general visual characteristics instead of promising exact face, "
        "identity, or 100% reference reproduction."
    ),
    "underage_ambiguity": (
        "Add explicit adult framing only for non-sexualized adult subjects; block "
        "rather than rewrite if the scene sexualizes an underage or ambiguous subject."
    ),
    "unsupported_profile": (
        "Move unsupported output requirements into local post-processing or remove "
        "unsupported API-field language from the generation prompt."
    ),
}

DEFAULT_RECOVERY_GUIDANCE = (
    "If the built-in image tool refuses, make the smallest safety rewrite that "
    "preserves subject, composition, lighting, style, aspect ratio, and requested deliverable."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare a Codex built-in image generation asset job."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--prompt", help="Prompt text. Long prompts should use --prompt-file.")
    source.add_argument("--prompt-file", help="Path to a prompt text or JSON file.")
    parser.add_argument("--model", default="gpt-image-2")
    parser.add_argument("--size", default="2160x3840")
    parser.add_argument("--quality", default="high")
    parser.add_argument("--output-format", default="png")
    parser.add_argument("--moderation", choices=["auto", "low"], default="low")
    parser.add_argument("--out", default="output/imagegen/output.png")
    parser.add_argument("--backend", choices=["built-in", "task-api"], default="built-in")
    parser.add_argument("--api-url", default=os.environ.get("IMAGE_TASK_API_URL", "http://127.0.0.1:9789"))
    parser.add_argument("--api-token-env", default="IMAGE_TASK_API_TOKEN")
    parser.add_argument("--provider", default="mock")
    parser.add_argument(
        "--api-mode",
        dest="api_mode",
        choices=["images", "responses"],
        default="images",
        help="Task API endpoint mode: 'images' (POST /images/generations, image models) or 'responses' (POST /responses with image_generation tool, text models that output images).",
    )
    parser.add_argument("--source-asset-id")
    parser.add_argument("--content-class", choices=["photo", "illustration", "text", "logo", "ui"], default="photo")
    parser.add_argument("--enhancement", choices=["auto", "none", "lanczos3", "real-esrgan", "hat"], default="auto")
    parser.add_argument("--idempotency-key")
    parser.add_argument("--max-attempts", type=int, choices=range(1, 6), default=3)
    parser.add_argument("--work-dir", default="work/imagegen")
    parser.add_argument("--report", help="Report JSON path.")
    parser.add_argument("--recovery-log", help="Refusal recovery JSON log path.")
    parser.add_argument(
        "--max-refusal-retries",
        type=int,
        choices=[0, 1],
        default=1,
        help="How many minimal safety rewrites may be attempted after a tool refusal.",
    )
    parser.add_argument("--force", action="store_true", help="Allow replacing --out.")
    parser.add_argument("--dry-run", action="store_true", help="Alias for --prepare-only.")
    parser.add_argument("--prepare-only", action="store_true", help="Write the plan report.")
    parser.add_argument(
        "--policy-mode",
        choices=["warn", "block"],
        default="warn",
        help="How to handle deterministic prompt risk findings.",
    )
    parser.add_argument(
        "--allow-policy-findings",
        action="store_true",
        help="Deprecated alias for --policy-mode warn.",
    )
    return parser.parse_args()


def read_prompt(args: argparse.Namespace) -> tuple[str, Path | None]:
    if args.prompt_file:
        path = Path(args.prompt_file)
        return path.read_text(encoding="utf-8"), path
    return args.prompt or "", None


def write_prompt_file(prompt: str, work_dir: Path) -> Path:
    work_dir.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        suffix=".txt",
        prefix="prompt-",
        dir=work_dir,
        delete=False,
    )
    with handle:
        handle.write(prompt)
    return Path(handle.name)


def scan_prompt(prompt: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    lower = prompt.lower()
    for category, patterns in RISK_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, lower, flags=re.IGNORECASE | re.DOTALL):
                findings.append({"category": category, "pattern": pattern})
    return findings


def parse_size(size: str) -> tuple[int, int] | None:
    if size == "auto" or not re.fullmatch(r"\d+x\d+", size):
        return None
    width, height = [int(part) for part in size.split("x", 1)]
    return width, height


def validate_size(size: str) -> list[str]:
    if size == "auto":
        return []
    parsed = parse_size(size)
    if parsed is None:
        return [f"size must be auto or WIDTHxHEIGHT, got {size!r}"]
    width, height = parsed
    errors: list[str] = []
    if width <= 0 or height <= 0:
        errors.append("width and height must be positive")
    if width > 3840 or height > 3840:
        errors.append("maximum supported target edge is 3840px")
    if width * height > 8_294_400:
        errors.append("target pixel count must be at most 8294400")
    return errors


def png_info(path: Path) -> dict[str, Any] | None:
    if not path.is_file() or path.stat().st_size < 24:
        return None
    with path.open("rb") as file:
        header = file.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return {
        "path": str(path),
        "format": "png",
        "width": int.from_bytes(header[16:20], "big"),
        "height": int.from_bytes(header[20:24], "big"),
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def source_path_for(out_path: Path) -> Path:
    return out_path.with_name(f"{out_path.stem}-source{out_path.suffix}")


def raw_path_for(out_path: Path) -> Path:
    return out_path.with_name(f"{out_path.stem}-raw{out_path.suffix}")


def recovery_log_path_for(out_path: Path) -> Path:
    return out_path.with_suffix(".recovery.json")


def build_refusal_recovery_plan(
    prompt_findings: list[dict[str, str]],
    max_refusal_retries: int,
    prepared_prompt_file: Path,
    recovery_log_path: Path,
) -> dict[str, Any]:
    categories = sorted({finding["category"] for finding in prompt_findings})
    guidance = [RECOVERY_GUIDANCE[category] for category in categories if category in RECOVERY_GUIDANCE]
    if not guidance:
        guidance = [DEFAULT_RECOVERY_GUIDANCE]

    return {
        "enabled": max_refusal_retries > 0,
        "max_retries_after_refusal": max_refusal_retries,
        "initial_prompt_file": str(prepared_prompt_file),
        "recovery_log": str(recovery_log_path),
        "retry_allowed_when": [
            "the visual goal can be preserved",
            "only the likely refusal trigger needs to change",
            "subject, composition, style, lighting, aspect ratio, and deliverable remain intact",
        ],
        "retry_forbidden_when": [
            "the unsafe element is the core user request",
            "the scene sexualizes an underage or age-ambiguous subject",
            "the request implies non-consensual, leaked, private, or voyeuristic sexual imagery",
            "the rewrite would materially change the requested image",
        ],
        "minimal_rewrite_guidance": guidance,
        "required_record_fields": [
            "attempt_1.prompt_file",
            "attempt_1.result",
            "attempt_1.refusal_summary",
            "rewrite.trigger_category",
            "rewrite.summary",
            "attempt_2.prompt_file",
            "attempt_2.result",
        ],
    }


def build_recovery_log_template(
    prepared_prompt_file: Path,
    max_refusal_retries: int,
) -> dict[str, Any]:
    return {
        "status": "not_triggered",
        "max_retries_after_refusal": max_refusal_retries,
        "attempt_1": {
            "prompt_file": str(prepared_prompt_file),
            "result": "pending",
            "refusal_summary": None,
        },
        "rewrite": {
            "trigger_category": None,
            "summary": None,
            "preserved_constraints": [
                "subject",
                "composition",
                "style",
                "lighting",
                "aspect_ratio",
                "deliverable",
            ],
        },
        "attempt_2": {
            "prompt_file": None,
            "result": "not_run",
        },
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    work_dir = Path(args.work_dir)
    out_path = Path(args.out)
    report_path = Path(args.report) if args.report else out_path.with_suffix(".report.json")
    recovery_log_path = (
        Path(args.recovery_log) if args.recovery_log else recovery_log_path_for(out_path)
    )

    prompt, original_prompt_file = read_prompt(args)
    prepared_prompt_file = original_prompt_file or write_prompt_file(prompt, work_dir)
    prompt_findings = scan_prompt(prompt)
    size_errors = validate_size(args.size)
    output_exists = out_path.exists()
    source_path = source_path_for(out_path)
    raw_path = raw_path_for(out_path)

    status = "prepared"
    reason = None
    policy_mode = "warn" if args.allow_policy_findings else args.policy_mode
    if size_errors:
        status = "blocked"
        reason = "invalid target size"
    elif prompt_findings and policy_mode == "block":
        status = "blocked"
        reason = "prompt findings blocked by policy mode"
    elif output_exists and not args.force:
        status = "blocked"
        reason = "output exists; pass --force or choose a new path"

    target_dimensions = None
    parsed_size = parse_size(args.size)
    if parsed_size is not None:
        target_dimensions = {"width": parsed_size[0], "height": parsed_size[1]}

    warnings: list[str] = []
    if prompt_findings:
        warnings.append("prompt risk findings detected; generator may refuse")
    if args.max_refusal_retries == 0:
        warnings.append("refusal recovery retry disabled; report a tool refusal as blocked")

    refusal_recovery_plan = build_refusal_recovery_plan(
        prompt_findings,
        args.max_refusal_retries,
        prepared_prompt_file,
        recovery_log_path,
    )

    report: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "reason": reason,
        "route": "local-image-task-api" if args.backend == "task-api" else "codex-built-in-image-tool",
        "requested_profile": {
            "model": args.model,
            "quality": args.quality,
            "output_format": args.output_format,
            "moderation": args.moderation,
            "target_size": args.size,
        },
        "out": str(out_path),
        "source_out": str(source_path),
        "raw_out": str(raw_path),
        "prompt_file": str(prepared_prompt_file),
        "prompt_findings": prompt_findings,
        "refusal_recovery_plan": refusal_recovery_plan,
        "refusal_recovery_log": str(recovery_log_path),
        "size_errors": size_errors,
        "output_exists_before_run": output_exists,
        "postprocess_plan": {
            "copy_generated_cache_to_raw": args.backend == "built-in",
            "normalize_raw_to_source_ratio": args.backend == "built-in" and args.size != "auto",
            "resize_final_to_target": args.size != "auto",
            "target_dimensions": target_dimensions,
            "forbid_stretching": True,
            "source_ratio_must_match_final": True,
            "preserve_source": True,
        },
        "verification_plan": [
            "if the first image_gen attempt refuses, fill the refusal recovery log before rewriting",
            "retry at most once after a minimal safety rewrite when the visual goal can be preserved",
            "copy the unmodified generated cache image to raw_out",
            "normalize raw_out to a source_out canvas with the target ratio when needed",
            "resize only the ratio-matched source_out to target_size",
            "reject any source/final ratio mismatch instead of stretching",
            "read final file header for dimensions and byte size",
            "view final image before reporting completion",
        ],
        "warnings": warnings,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    recovery_log_path.parent.mkdir(parents=True, exist_ok=True)
    recovery_log_path.write_text(
        json.dumps(
            build_recovery_log_template(prepared_prompt_file, args.max_refusal_retries),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return report


def api_request(
    args: argparse.Namespace,
    path: str,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, str]]:
    token = os.environ.get(args.api_token_env)
    if not token:
        raise RuntimeError(f"environment variable {args.api_token_env} is required")
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        f"{args.api_url.rstrip('/')}{path}",
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            **({"Content-Type": "application/json"} if body is not None else {}),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=310) as response:
            return json.loads(response.read().decode("utf-8")), dict(response.headers.items())
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"task API returned HTTP {error.code}: {detail[:500]}") from error


def download_asset(args: argparse.Namespace, asset_id: str, path: Path) -> None:
    token = os.environ.get(args.api_token_env)
    if not token:
        raise RuntimeError(f"environment variable {args.api_token_env} is required")
    request = urllib.request.Request(
        f"{args.api_url.rstrip('/')}/v1/assets/{asset_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with urllib.request.urlopen(request, timeout=310) as response:
            temporary.write_bytes(response.read())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def exact_ratio(width: int, height: int) -> str:
    from math import gcd

    divisor = gcd(width, height)
    return f"{width // divisor}:{height // divisor}"


def execute_task_api(args: argparse.Namespace, report: dict[str, Any]) -> dict[str, Any]:
    parsed = parse_size(args.size)
    if parsed is None:
        raise RuntimeError("task-api backend requires an exact WIDTHxHEIGHT target")
    prompt, _ = read_prompt(args)
    idempotency_key = args.idempotency_key or hashlib.sha256(
        json.dumps(
            {
                "prompt": prompt,
                "size": args.size,
                "quality": args.quality,
                "format": args.output_format,
                "provider": args.provider,
                "source": args.source_asset_id,
            },
            ensure_ascii=False,
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    request = {
        "contractVersion": "1",
        "idempotencyKey": f"skill:{idempotency_key}",
        "input": {
            "prompt": prompt,
            **({"sourceAssetId": args.source_asset_id} if args.source_asset_id else {}),
        },
        "composition": {"ratio": exact_ratio(parsed[0], parsed[1])},
        "generation": {"provider": args.provider, "model": args.model, "apiMode": args.api_mode},
        "output": {
            "ratioMode": "inherit",
            "format": "png",
            "quality": "high",
            "dimensions": args.size,
            "enhancement": args.enhancement,
            "contentClass": args.content_class,
        },
        "retry": {"maxAttempts": args.max_attempts},
    }
    job, response_headers = api_request(args, "/v1/image-jobs", "POST", request)
    deadline = time.monotonic() + max(300, args.max_attempts * 330)
    while job["state"] not in {"succeeded", "failed", "cancelled"}:
        if time.monotonic() >= deadline:
            raise RuntimeError("task API job polling timed out")
        time.sleep(0.25)
        job, _ = api_request(args, f"/v1/image-jobs/{job['id']}")
    if job["state"] != "succeeded":
        raise RuntimeError(f"task API job ended as {job['state']}: {job.get('error')}")

    out_path = Path(args.out)
    source_path = source_path_for(out_path)
    download_asset(args, job["sourceAssetId"], source_path)
    download_asset(args, job["finalAssetId"], out_path)
    source_manifest, _ = api_request(args, f"/v1/assets/{job['sourceAssetId']}?manifest=1")
    final_manifest, _ = api_request(args, f"/v1/assets/{job['finalAssetId']}?manifest=1")
    source_info = png_info(source_path)
    final_info = png_info(out_path)
    if not source_info or not final_info:
        raise RuntimeError("task API did not return valid PNG assets")
    if source_info["width"] * final_info["height"] != final_info["width"] * source_info["height"]:
        raise RuntimeError("source and final ratios differ at integer-pixel precision")
    if (final_info["width"], final_info["height"]) != parsed:
        raise RuntimeError("final dimensions do not match the exact requested target")
    report.update(
        {
            "status": "succeeded",
            "image_job_id": job["id"],
            "idempotency_replayed": response_headers.get("idempotency-replayed") == "true",
            "source": source_info,
            "final": final_info,
            "source_manifest": source_manifest,
            "final_manifest": final_manifest,
            "integer_ratio_exact": True,
        }
    )
    report_path = Path(args.report) if args.report else out_path.with_suffix(".report.json")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> int:
    args = parse_args()
    report = build_report(args)
    if args.backend == "task-api" and not (args.prepare_only or args.dry_run) and report["status"] != "blocked":
        report = execute_task_api(args, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 2 if report["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
