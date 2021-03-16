#!/bin/bash
echo -e "removing execute from pre-commit hook"
chmod -x ./.git/hooks/pre-commit
echo -e "committing with --amend --no-edit"
git commit --amend --no-edit
echo -e "restoring execute from pre-commit hook"
chmod +x ./.git/hooks/pre-commit
