---
name: txt-accessibility
description: Wire VoiceOver, accessibility traits, UIAccessibilityReadingContent, accessibilityTextualContext, and announcement notifications into custom or wrapped Apple text editors. Use when a UIViewRepresentable wrapper shadows a UITextView's accessibility, a custom text view doesn't appear in the accessibility tree, VoiceOver reads stale text or skips punctuation in a code editor, programmatic edits aren't announced, or rotor gestures don't navigate by character/word/line. Trigger on 'screen reader', 'VoiceOver', 'blind users', 'WCAG', or 'accessibility audit' even when traits and rotor aren't explicitly named. Do NOT use for Dynamic Type font scaling and content-size category — see txt-dynamic-type.
license: MIT
---

# Accessibility for Custom Text Editors

Authored against iOS 26.x / Swift 6.x / Xcode 26.x.

This skill covers the accessibility surface that text editors specifically need: keeping `UITextView`'s built-in accessibility intact when wrapping it in SwiftUI, declaring traits and value on a from-scratch text view, adopting `UIAccessibilityReadingContent` so VoiceOver's text-navigation rotor works, choosing the right `accessibilityTextualContext` so prose vs code vs chat are read correctly, and posting announcements when programmatic changes happen. The patterns here are clues, not answers — before claiming any specific accessibility property exists or behaves a particular way, open the actual view code and verify the configuration, and fetch the current docs via Sosumi (`sosumi.ai/documentation/uikit/uiaccessibility`) for any signature you're not certain about.

For Dynamic Type — text scaling, `UIFontMetrics`, content-size category notifications, AX size testing — see `txt-dynamic-type`. The boundary is intentional: this skill is about VoiceOver and trait wiring; that one is about size scaling.

## Contents

