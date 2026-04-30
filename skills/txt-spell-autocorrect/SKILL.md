---
name: txt-spell-autocorrect
description: Configure spell checking, autocorrect, smart substitutions, and inline prediction on UITextView and NSTextView, drive UITextChecker and NSSpellChecker directly, and avoid the UITextInteraction correction trap that breaks corrections in custom UITextInput views. Use when spell-check underlines are missing or wrong, autocorrect doesn't apply, completions are needed, code editors need spell-check disabled. Trigger on 'red squiggle', 'autocorrect', 'spell-check', 'predictive text', 'why isn't my correction working' even without formal API names. Continue trigger:, or a custom editor is being told it can't ship with system spell-check because the correction tap routes through private API.
license: MIT
---

# Spell Checking and Autocorrect

Authored against iOS 26.x / Swift 6.x / Xcode 26.x.

This skill covers the configuration knobs on stock text views, the `UITextChecker`/`NSSpellChecker` services for custom logic, and the gotcha that derails almost every custom-`UITextInput` editor: the correction popover invokes a private API (`UITextReplacement`) to apply selected suggestions, so a fully-custom view can show red underlines but cannot apply the correction without rejection-grade private symbols. Before claiming a specific autocorrect property, fetch the current API via Sosumi (`sosumi.ai/documentation/uikit/uitextinputtraits`) — the trait set has grown across iOS 17, 18, and 26.

If the user's editor is `UITextView` or `NSTextView`, the work is almost always configuration. If it's a custom `UITextInput` view, the answer is structurally different and the trap section below matters more than the configuration section.

## Contents

