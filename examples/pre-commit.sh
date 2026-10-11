#!/usr/bin/env bash
# Save as .git/hooks/pre-commit (chmod +x). Blocks commits that add skill errors.
set -e
claude-skill-lint check .claude/skills --fail-on error
