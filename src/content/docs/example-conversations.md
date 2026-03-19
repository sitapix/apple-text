---
title: "Example Conversations"
description: "Routing smoke tests and example interactions for the Apple Text plugin."
---

Use this page when you want to see how the public entry points should feel in practice.

> Treat these as routing smoke tests and as examples of the tone the plugin should support. Each linked skill name goes to the actual skill page so you can inspect the target surface directly.

## Ask Command

**User**

```text
/apple-text:ask Why is my NSTextView rendering stale after I mutate the backing storage?
```

**Expected behavior**

- Routes to [`apple-text-layout-invalidation`](/skills/apple-text-layout-invalidation/), [`apple-text-storage`](/skills/apple-text-storage/), or [`apple-text-textkit-diag`](/skills/apple-text-textkit-diag/)
- Does not require the user to know plugin internals
- Keeps the answer on Apple text layout mechanics rather than generic editor advice

> Why this matters: the plain-language command should absorb ambiguity and route cleanly without forcing the user to learn the catalog first.

## Router

**User**

```text
Use apple-text and explain why my UITextView lost TextKit 2.
```

**Expected behavior**

- Routes to [`apple-text-fallback-triggers`](/skills/apple-text-fallback-triggers/) or [`apple-text-textkit-diag`](/skills/apple-text-textkit-diag/)
- Explains fallback triggers first
- Avoids drifting into generic SwiftUI guidance

> Why this matters: the router should compress the taxonomy, not repeat it.

## View Selection

**User**

```text
Use apple-text-views and tell me whether this should be TextEditor or UITextView.
I need syntax highlighting and inline attachments.
```

**Expected behavior**

- Chooses `UITextView`
- Explains why `TextEditor` is not enough
- Points to [`apple-text-representable`](/skills/apple-text-representable/) if the user is in SwiftUI
- Keeps the choice concrete instead of listing every possible text surface

> Why this matters: decision skills should answer the choice directly and only then pull in supporting skills.

## Audit Workflow

**User**

```text
Use apple-text-audit on Sources/Editor and list the highest-risk issues first.
```

**Expected behavior**

- Delegates to [`textkit-auditor`](/agents/)
- Returns findings by severity with file references
- Calls out fallback triggers, editing lifecycle issues, and deprecated APIs

> Why this matters: review flows should produce findings, not a tutorial.

## Writing Tools

**User**

```text
Use apple-text-writing-tools and show how to keep code blocks out of Writing Tools rewrites.
```

**Expected behavior**

- Focuses on Writing Tools APIs and ignored ranges
- Does not turn into a generic AI feature explanation
- Links protected-range guidance back to [`apple-text-writing-tools`](/skills/apple-text-writing-tools/)

> Why this matters: this plugin should stay on editor implementation details even when the feature touches AI.

## Representable Bridge

**User**

```text
Use apple-text-representable and fix cursor jump in my SwiftUI wrapper around UITextView.
```

**Expected behavior**

- Focuses on coordinator/update cycle issues
- Mentions state synchronization and selection preservation
- Links to the specialist workflow instead of stopping at broad SwiftUI framing

> Why this matters: wrapper problems should stay wrapper-shaped, not collapse into generic SwiftUI advice.

## Coverage Map

- Broad intake: [`/apple-text:ask`](/commands/), [`apple-text`](/skills/apple-text/)
- Decision paths: [`apple-text-views`](/skills/apple-text-views/), [`apple-text-layout-manager-selection`](/skills/apple-text-layout-manager-selection/)
- Workflow paths: [`apple-text-audit`](/skills/apple-text-audit/), [`apple-text-writing-tools`](/skills/apple-text-writing-tools/), [`apple-text-representable`](/skills/apple-text-representable/)
