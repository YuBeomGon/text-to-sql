---
description: Pick the next WBS item and delegate it to the most appropriate subagent
argument-hint: [optional WBS area or note]
---
Read these files in order:
1. `program.md`
2. `docs/wbs_v0.1.md`
3. `docs/harness_design.md`
4. `CLAUDE.md`

Find the next unfinished WBS item, unless the user gave a narrower focus: $ARGUMENTS

Then:
- choose the best matching subagent among `data-eval`, `semantics`, `verifier`, `policy`, and `bench`
- keep the task narrow
- instruct the subagent to touch only its owned area
- require a small change and a `./score.sh --quick` run before handoff back

When the delegated work returns, summarize:
- what was attempted
- what changed
- whether quick score passed
- what the next small step should be
