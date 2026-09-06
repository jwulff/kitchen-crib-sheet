---
name: private-to-oss
description: Turn a working private agent skill into a distributable open-source skill, separating personal context from reusable behavior and tracking release evidence.
---

# Private to OSS

Start from the working skill and the user's intended public audience. Preserve useful behavior and lessons from real use. Do not copy a private directory wholesale or import its Git history.

Create a release record from [references/release-record.md](references/release-record.md) in the user's private project notes. Update it as decisions and evidence accumulate. Keep private source paths and excluded information in that private record, outside the public tree.

## Extract the reusable workflow

Read the skill, its referenced resources, scripts, and recent task history. Separate:

- Stable behavior: what the skill helps someone do, its fragile invariants, and how success is checked.
- Configuration: source/output paths, time zone, paper size, accounts, host-specific tools.
- Personal material: names, recipes or other corpus, vault links, identifiers, tokens, local history, screenshots, and generated files.

Carry the behavior forward, make necessary configuration explicit, and use a small synthetic example. Include personal examples only within the user's authorized sharing scope. A finished artifact approved for sharing does not authorize publishing all of its source notes.

## Package and exercise

Build in a fresh directory. Keep `SKILL.md` focused on decisions and route setup or schemas into supporting files only where useful. Include installation instructions, a license for original work, and notices for third-party assets. Inspiration is not a license to copy code, prompts, fonts, or media.

Replace private integrations with optional adapters or ordinary file outputs. Avoid requiring the creator's machine or services for the core workflow. Keep secrets in runtime configuration when an integration genuinely needs them, never in examples.

Test from a clean copy using only documented dependencies. Exercise a normal request and a meaningful failure case. Verify generated output, not just script exit status. Track tested platforms honestly. Preserve the last good artifact when a new build fails, and distinguish preview mode from a completed release.

Review both the public working tree and the exact Git archive or release ZIP: credentials, personal paths, private URLs/IDs, source notes, PDF metadata, binary assets, symlinks, and accidental history. Confirm that every bundled asset has a distributable license. Record findings and fixes, rather than treating a clean pattern scan as proof of privacy.

## Release and handoff

Honor any publication authorization already in the conversation. Without it, finish a reviewable local repository and distribution package. With it, publish to the named owner/repository, then check the public files, fresh-clone setup, tests, and release links. Do not publish unrelated private repositories or downstream blog posts by implication.

Update the private release record with repository URL, release tag/commit, artifact hashes, validation evidence, remaining limitations, and the maintenance relationship between private and public skills. Return the usable skill and concrete links, distinguishing published work from drafts.
