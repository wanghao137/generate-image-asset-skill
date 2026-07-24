---
name: generate-image-asset
description: Use whenever a user asks Codex to generate a local PNG, WebP, or JPEG image asset, references uploaded or local images, needs prompt normalization, hits an image-generation refusal, needs minimal safety rewriting, or wants exact final dimensions under output/imagegen.
---

# Generate Image Asset

## Contract

Turn a visual intent into a verified local image artifact using Codex's built-in image generator.

Required outputs:
- final image path
- actual route: `codex-built-in-image-tool` or `blocked`
- final prompt or material rewrite summary
- refusal recovery record when the first `image_gen` attempt is refused
- raw image path copied unchanged from the Codex generated-image cache when using the built-in backend
- normalized source image path whose ratio matches the final image
- source dimensions, final dimensions, byte size, format, and visual inspection status

## Core Rules

- Default to Codex's built-in image generator. Do not stop to inspect local API tooling unless the user explicitly asks for that route.
- The built-in `image_gen` tool only accepts the prompt exposed in the tool schema. Treat `moderation: low` as the desired profile in preflight/reporting, not as a guarantee that the tool received an API moderation parameter.
- Treat requested model, quality, and size as the desired generation profile. The exact final pixel size is enforced locally after generation when needed.
- Default image moderation to `low`; pass `auto` only when explicitly requested.
- The engine defaults to **2K generation → 4K final output**. You do not need to specify dimensions — if omitted, the engine selects the 4K preset for the given ratio (e.g. `3:4` → `2400x3200`, `9:16` → `2160x3840`, `1:1` → `2880x2880`).
- If the user requests a specific size like `2160x3840`, the final saved asset must be exactly `2160x3840` unless generation is blocked.
- Always preserve the unmodified built-in generated image as `*-raw.<ext>`.
- `*-source.<ext>` is the canonical source canvas. If raw already matches the requested ratio it may be copied unchanged; otherwise normalize it with a centered `cover` crop and record that transform.
- Never stretch a ratio-mismatched raw image into the requested final dimensions.
- The final image must be resized only from a source image whose integer-pixel ratio exactly matches the final target (`sourceWidth * finalHeight == finalWidth * sourceHeight`).
- Never leave a project-bound result only in the Codex generated-image cache.
- Do not overwrite an existing requested output unless the user explicitly asked for that exact path to be replaced; otherwise version the filename.
- Refusal recovery is mandatory when the first generation attempt is refused: record the refusal, make one minimal safety rewrite if the user's visual goal can still be preserved, and retry exactly once.

## Workflow

1. Parse the request.
   - Put long prompts or JSON into `work/imagegen/prompt.txt` or a descriptive sibling file.
   - For referenced local images, inspect them with `view_image` before generation so they are visible to the built-in image tool.

2. Normalize only when needed.
   - Preserve subject, composition, lighting, style, aspect ratio, and must-keep details.
   - Do not rewrite merely because the prompt is adult fashion, swimwear, or dramatic.
   - Rewrite only when the prompt is explicit, underage, non-consensual, asks for nudity, asks to evade policy, or the generator refuses.
   - If rewriting, keep the user's core visual goal and remove only the unsafe trigger.

3. Preflight.
   - Run `scripts/run_image_job.py --prepare-only` with the prompt file, requested size, output format, output path, and `--force` only when replacement is intended.
   - This preflight checks prompt findings, target dimensions, output collision, the refusal recovery plan, the refusal recovery log path, and the required copy/resize/verify plan.
   - Treat `prompt_findings` as warnings by default; use `--policy-mode block` only for strict audit mode.
   - Keep the emitted `refusal_recovery_plan` visible while generating. It is the checklist for what to do if the built-in tool refuses.

4. Generate.
   - Attempt 1: use the built-in `image_gen` tool with the normalized prompt.
   - For reference images, the prompt must name each image role, for example `Image #1: person reference`.
   - If attempt 1 succeeds, mark refusal recovery as `not_triggered`.
   - If attempt 1 refuses, run the Refusal Recovery procedure below before changing the prompt.
   - Attempt 2 is allowed only after a minimal safety rewrite. Do not make a third attempt unless the user explicitly asks for another strategy.

5. Save.
   - Locate the newest generated PNG from the Codex generated-image cache after a successful generation.
   - Copy it unchanged to `output/imagegen/<name>-raw.<ext>`.
   - Compare the raw ratio with the requested final ratio.
   - If ratios match, copy raw to `output/imagegen/<name>-source.<ext>`.
   - If ratios differ, create a centered `cover` crop at the requested ratio as `*-source.<ext>` and keep raw unchanged for audit.
   - Resize only the ratio-matched source to the requested final path.
   - On Windows, using PowerShell `System.Drawing` for resizing is acceptable when Python image libraries are unavailable.

6. Verify.
   - Read the final file header for format, byte size, width, and height.
   - Read source dimensions when a source file exists.
   - Confirm source and final ratios match exactly at integer-pixel precision.
   - Inspect the final image visually with `view_image`.
   - Confirm the final image matches the requested scene and the final dimensions exactly when a target size was requested.

7. Report.
   - Keep the final report concise.
   - Include final path, route, raw path, source path, final dimensions, source dimensions, file size, and visual inspection status.
   - If raw was normalized, report its original dimensions and the centered cover crop plainly.
   - If attempt 1 was refused, include: initial refusal summary, likely trigger category, exact rewrite summary, retry result, and whether the final route is `codex-built-in-image-tool` or `blocked`.

