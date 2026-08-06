---
name: release-note-generation
description: Use when filling `messages/*.txt` release notes from git commits, commit bodies, and pull request metadata since a previous tag.
---

# Release Note Generation

Use this skill when the user asks for a release note or changelog entry in `messages/*.txt`.

If the note is marked with `(Notes not shown on release)`, create only the
`messages/<version>.txt` file.
Do not add a `messages.json` entry for that version.
If the note should appear on release, add the new `messages/<version>.txt`
file to `messages.json`.

## Goal

Turn the commit range since the previous release into a concise release note that matches the existing messages style.

Prefer the smallest useful summary.
Include only user-facing changes, not maintenance noise unless the project already records that kind of change.

## Workflow

1. Identify the release range.
   Use the previous version tag or release file as the lower bound.
   Example: `git log v3.6.2..HEAD`.
2. Parse commit subjects and bodies.
   The subject usually gives the section and the main change.
   The body often contains the actual user-facing detail, the rationale, or issue references.
3. Treat `(#123)` in a commit subject as a squash-merged pull request number.
   That suffix usually refers to the PR that landed the commit, not to an issue.
   If the commit is part of a merge tree instead of a squash merge, trace the merge commit or PR metadata to find the originating merge request number and use that number in the note.
4. Fetch pull request metadata when needed.
   Use `gh pr view <number>` only for reading metadata.
   Do not create, edit, merge, or close anything with `gh`.
5. Check the milestone for the target release version.
   Look for the respective milestone that matches the version being released, then review the issues and pull requests assigned to that milestone as a reference list.
   Use it to spot missing user-facing changes, confirm issue numbers, and cross-check the release range.
   Treat the milestone as a reference, not as a replacement for the commit and PR history.
6. Collect referenced issues.
   If the PR body or commit body says `Fixes #123`, `Closes #123`, or `Resolves #123`, include those issue numbers in the release note too.
   Those issue numbers are separate from the PR number in `(#123)`.
7. Match the existing file style.
   Preserve the current headings, bullet style, and contributor format in the target `messages/*.txt` file.

## What to extract

For each meaningful commit or PR:

- Section or subsystem name, such as `Syntax`, `Settings`, or `Commands`.
- Short action summary.
- PR number from `(#123)` when present.
- Issue numbers referenced in the commit body or PR body.
- Author handle or name in the existing note style.

## How to infer more detail

Prefer these sources in order:

1. Commit subject.
2. Commit body.
3. PR title and PR body via `gh pr view`.
4. Referenced issues from the PR body or linked timeline items.

Useful inference rules:

- A squash-merged commit with `(#123)` at the end generally maps to PR `123`.
- A commit body that mentions what changed is often better release-note text than the subject alone.
- `Fixes #123`, `Closes #123`, and `Resolves #123` should be copied into the release note as issue references.
- If a PR fixed several issues, include all of them if they are relevant and easy to verify.
- If a PR title is too vague, use the body and the linked issues to write the note.
- If multiple commits describe the same feature, collapse them into one bullet.

## Style

Follow the project’s existing messages style.

- Keep bullets short.
- Mention authors and issue numbers in parentheses when that is the local convention.
- Use the same capitalization and section naming patterns already present in nearby release files.
- Do not add filler prose unless the existing file style does.

## Verification

Before writing the file:

- Review the commit range with author and body output.
- Inspect the target `messages/*.txt` file and nearby versions for formatting.
- Check that every included PR number and issue reference actually appears in a commit body, PR body, or linked metadata.
- If the resulting note should appear on release, verify that `messages.json` includes the new file.
- If the resulting note is hidden on release, verify that `messages.json` was not changed.

## `gh` usage rules

- Read-only metadata only.
- Safe commands include `gh pr view`, `gh pr list`, and `gh issue view`.
- Do not use `gh` to modify repository state.
- If the PR metadata is unavailable, fall back to the commit body and git log.