- [What stock text views give you](#what-stock-text-views-give-you)
- [SwiftUI representable wrappers](#swiftui-representable-wrappers)
- [Custom text views from scratch](#custom-text-views-from-scratch)
- [UIAccessibilityReadingContent](#uiaccessibilityreadingcontent)
- [accessibilityTextualContext](#accessibilitytextualcontext)
- [Announcing programmatic changes](#announcing-programmatic-changes)
- [Accessibility Inspector checks](#accessibility-inspector-checks)
- [Common Mistakes](#common-mistakes)
- [References](#references)

## What stock text views give you

`UITextView` and `NSTextView` are accessible by default. They report as static text or as an editable text field depending on `isEditable`, expose their text content as the accessibility value, support the rotor's character/word/line/heading navigation, and announce typing through the text input system. If a stock text view is silent in VoiceOver, the cause is upstream — a parent `isAccessibilityElement = false` shadowing the subtree, an overlay view obscuring it, or `accessibilityElementsHidden = true` on an ancestor — not the view itself.

Programmatic changes (insertions from autocomplete, clipboard pastes you trigger, formatting commands) are not auto-announced. Stock views announce only what flows through the input system. See "Announcing programmatic changes" below.

## SwiftUI representable wrappers

The most common failure is a `UIViewRepresentable` wrapper that accidentally replaces the `UITextView`'s accessibility subtree. SwiftUI generates an accessibility element for the representable container; if you set `.accessibilityLabel`/`.accessibilityValue` on the SwiftUI side, the SwiftUI element shadows the UIKit view's dynamic accessibility behavior.

```swift
// WRONG — replaces UITextView's dynamic accessibility
EditorView()
    .accessibilityLabel("Editor")

// CORRECT — set on the UITextView itself
struct EditorView: UIViewRepresentable {
    func makeUIView(context: Context) -> UITextView {
        let tv = UITextView()
        tv.isEditable = true
        tv.accessibilityHint = "Double tap to edit"
        // Do NOT set accessibilityLabel/accessibilityValue here —
        // UITextView populates them dynamically from text and isEditable.
        return tv
    }
    func updateUIView(_ uiView: UITextView, context: Context) { }
}
```

The narrowest hint to add: a hint (not a label, not a value) on the UITextView itself. Hints supplement; labels and values replace. Letting `UITextView` continue to drive its label and value is what keeps the rotor and text navigation working.

If the SwiftUI side genuinely needs to expose its own label (because the editor is one element of a larger composite), apply `.accessibilityElement(children: .contain)` so the wrapper becomes a container that lets the UIKit subtree through, rather than `.accessibilityElement()` (no argument), which replaces the subtree with a single element.

## Custom text views from scratch

A text view that doesn't inherit from `UITextView`/`NSTextView` is silent until you wire accessibility manually. The minimum surface is `isAccessibilityElement = true`, a label, a value, and traits matching the editing state.

```swift
class CustomTextView: UIView {
    override var isAccessibilityElement: Bool {
        get { true }
        set { }
    }

    override var accessibilityTraits: UIAccessibilityTraits {
        get { isEditable ? [] : .staticText }
        set { }
    }

    override var accessibilityValue: String? {
        get { textContent }
        set { }
    }

    override var accessibilityLabel: String? {
        get { placeholder ?? "Text editor" }
        set { }
    }
}
```

The trait set is empty for editable views and `.staticText` for read-only — VoiceOver derives "editable" handling from the absence of `.staticText` plus the input-system signals (focus state, first-responder status). Do not try to add a hypothetical `.editable` trait; the trait that exists is `.staticText` for the read-only case.

The accessibility value should reflect the current text content. If the editor stores text in a backing store that updates incrementally, ensure `accessibilityValue` reads the current state — caching a snapshot here is how "VoiceOver reads stale text" bugs originate.

## UIAccessibilityReadingContent

For VoiceOver's rotor to navigate the editor by line, the view must declare its line geometry through `UIAccessibilityReadingContent`. Without this protocol, character and word rotors still work (they use the value string), but line navigation does not.

```swift
extension CustomTextView: UIAccessibilityReadingContent {
    func accessibilityLineNumber(for point: CGPoint) -> Int {
        lineNumber(at: point)
    }

    func accessibilityContent(forLineNumber lineNumber: Int) -> String? {
        textContent(forLine: lineNumber)
    }

    func accessibilityFrame(forLineNumber lineNumber: Int) -> CGRect {
        frameForLine(lineNumber)
    }

    func accessibilityPageContent() -> String? {
        textContent
    }
}
```

The frame returned by `accessibilityFrame(forLineNumber:)` is in screen coordinates — convert from your view's coordinate space via `convert(rect, to: nil)` if needed. VoiceOver uses this rect to position its highlight overlay; an incorrect coordinate space results in the focus indicator drawing in the wrong place.

`accessibilityPageContent()` returns the entire visible page of text; pagination is a concept VoiceOver uses to scope long documents. For editors that don't paginate, return the full content.

## accessibilityTextualContext

`UIAccessibilityTextualContext` tells VoiceOver how to read the content. The default treats text as ordinary prose; that's wrong for code (where punctuation matters), spreadsheets (where layout structure matters), and chat (where utterances are short and discrete). The right context per editor type:

- `.sourceCode` — reads punctuation literally (braces, parens, colons, operators). The real differentiator for code editors; without it VoiceOver elides the symbols that carry meaning.
- `.wordProcessing` — rich-text editor cues. Right for a Notes-style editor with formatting and structural elements.
- `.narrative` — long-form prose readers (essays, articles, books). Reading cadence tuned for paragraphs.
- `.console` — terminals and log viewers. Treats lines as discrete records, reads control characters.
- `.messaging` — chat. Short discrete utterances, fast cadence.
- `.spreadsheet` — tabular cells. VoiceOver reads coordinates and structure.
- `.fileSystem` — paths and identifiers. Reads separators and segments rather than treating slashes as prose.

```swift
textView.accessibilityTextualContext = .sourceCode
```

Source-code context is the most consequential. In the default prose context, VoiceOver omits most punctuation — a comprehensible behavior for paragraphs, an incomprehensible one for code. A code editor that doesn't set `.sourceCode` is effectively unusable with VoiceOver.

The property is settable on any `UIView` that can be an accessibility element, not just `UITextView`. Set it on the wrapper view of a custom editor as well.

### iOS 17 and iOS 18 rotor changes

iOS 17 added a "Change Rotor with Item" toggle in Settings → Accessibility → VoiceOver → Rotor. With it enabled, focusing an item that has custom actions auto-switches the rotor to Actions; with it disabled (and many users now disable it after the iOS 17 default change), the rotor stays where the user left it. For a custom editor that exposes `accessibilityCustomActions`, this means the user may not discover the actions unless they manually rotate to the Actions rotor. Surface critical actions through the standard text-edit menu or via gesture as a backup, not only through custom actions.

iOS 18 added a two-finger rotation gesture as an alternative to the rotor twist. It reaches the same rotor ring but can be performed with one hand. No code change is required for support — the gesture works on any view that participates in the rotor — but it's worth knowing when reproducing user reports of "I can't get to the rotor."

## Announcing programmatic changes

VoiceOver is not aware of edits that happen outside the input system. Format commands, paste-and-clean operations, autocompletion expansions, AI rewrites — none of these emit accessibility events on their own. Post an announcement so the user knows what changed.

```swift
func applyFormatting(_ style: FormatStyle) {
    applyStyle(style, to: selectedRange)
    UIAccessibility.post(
        notification: .announcement,
        argument: "Applied \(style.name) formatting"
    )
}
```

For larger structural changes (content reloaded, document switched, view layout substantially changed), post `.layoutChanged` with the new focus argument so VoiceOver re-reads the focused element:

```swift
UIAccessibility.post(notification: .layoutChanged, argument: textView)
```

Don't over-announce. An announcement on every keystroke or every autocorrect is noise that makes the editor harder to use, not easier. Reserve announcements for user-initiated commands the user might not have heard the result of.

`AccessibilityNotification` on macOS uses `NSAccessibility.post(...)` with `NSAccessibility.Notification.announcementRequested` — the equivalent path with a slightly different argument shape.

## Accessibility Inspector checks

The Xcode Accessibility Inspector exposes the live tree. Run it against the simulator while interacting with the editor; the relevant fields:

- The text view appears as an element (no shadowing parent).
- Traits show as expected: `.staticText` for read-only, empty trait set for editable.
- Value updates as text changes — typing in the editor should change the displayed value live.
- Label is non-empty (a placeholder, a header label, or an accessibility-only label).
- Hint, if set, supplements the label without duplicating it.

The interaction surface should also be tested with a screen reader, not just the inspector. Accessibility Inspector confirms the wiring is present; VoiceOver confirms the wiring is correct.

## Common Mistakes

1. **SwiftUI accessibility modifiers on a `UIViewRepresentable` wrapper.** `.accessibilityLabel("Editor")` on the SwiftUI side replaces the UITextView's dynamic value with a static label, breaking text navigation. Set accessibility properties on the underlying `UITextView`, or use `.accessibilityElement(children: .contain)` to leave the subtree intact.

2. **Caching text in `accessibilityValue`.** A snapshot value stays stale as text changes. The getter should read current state from the backing store every call.

3. **Missing `UIAccessibilityReadingContent` on a custom view.** Without it, the line rotor doesn't function. Character and word navigation still work (they only need `accessibilityValue`), but line navigation requires the protocol.

4. **`.plain` context on a code editor.** VoiceOver skips most punctuation in prose context. Code becomes incomprehensible. Set `.sourceCode` on any text view whose content is code.

5. **Programmatic edits without an announcement.** A user invoking a "make this formal" rewrite hears nothing if the editor doesn't post an announcement. Post `.announcement` for command outcomes; post `.layoutChanged` for structural changes.

6. **Custom fonts without the `UIFontMetrics` + `adjustsFontForContentSizeCategory` pair.** Custom fonts re-scale only when both conditions are met: the font is wrapped via `UIFontMetrics.scaledFont(for:)` *and* the text view has `adjustsFontForContentSizeCategory = true`. Either alone is inert. This often surfaces during accessibility audits because reviewers test at AX sizes and the editor's text doesn't grow. See `/skill txt-dynamic-type` for the scaling pattern. Accessibility and Dynamic Type are separate but mutually reinforcing.

7. **Testing only with VoiceOver.** Switch Control, Voice Control, and Full Keyboard Access exercise different surfaces. A view that works with VoiceOver may still be unreachable by Switch Control if the trait set or focus order is wrong.

## References

- `/skill txt-dynamic-type` — Dynamic Type scaling, content-size categories, `UIFontMetrics`
- `/skill txt-wrap-textview` — `UIViewRepresentable` wrapping patterns and the SwiftUI/UIKit boundary
- `/skill txt-view-picker` — picking an accessible text view in the first place
- `/skill txt-colors` — text contrast and semantic color pairing
- [UIAccessibility](https://sosumi.ai/documentation/uikit/uiaccessibility)
- [UIAccessibilityReadingContent](https://sosumi.ai/documentation/uikit/uiaccessibilityreadingcontent)
- [UIAccessibilityTextualContext](https://sosumi.ai/documentation/uikit/uiaccessibilitytextualcontext)
