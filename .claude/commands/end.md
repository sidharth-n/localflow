---
description: Wrap up the localflow session — update SESSION.md, commit, and push.
---

End-of-session protocol. Do these in order.

**1. Update `SESSION.md`:**
- Move anything from "In progress" that was finished this session into "Completed ✅".
- Move anything newly started from "Next up" into "In progress 🔄".
- Add newly-discovered work items to "Next up" at the right priority.
- Bump "Last updated" to today's date.
- Bump "Active milestone" if it changed.
- Append a new entry under "Session log 📝" with today's date and a 3–5 bullet summary of what actually happened (concrete, not vague — name files touched, decisions made, numbers measured).

**2. Update `knowledge-base/` if warranted:**
- If any non-trivial research, benchmark, or design decision happened this session, add or extend a file under `knowledge-base/`. Keep each file focused on one topic.

**3. Review changes before committing:**
- Run `git status` and `git diff` — surface anything surprising to the user.
- If there are unrelated untracked files, ask the user before staging them.

**4. Commit and push:**
- Stage the changed files explicitly (no `git add -A`).
- Commit message format: `<type>: <short summary>` where type is one of feat, fix, docs, chore, refactor, test. Body should be 1–3 bullets of what changed. End with the standard Co-Authored-By line for Claude.
- Push to `origin main`.

**5. Report:**
- Final summary to the user: what was committed, pushed, and the next item ready to go at `/start`. Keep it to 3–5 lines.

If any step blocks (e.g. merge conflict, push rejected, hook failure), stop and ask — do not force-push, do not skip hooks.
