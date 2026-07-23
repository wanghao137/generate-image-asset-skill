# Adversarial Review

Run this before reporting success.

## Critical

- Prompt policy: Would the prompt still be refused because it sexualizes, privatizes, or body-emphasizes an adult subject? If yes, rewrite or stop.
- Age ambiguity: Could the subject be read as underage? If yes, add adult age framing or stop if sexualized.
- Consent/privacy: Does the scene imply hidden, leaked, voyeuristic, coerced, or private sexual imagery? If yes, rewrite or stop.
- Body emphasis: Does the prompt specify bust size, cup/implant volume, nipples, areola, cleavage, or other sexualized measurements? If yes, record it as a refusal risk and remove it only if the provider refuses or the request becomes explicit.
- Reference dependency: Does a generate-only job mention uploaded images, face references, clothing references, or identity preservation without an inspected input image? If yes, inspect the local image first or block.
- Refusal recovery: If attempt 1 was refused, is there a recorded refusal summary, likely trigger category, minimal rewrite summary, and attempt 2 result? If no, do not report completion.
- Secrets: Did any command, report, or chat output reveal credentials, cookies, tokens, or bearer strings? If yes, rotate and clean up before continuing.
- False success: Is there an actual image file at the reported final path? If no, do not claim success.

## High

- Wrong route: Did the agent use anything other than Codex's built-in image tool without an explicit user request? If yes, correct the workflow.
- Source preservation: Was the unmodified generated image copied to `*-source.<ext>` before resizing? If no, fix it before reporting success.
- Exact dimensions: If the user requested `2160x3840`, does the final file header read exactly `2160x3840`? If no, resize or report the blocker.
- Output overwrite: Would the workflow overwrite an existing file without explicit intent? If yes, version the filename or require explicit replacement.
- Visual mismatch: Does visual inspection fail must-keep constraints? If yes, regenerate or report the mismatch.
- Cache-only result: Is the only usable image still in the Codex generated-image cache? If yes, copy it into the requested workspace path.
- Retry limit: Did the agent make more than one safety rewrite retry after a refusal without explicit user approval? If yes, stop and report the overrun.

## Medium

- Provenance: Are source and final paths recorded when copying or resizing?
- Source/final dimensions: If a generated image was resized, are both source dimensions and final dimensions reported?
- Prompt drift: Did safety rewriting remove the actual user goal rather than only unsafe wording?
- Text rendering: If text is requested, is exact text checked visually?
- Geometry: For reference-image or ride/product shots, are hands, faces, seat restraints, reflections, and random letters checked?

## Pass Criteria

Pass only when critical issues are resolved, high issues are resolved or explicitly reported as blockers, and any medium limitations are named briefly.