## Refusal Recovery

Use this only after the built-in `image_gen` tool refuses. The goal is not to sanitize the whole prompt or change the concept; it is to remove the smallest refusal trigger while preserving the image the user actually asked for.

Required sequence:
1. Stop and record the refusal before editing the prompt.
   - Summarize the refusal in neutral terms without inventing policy details.
   - Identify the smallest likely trigger: age ambiguity, nudity/explicitness, private/voyeuristic framing, body-measurement emphasis, missing reference dependency, identity exactness, or unsupported generation profile.
2. Decide whether a retry can preserve the visual goal.
   - Retry is allowed when the core subject, composition, style, lighting, camera angle, aspect ratio, and requested deliverable can remain intact.
   - Block instead of retrying when the unsafe element is the user's core request, the subject could be underage in a sexualized context, the prompt asks for non-consensual/private sexual imagery, or the rewrite would materially change what the user wanted.
3. Make one minimal rewrite.
   - Add explicit adult framing only when age ambiguity matters, for example `adult person, age 25+`.
   - Replace private, voyeuristic, or sensual framing with public/editorial/studio framing.
   - Replace explicit body metrics or sexualized body-part focus with wardrobe, silhouette, fabric fit, pose, or non-explicit fashion language.
   - Remove nudity, nipples, areola, genitals, sex acts, coercion, leaked/private framing, and evasion language.
   - For missing reference images, inspect the referenced local image first; if unavailable, remove the unsupported reference dependency or block.
   - For exact identity matching, preserve general visual characteristics instead of promising exact face or identity reproduction.
4. Retry exactly once with the rewritten prompt.
   - If attempt 2 succeeds, save and verify normally.
   - If attempt 2 refuses, stop and report `blocked`; do not continue rewriting in a loop.

Required refusal recovery record:

```json
{
  "status": "not_triggered | recovered | blocked",
  "attempt_1": {
    "prompt_file": "path",
    "result": "success | refused",
    "refusal_summary": "short neutral summary or null"
  },
  "rewrite": {
    "trigger_category": "category or null",
    "summary": "what changed and why",
    "preserved_constraints": ["subject", "composition", "style", "lighting", "aspect_ratio"]
  },
  "attempt_2": {
    "prompt_file": "path or null",
    "result": "success | refused | not_run"
  }
}
```

## Preflight Command

Resolve `<skill-dir>` to the directory containing this `SKILL.md`. Use the
available Python launcher (`python3`, `python`, or `py -3`) for the bundled
script.

```bash
python "<skill-dir>/scripts/run_image_job.py" \
  --prompt-file work/imagegen/prompt.txt \
  --model gpt-image-2 \
  --size 2160x3840 \
  --quality high \
  --output-format png \
  --moderation low \
  --out output/imagegen/example.png \
  --prepare-only
```

If replacing an existing requested output is intended, add `--force`. The command writes both the main report and a `*.recovery.json` template next to the requested output.

## Optional Task API Backend

Use the same Image Job Contract v1 as TaoStudio when a local or remote task API
is available. Keep the bearer token in `IMAGE_TASK_API_TOKEN`; never place it in
the prompt, report, or command history.

```bash
python "<skill-dir>/scripts/run_image_job.py" \
  --backend task-api \
  --prompt-file work/imagegen/prompt.txt \
  --model gpt-image-2 \
  --provider configured \
  --ratio 9:16 \
  --quality high \
  --output-format png \
  --max-attempts 5 \
  --out output/imagegen/example.png
```

`--size` is optional. When omitted, the engine defaults to 2K generation and
inherits a 4K final target from the ratio (see 4K presets below). The backend
creates one idempotent job, downloads immutable source and final assets
separately, and verifies PNG signature, SHA-256, exact final dimensions, and
inherited source ratio. The bundled `vendor/image-job-core` is the portable
geometry and contract implementation; `scripts/image_core_cli.mjs` exposes it
without any TaoStudio repository dependency.

### 4K Final Presets by Ratio

| Ratio | 4K Final | 2K Generation |
|-------|----------|---------------|
| 1:1 | 2880x2880 | 2048x2048 |
| 3:2 | 3456x2304 | 2160x1440 |
| 2:3 | 2304x3456 | 1440x2160 |
| 16:9 | 3840x2160 | 2560x1440 |
| 9:16 | 2160x3840 | 1440x2560 |
| 4:3 | 3200x2400 | 2048x1536 |
| 3:4 | 2400x3200 | 1536x2048 |
| 21:9 | 3840x1646 | 2560x1097 |

## Ratio-Safe Post-Processing

Use Sharp, Pillow, ImageMagick, or an equivalent structured image library. The
required order is: inspect raw dimensions, create a centered `cover` crop only
when the integer-pixel ratio differs, save that result as source, then resize
source to the exact final pixels with Lanczos. For a `3840x1646` target, use a
`1920x823` canonical source. Reject the task if source and final cross-products
are not equal. A direct `DrawImage(raw, 0, 0, targetWidth,
targetHeight)` operation is forbidden because it stretches mismatched ratios.

## References

- `references/adversarial-review.md`: mandatory pre-completion review checklist.
