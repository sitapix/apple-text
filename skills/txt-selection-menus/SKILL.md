---
name: txt-selection-menus
description: Customize selection UI, edit menus, link taps, gestures, and cursor appearance on UITextView and NSTextView — UIEditMenuInteraction, UITextItem actions and tags, link delegate routing, gesture coordination, tintColor and linkTextAttributes. Use when the user is changing how the stock edit menu, selection rects, link tap, long-press menu, or cursor color behaves on a text view they didn't write from scratch. Do NOT use for full UITextInput protocol implementation in custom views — see txt-uitextinput.
license: MIT
---

# Selection, Menus, and Gestures

Authored against iOS 26.x / Swift 6.x / Xcode 26.x.

This skill covers the *customization seams* that UIKit and AppKit expose on stock text views: the edit menu, link and text-item interaction, gesture priorities, cursor color, selection rects. The protocol that text views implement underneath (`UITextInput`) is a different skill. The patterns here are clues — before claiming a delegate signature, fetch the current API via Sosumi (`sosumi.ai/documentation/uikit/uieditmenuinteraction`, `sosumi.ai/documentation/uikit/uitextitem`); the iOS 17 text-item APIs replaced large parts of the older link delegate.

If a tap is going to the wrong handler, the answer is usually a gesture-coordination question, not a configuration question. Read the gesture recognizer list on the live view in the debugger before tweaking delegate methods.

## Contents

