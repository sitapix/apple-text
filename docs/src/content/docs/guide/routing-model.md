---
title: "Routing Model"
sidebar:
  order: 7
---

Use this page when you are routing a prompt and want a simple decision model instead of a full catalog scan.

Apple Text uses progressive disclosure: start broad, then move to the narrowest skill that matches the job.

## Routing Pattern

1. Start with `/apple-text:ask`.
2. Decide whether the user needs a workflow, a diagnosis, a choice, or a reference.
3. Open the narrowest skill that matches that answer shape.

Do not memorize every skill name. Ask whether the prompt is broad, broken, comparative, or already scoped to a subsystem.

## Mental Model

- **Broad intake**: start with `/apple-text:ask`.
Use this when the problem is clearly Apple text work but still mixed or underspecified.
- **Guided flow or review**: start with `/skill apple-text-audit`.
Use this when the user wants an audit, integration walkthrough, or step-by-step implementation path.
- **Broken behavior**: start with `/skill apple-text-textkit-diag`.
Use this when the user starts with stale layout, fallback, crashes, or rendering bugs.
- **Tradeoff question**: use `apple-text-views`, `apple-text-attributed-string`, `apple-text-layout-manager-selection`.
Use this when the main job is picking the right API, architecture, or view.
- **Known API family**: start with `/skill apple-text-storage` or the matching reference skill.
Use this when the user already knows the subsystem and wants mechanics, behavior, or API detail.

## Prompt Patterns

- "Why is this editor broken?" -> diagnostic skill
- "Review this code for risks." -> workflow skill
- "Should I use A or B?" -> decision skill
- "How does this Apple text API behave?" -> reference skill

## Shortcuts

- Broad Apple text question -> [`apple-text`](/skills/apple-text/)
- Findings-first review -> [`apple-text-audit`](/skills/apple-text-audit/)
- Debugging a broken editor -> [`apple-text-textkit-diag`](/skills/apple-text-textkit-diag/)
- Choosing among text stacks -> [`apple-text-views`](/skills/apple-text-views/)

## Read Next

- [Quick Start](/apple-text/guide/quick-start/)
- [Entry Points](/apple-text/guide/entry-points/)
- [Problem Routing](/apple-text/guide/problem-routing/)