- [Stock view configuration](#stock-view-configuration)
- [The UITextInteraction correction trap](#the-uitextinteraction-correction-trap)
- [UITextChecker](#uitextchecker)
- [NSSpellChecker on macOS](#nsspellchecker-on-macos)
- [How autocorrect actually wires up](#how-autocorrect-actually-wires-up)
- [Platform differences](#platform-differences)
- [Common Mistakes](#common-mistakes)
- [References](#references)

## Stock view configuration

`UITextView` and `NSTextView` get spell check, autocorrect, smart quotes/dashes, and (on iOS 17+) inline prediction for free. Configuration is via properties.

```swift
// iOS — UITextInputTraits
textView.spellCheckingType = .yes        // .default | .no | .yes
textView.autocorrectionType = .yes
textView.autocapitalizationType = .sentences
textView.smartQuotesType = .yes
textView.smartDashesType = .yes
textView.smartInsertDeleteType = .yes
textView.inlinePredictionType = .yes     // iOS 17+

// macOS — explicit per-feature toggles
textView.isContinuousSpellCheckingEnabled = true
textView.isGrammarCheckingEnabled = true              // macOS only
textView.isAutomaticSpellingCorrectionEnabled = true
textView.isAutomaticQuoteSubstitutionEnabled = true
textView.isAutomaticDashSubstitutionEnabled = true
textView.isAutomaticTextReplacementEnabled = true
textView.isAutomaticTextCompletionEnabled = true
textView.isAutomaticLinkDetectionEnabled = true
textView.isAutomaticDataDetectionEnabled = true
```

For code editors, the right configuration is "disable everything that mangles literal text":

```swift
// iOS
textView.spellCheckingType = .no
textView.autocorrectionType = .no
textView.autocapitalizationType = .none
textView.smartQuotesType = .no
textView.smartDashesType = .no
textView.smartInsertDeleteType = .no
textView.inlinePredictionType = .no

// macOS
textView.isContinuousSpellCheckingEnabled = false
textView.isAutomaticSpellingCorrectionEnabled = false
textView.isAutomaticQuoteSubstitutionEnabled = false
textView.isAutomaticDashSubstitutionEnabled = false
textView.isAutomaticTextReplacementEnabled = false
textView.isAutomaticTextCompletionEnabled = false
```

Trait changes on iOS only take effect when the view is *not* first responder. If users see no change after toggling `autocorrectionType`, resign first responder, change the trait, then become first responder again.

## The UITextInteraction correction trap

This is the part of the skill most worth slowing down for.

A custom view that adopts `UITextInput` and adds a `UITextInteraction` will get spell-check underlines for free. The system detects misspellings, draws red underlines, and shows a correction popover when the user taps an underlined word. So far so good.

The trap is what happens when the user taps a suggestion in that popover. The popover dispatches the correction through `UITextReplacement` — a private API. A fully custom view has no public way to receive that callback. The result:

- Underlines render correctly.
- The correction popover appears correctly.
- Tapping a suggestion does nothing visible, or crashes deep inside the input pipeline.
- Calling the private API to fix it is App Store rejection bait.

There are three workable responses. First, disable the system spell check on your custom view (`spellCheckingType = .no`, `autocorrectionType = .no`) and run your own checker UI built on `UITextChecker`. Second, leave system check enabled but accept that inline corrections won't apply on iOS — users use the system Spelling panel on macOS, and on iOS they edit by hand. Third, abandon the custom view and use `UITextView`, which has the private bridging that custom views lack.

For the build-your-own path:

```swift
let checker = UITextChecker()
let nsText = text as NSString
let range = NSRange(location: 0, length: nsText.length)
let misspelled = checker.rangeOfMisspelledWord(
    in: text, range: range, startingAt: 0,
    wrap: false, language: "en"
)
if misspelled.location != NSNotFound {
    let guesses = checker.guesses(forWordRange: misspelled,
                                  in: text, language: "en") ?? []
    presentCustomCorrectionUI(at: misspelled, guesses: guesses)
}
```

Custom correction UI applies the replacement through your normal edit path, so undo, autocorrect, and `inputDelegate` notifications all flow correctly.

## UITextChecker

`UITextChecker` is a standalone, view-independent spell checker. It works on iOS and macOS. Use it for find-misspelled-word loops, custom autocomplete, and the build-your-own path above.

```swift
let checker = UITextChecker()

// Misspelled word scan
var offset = 0
let nsText = text as NSString
let fullRange = NSRange(location: 0, length: nsText.length)

while offset < nsText.length {
    let r = checker.rangeOfMisspelledWord(in: text, range: fullRange,
                                          startingAt: offset, wrap: false, language: "en")
    if r.location == NSNotFound { break }
    let word = nsText.substring(with: r)
    let guesses = checker.guesses(forWordRange: r, in: text, language: "en") ?? []
    print("'\(word)' → \(guesses)")
    offset = r.location + r.length
}

// Word completion (alphabetical despite the docs)
let completions = checker.completions(
    forPartialWordRange: NSRange(location: 0, length: 4),
    in: "prog", language: "en"
) ?? []
```

The `completions` API is documented as ranking by probability; it actually returns alphabetical order. If your UI claims "best suggestion first," you have to do that ranking yourself.

User dictionary additions persist across launches:

```swift
UITextChecker.learnWord("SwiftUI")
UITextChecker.hasLearnedWord("SwiftUI")   // true
UITextChecker.unlearnWord("SwiftUI")
```

Per-document ignore lists need a tag:

```swift
let tag = UITextChecker.uniqueSpellDocumentTag()
checker.ignoreWord("xyzzy", inSpellDocumentWithTag: tag)
```

## NSSpellChecker on macOS

The macOS spell checker is a singleton and significantly more capable than `UITextChecker`. It supports grammar checking, async batch checks, and a unified check that bundles spelling, grammar, and data detection.

```swift
let spell = NSSpellChecker.shared

// Async, large-document checking
let tag = NSSpellChecker.uniqueSpellDocumentTag()
spell.requestChecking(
    of: text,
    range: NSRange(location: 0, length: (text as NSString).length),
    types: NSTextCheckingAllTypes,
    options: nil,
    inSpellDocumentWithTag: tag
) { _, results, _, _ in
    DispatchQueue.main.async { self.applyResults(results) }
}
```

For a custom AppKit view, you can set the spelling state attribute on a range and the system draws the misspelling underline:

```swift
textView.setSpellingState(NSSpellingStateSpellingFlag, range: misspelledRange)
```

Close document tags when the document closes — they hold per-document ignore lists in memory:

```swift
spell.closeSpellDocument(withTag: tag)
```

`NSSpellChecker` itself is main-thread-only despite the async-feeling `requestChecking` callback. Treat it as you would a UI singleton.

## How autocorrect actually wires up

For a custom `UITextInput` view to get autocorrect at all, four things have to be true:

1. The view exposes `UITextInputTraits` properties (`spellCheckingType`, `autocorrectionType`) that are `.yes` or `.default`.
2. The view calls `inputDelegate?.textWillChange(self)` and `textDidChange(self)` around every text mutation, and `selectionWillChange(self)` / `selectionDidChange(self)` around every selection change. Skipping these silently desyncs the autocorrect cache — there's no error and no crash, autocorrect just stops surfacing suggestions.
3. `caretRect(for:)` and `firstRect(for:)` return correct geometry. The autocorrect bubble and spell-check popover are positioned by these rects.
4. A `UITextInteraction` is added to the view. The interaction supplies the gesture recognizers that trigger the correction popover.

When autocorrect "stops working" in a custom view, walk this list. Trait wrong, inputDelegate skipped, geometry wrong, or interaction missing — almost always one of those four. (And if all four are right, the correction trap above kicks in.)

## Platform differences

| Capability | iOS UITextView | macOS NSTextView |
|---|---|---|
| Continuous spell check | `spellCheckingType` enum | `isContinuousSpellCheckingEnabled` Bool |
| Grammar check | not exposed | `isGrammarCheckingEnabled` |
| Mark a range misspelled | not exposed | `setSpellingState(_:range:)` |
| Async batch check | not exposed | `requestChecking(...)` |
| Spelling panel | not exposed | `orderFrontSpellingPanel(_:)` |
| Substitutions panel | not exposed | `orderFrontSubstitutionsPanel(_:)` |
| Inline prediction | iOS 17+ trait | not exposed |
| Spell-check pre-existing text | only near edits | full document |

The grammar/panel features simply don't exist on iOS. If a feature in this table is iOS-blank, it isn't a missing API call — it's not a public capability.

## Common Mistakes

1. **Building a custom UITextInput editor and assuming spell check will "just work."** Underlines render but corrections don't apply (private API trap). Either disable system spell check and build your own, or use `UITextView`.

2. **Skipping `inputDelegate` will/did notifications.** Autocorrect goes silent with no error. The system's cache drifts out of sync with your storage, so the correction engine has nothing useful to suggest.

3. **Changing autocorrect traits while the view is first responder.** No effect. Resign first responder, change the trait, then become first responder again.

4. **Treating `completions(forPartialWordRange:)` as probability-ranked.** It returns alphabetical order. Rank in your own UI if you need "best first" behavior.

5. **Code editor with spell check on.** Variable names get red underlines, autocorrect helpfully turns `let` into `Let`, and smart quotes break string literals. For code editors, disable every trait that rewrites characters.

6. **Forgetting `closeSpellDocument(withTag:)` on macOS.** The ignore list for that document stays in `NSSpellChecker.shared` until the process exits.

7. **Calling `NSSpellChecker` from a background thread.** It's main-thread-only. The async-looking `requestChecking` is a wrapper; you still consume results on main.

8. **Expecting iOS to spell-check the whole document on load.** iOS only checks near the editing cursor. macOS checks the full document. If the user pastes a wall of text on iOS and expects red underlines everywhere, that's not how the iOS engine runs.

## References

- `txt-uitextinput` — full UITextInput protocol surface, `inputDelegate` notifications, the marked-text lifecycle that autocorrect coordinates with
- `txt-selection-menus` — `UITextInteraction` setup, edit menu, gesture coordination
- `txt-view-picker` — picker between custom UITextInput, UITextView, and SwiftUI text fields
- [UITextChecker](https://sosumi.ai/documentation/uikit/uitextchecker)
- [NSSpellChecker](https://sosumi.ai/documentation/appkit/nsspellchecker)
- [UITextInputTraits](https://sosumi.ai/documentation/uikit/uitextinputtraits)
