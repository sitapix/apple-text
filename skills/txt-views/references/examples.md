# Text View Selection Examples

These examples show the kinds of questions this skill should answer cleanly.

## Example 1: SwiftUI Enough?

**User prompt**

```text
I need a multi-line notes field in SwiftUI. It does not need rich text, attachments, or syntax highlighting.
```

**Good answer shape**

- Recommend `TextEditor`
- Call out plain-text limitation up front
- Mention `UITextView` only as the escalation path if requirements grow

## Example 2: Rich Text Escalation

**User prompt**

```text
Should this be TextEditor or UITextView if I need inline images and custom paragraph styles?
```

**Good answer shape**

- Recommend `UITextView`
- Explain that `TextEditor` is not the right tool for rich attributed editing
- Mention TextKit 2 if the user also needs modern layout APIs or Writing Tools support

## Example 3: macOS-Specific Capability

**User prompt**

```text
I am building a macOS document editor and need rulers, text tables, and printing. What should I use?
```

**Good answer shape**

- Recommend `NSTextView`
- Call out AppKit-only editing surface area
- Route to `/skill txt-appkit-vs-uikit` if the user is comparing an iOS port

## Example 4: Chat Composer

**User prompt**

```text
I want an iMessage-style composer that starts as one line and grows to four lines.
```

**Good answer shape**

- Recommend `TextField(axis: .vertical)` first
- Mention `lineLimit` options
- Escalate to `UITextView` only if richer editing control is needed

## Example 5: Code Editor

**User prompt**

```text
I need syntax highlighting, custom selection behavior, and layout queries in an editor.
```

**Good answer shape**

- Recommend `UITextView` / `NSTextView`
- Explain why TextKit-backed views are required
- Route to `/skill txt-textkit2` or `/skill txt-textkit1` based on API needs
