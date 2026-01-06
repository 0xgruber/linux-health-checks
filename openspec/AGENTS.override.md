# openspec/AGENTS.override.md

## Strict Git Workflow

### 1. After Completing a Phase
**Trigger:** When a specific "Phase" in `tasks.md` is complete and tests pass.
**Action:**
1. `git add .`
2. `git commit -m "feat: completed phase <number>: <description>"`

### 2. After Completing the Proposal
**Trigger:** When **all** phases and tasks are complete.
**Action:**
1. `git push`
2. Notify user: "Proposal complete. Changes pushed to remote."
