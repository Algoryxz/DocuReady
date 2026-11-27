# Git Publishing Workflow & Remote Synchronization Guide

**Repository:** `Algoryxz/DocuReady`  
**Purpose:** Standardized developer guide for publishing local Git work to GitHub, configuring branch tracking, avoiding detached HEAD states, and safely merging feature work into `main`.

---

## 1. Why Local Work Previously Did Not Appear on GitHub

During repository forensics across Loops 01–47, five root causes were identified that caused local development work to remain unpublished:

1. **Explicit Restraint / Permission Boundary:** Autonomous agents operate under strict safety rules that forbid pushing or publishing to remotes without explicit Product Owner authorization. When local commits were made, `git push` was intentionally withheld pending explicit qualification.
2. **Missing Upstream Tracking:** Local branches (such as `loop-01` through `loop-47`) were branched locally without `-u` or `--set-upstream origin <branch>`. Git did not configure a default push target (`branch.<name>.remote` was unset).
3. **Branch Pushing vs Main Merging:** Pushing a topic/feature branch (e.g. `loop-47`) publishes that specific branch ref to GitHub, but **does not automatically update `origin/main`**. Updating `main` requires a Pull Request or a fast-forward merge onto `main`.
4. **Isolated Worktrees:** Development performed across multiple worktrees (e.g., `wt-integration`, `wt-sync`) creates commits on separate HEADs. If commits are made on an isolated worktree branch, they are not reflected on the root working tree or remote until explicitly pushed.
5. **Dual Repository Roots:** An early prototype history (`22377d5`) was preserved on local `main` while remote `origin/main` tracked the modern package architecture (`ba09593` -> `392ce9a` -> `75aa130`). Without upstream synchronization, local `main` remained on the orphan commit.

---

## 2. Standard Publishing Workflow

Always follow this exact four-step sequence when working on features or bugfixes:

### Step 1: Check Working Tree & Branch
Verify current branch and staged files:
```bash
git status
```
Ensure you are on a named branch (never detached HEAD).

### Step 2: Stage Intended Files
Stage only intended source, test, or documentation files (never secrets or scratch artifacts):
```bash
git add <intended-files>
```

### Step 3: Commit with Conventional Commit Format
Write clear, conventional commit messages:
```bash
git commit -m "type(scope): description"
```
Examples: `feat(ocr): ...`, `fix(desktop): ...`, `docs(governance): ...`, `test(rules): ...`.

### Step 4: Publish to GitHub with Upstream Tracking
On the first push of a new branch, establish upstream tracking:
```bash
git push -u origin HEAD
```
For all subsequent commits on that branch:
```bash
git push
```

---

## 3. Merging into Main via Pull Request

Pushing a feature branch publishes your work to GitHub, but does not modify `main`. To integrate into `main`:

1. Open a Pull Request targeting `main`:
   ```bash
   # Using GitHub CLI:
   gh pr create --base main --head <your-branch> --title "type(scope): description" --body "..."
   ```
2. Await CI checks and review verification.
3. Merge the Pull Request on GitHub (or via `gh pr merge --squash` / `gh pr merge --merge`).
4. Pull the updated `main` into your local workspace:
   ```bash
   git checkout main
   git pull origin main
   ```

---

## 4. Worktree Guidelines

When using Git worktrees for isolated development:
- Every worktree must point to a dedicated branch (e.g., `git worktree add -b <branch-name> <path> <base-ref>`).
- Always verify your current working directory and checked-out branch before running `git commit` or `git push`.
- When work in a worktree is complete and pushed, remove the worktree safely:
  ```bash
  git worktree remove <path>
  ```