- [Edit menu on iOS](#edit-menu-on-ios)
- [Text items: links, attachments, custom tags](#text-items-links-attachments-custom-tags)
- [Legacy link delegate](#legacy-link-delegate)
- [Cursor and selection appearance](#cursor-and-selection-appearance)
- [Constraining selection](#constraining-selection)
- [Gesture coordination](#gesture-coordination)
- [Edit menu on macOS](#edit-menu-on-macos)
- [Common Mistakes](#common-mistakes)
- [References](#references)

## Edit menu on iOS

`UIEditMenuInteraction` is the modern edit-menu host. `UITextView` adds it automatically; you customize either by overriding `canPerformAction(_:withSender:)` for built-in selectors or by adding your own `UIEditMenuInteraction` and rewriting the menu in the delegate.

```swift
final class AnnotatableTextView: UITextView {
    override func canPerformAction(_ action: Selector, withSender sender: Any?) -> Bool {
        if action == #selector(defineWord(_:)) {
            return selectedRange.length > 0
        }
        return super.canPerformAction(action, withSender: sender)
    }

    @objc func defineWord(_ sender: Any?) {
        let word = (text as NSString).substring(with: selectedRange)
        // present definition
    }
}
```

For larger menus or contextual menus on non-text views, install the interaction directly and rewrite the menu in the delegate:

```swift
class EditorView: UIView {
    let editMenu = UIEditMenuInteraction(delegate: self)
    override init(frame: CGRect) {
        super.init(frame: frame); addInteraction(editMenu)
    }
}

extension EditorView: UIEditMenuInteractionDelegate {
    func editMenuInteraction(
        _ interaction: UIEditMenuInteraction,
        menuFor configuration: UIEditMenuConfiguration,
        suggestedActions: [UIMenuElement]
    ) -> UIMenu? {
        let bold = UIAction(title: "Bold", image: UIImage(systemName: "bold")) { [weak self] _ in
            self?.toggleBold()
        }
        return UIMenu(children: suggestedActions + [bold])
    }
}
```

`UIMenuController` is the deprecated predecessor; calls still link, but new code should not start there. The replacement happened in iOS 16 and the old API will eventually stop responding.

## Text items: links, attachments, custom tags

iOS 17 generalized link interaction into `UITextItem`. The same delegate methods now handle URL links, `NSTextAttachment` taps, and arbitrary tagged ranges, which lets you make non-link text interactive without forcing the link tint color.

```swift
func textView(_ textView: UITextView,
              primaryActionFor textItem: UITextItem,
              defaultAction: UIAction) -> UIAction? {
    switch textItem.content {
    case .link(let url):
        return UIAction { _ in self.handleLink(url) }
    case .textAttachment(let attachment):
        return UIAction { _ in self.handleAttachment(attachment) }
    case .tag(let tag):
        return UIAction { _ in self.handleTag(tag) }
    @unknown default:
        return defaultAction
    }
}

func textView(_ textView: UITextView,
              menuConfigurationFor textItem: UITextItem,
              defaultMenu: UIMenu) -> UITextItem.MenuConfiguration? {
    switch textItem.content {
    case .tag(let tag):
        let viewProfile = UIAction(title: "View Profile") { _ in self.showProfile(for: tag) }
        return UITextItem.MenuConfiguration(menu: UIMenu(children: [viewProfile] + defaultMenu.children))
    default:
        return UITextItem.MenuConfiguration(menu: defaultMenu)
    }
}
```

The `.uiTextItemTag` attribute makes a range tappable without the `.link` styling. `.link` forces the foreground color to `tintColor` and an underline; `.uiTextItemTag` leaves the range visually unchanged but routes taps and long-presses through the same delegate methods.

```swift
let s = NSMutableAttributedString(string: "@username is here")
s.addAttribute(.uiTextItemTag,
               value: "user:123",
               range: NSRange(location: 0, length: 9))
// Tappable, but renders in the default text color
```

## Legacy link delegate

`textView(_:shouldInteractWith:in:interaction:)` predates the text-item API and only handles `.link` ranges. iOS 17 marked it deprecated, but it's still everywhere in existing code and works on iOS 13+:

```swift
func textView(_ textView: UITextView,
              shouldInteractWith URL: URL,
              in characterRange: NSRange,
              interaction: UITextItemInteraction) -> Bool {
    switch interaction {
    case .invokeDefaultAction:
        handleLink(URL); return false
    case .presentActions, .preview:
        return true
    @unknown default:
        return true
    }
}
```

This delegate stays silent unless the text view is non-editable and selectable — `isEditable = true` routes link taps through editing first, and `isSelectable = false` disables interaction entirely. If a link is set up correctly but nothing fires, those two flags are the first thing to check.

## Cursor and selection appearance

The cursor color and the link tint share a single property: `tintColor`. There is no separate cursor color API. If links and the cursor need different colors, leave `tintColor` for the cursor and override `linkTextAttributes` for links:

```swift
textView.tintColor = .systemRed
textView.linkTextAttributes = [
    .foregroundColor: UIColor.systemBlue,
    .underlineStyle: NSUnderlineStyle.single.rawValue,
]
```

Cursor *width* is system-rendered — there's no public knob for it on a stock text view. A custom view can render its own cursor through `UITextSelectionDisplayInteraction` (covered in `txt-uitextinput`).

To suppress the cursor entirely on a presentation-mode text view that still allows selection, override `caretRect(for:)` to return `.zero`:

```swift
final class NoCaretTextView: UITextView {
    override func caretRect(for position: UITextPosition) -> CGRect { .zero }
}
```

## Constraining selection

If parts of the document are protected (read-only headers, immutable code blocks), push selection out of the protected range in `textViewDidChangeSelection`:

```swift
func textViewDidChangeSelection(_ textView: UITextView) {
    let sel = textView.selectedRange
    if NSIntersectionRange(sel, protectedRange).length > 0 {
        textView.selectedRange = NSRange(location: NSMaxRange(protectedRange), length: 0)
    }
}
```

This runs on the main thread synchronously after every selection change, so the user sees the cursor jump rather than land inside the protected region.

For per-line or word-granularity selection differences, override `selectionRects(for:)` on a `UITextView` subclass — it lets you change how the selection is drawn without changing what the selection actually covers in storage.

## Gesture coordination

`UITextView` installs many gesture recognizers — tap-to-position, double-tap to word-select, long-press for the loupe and edit menu, and on iPadOS 14+ the Scribble recognizer. Adding your own gestures often produces "the recognizer fires sometimes" bugs because the system gestures are claiming the touch first.

Two coordination tools matter. `gestureRecognizerShouldBegin` lets you reject system gestures over your own UI elements:

```swift
final class CustomGestureTextView: UITextView {
    override func gestureRecognizerShouldBegin(_ g: UIGestureRecognizer) -> Bool {
        if g is UILongPressGestureRecognizer,
           isOverCustomElement(g.location(in: self)) {
            return false
        }
        return super.gestureRecognizerShouldBegin(g)
    }
}
```

`UIGestureRecognizerDelegate.shouldRecognizeSimultaneously` lets a custom recognizer coexist with system ones:

```swift
func gestureRecognizer(_ g: UIGestureRecognizer,
                       shouldRecognizeSimultaneouslyWith other: UIGestureRecognizer) -> Bool {
    return true
}
```

Touch hit-testing is in view coordinates; the gesture recognizer can be on a parent view but the location is always reported relative to the view passed to `location(in:)`.

## Edit menu on macOS

AppKit doesn't have a `UIEditMenuInteraction` analog — the contextual menu on right-click uses `NSMenu`, configured per `NSTextView` via `menu(for:)` or by replacing the view's `menu` property:

```swift
final class CustomTextView: NSTextView {
    override func menu(for event: NSEvent) -> NSMenu? {
        let menu = super.menu(for: event) ?? NSMenu()
        let bold = NSMenuItem(title: "Bold",
                              action: #selector(toggleBold(_:)),
                              keyEquivalent: "")
        menu.addItem(bold)
        return menu
    }
}
```

`NSTextView` also dispatches its own selectors for the standard items (cut, copy, paste, look up). Override `validateMenuItem(_:)` to enable or disable specific items per selection.

## Common Mistakes

1. **Using `.link` to make non-link text tappable, then trying to suppress the styling.** `.link` is documented to force `tintColor` and underline. Removing those overrides is fragile across iOS versions. Use `.uiTextItemTag` instead — it's the iOS 17+ way to route taps without altering text color.

2. **Configuring link delegate but `isSelectable = false` on the text view.** The link delegate never fires. The view must be selectable for the system to deliver link interaction events. If the view is also `isEditable = true`, taps go through editing first; non-editable + selectable is the link-only configuration.

3. **Trying to set a separate cursor color and link color via `tintColor`.** They share the same property. The cursor reads `tintColor`; links read `linkTextAttributes[.foregroundColor]` if set, otherwise fall back to `tintColor`. Override the dictionary to split them.

4. **Adding gesture recognizers without coordination, then debugging "sometimes fires."** The system gesture wins because it was added first and isn't told to share. Either reject the system recognizer in `gestureRecognizerShouldBegin` for the regions you care about, or set `shouldRecognizeSimultaneously` to `true` on your delegate.

5. **Mutating the menu in `editMenuInteraction(_:menuFor:suggestedActions:)` by index.** The suggested actions list changes between iOS versions and selection states. Append by content (look up actions by identifier) rather than mutating positions.

6. **Calling `UIMenuController` API.** Deprecated since iOS 16 and likely to stop functioning. Migrate to `UIEditMenuInteraction`.

7. **Right-click menu on macOS not showing custom items.** AppKit assembles the menu through `validateMenuItem(_:)` — if the action's selector isn't reachable on the responder chain, the item is hidden, not greyed out. Verify the selector resolves on the view or its delegate.

## References

- `txt-uitextinput` — full UITextInput protocol implementation in custom views (selection display, loupe, marked text)
- `txt-find-replace` — find/replace UI on text views
- `txt-pasteboard` — copy/paste customization, including custom edit-menu items that copy non-default formats
- `txt-writing-tools` — Writing Tools and how it integrates with the edit menu
- [UIEditMenuInteraction](https://sosumi.ai/documentation/uikit/uieditmenuinteraction)
- [UITextItem](https://sosumi.ai/documentation/uikit/uitextitem)
- [UITextInteraction](https://sosumi.ai/documentation/uikit/uitextinteraction)
