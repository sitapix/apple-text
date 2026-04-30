# Latest API surface — txt-writing-tools

Authored against iOS 26.x / Swift 6.x / Xcode 26.x. Last refreshed 2026-04-29 against Sosumi.

This sidecar pins the API signatures the SKILL.md describes. SKILL.md owns the mental model; this file owns the call shapes. Refresh on each Xcode 26.x point release via the `txt-refresh-against-sosumi` skill.

## Coordinator

- `UIWritingToolsCoordinator` — `@MainActor class UIWritingToolsCoordinator` conforming to `UIInteraction`; manages Writing Tools for a custom view, since: iOS 18.2. <https://sosumi.ai/documentation/uikit/uiwritingtoolscoordinator>
- `UIWritingToolsCoordinator.init(delegate:)` — creates the coordinator with a `UIWritingToolsCoordinator.Delegate`, since: iOS 18.2. <https://sosumi.ai/documentation/uikit/uiwritingtoolscoordinator>
- `UITextView.writingToolsCoordinator` — `var writingToolsCoordinator: UIWritingToolsCoordinator { get }`, since: iOS 18.2. UITextView gets a free coordinator lazily on first access; the property is read-only and returns the same instance for the lifetime of the text view. Use it to drive interactive rewrites or react to coordinator state without writing a custom delegate. <https://sosumi.ai/documentation/uikit/uitextview/writingtoolscoordinator>
- `UIWritingToolsCoordinator.isWritingToolsAvailable` — Boolean indicating whether Writing Tools features are currently available, since: iOS 18.2.
- `UIWritingToolsCoordinator.delegate` — the object that handles Writing Tools interactions, since: iOS 18.2.
- `UIWritingToolsCoordinator.effectContainerView` — view used for visual effects during rewrites, since: iOS 18.2.
- `UIWritingToolsCoordinator.decorationContainerView` — view used for proofreading marks and other decorations, since: iOS 18.2.
- `UIWritingToolsCoordinator.stopWritingTools()` — terminates the current Writing Tools operation and dismisses the system UI, since: iOS 18.2.
- `UIWritingToolsCoordinator.updateRange(_:with:reason:forContextWithIdentifier:)` — informs the coordinator of app-driven text changes inside an active context, since: iOS 18.2.
- `UIWritingToolsCoordinator.updateForReflowedTextInContextWithIdentifier(_:)` — informs the coordinator of layout-changing edits, since: iOS 18.2.
- `NSWritingToolsCoordinator` — `@MainActor class NSWritingToolsCoordinator`; AppKit equivalent attached via `NSView.writingToolsCoordinator`, since: macOS 15.2. <https://sosumi.ai/documentation/appkit/nswritingtoolscoordinator>

## Behavior configuration

- `UIWritingToolsBehavior` — `enum UIWritingToolsBehavior`; cases `.none`, `.default`, `.complete`, `.limited`, since: iOS 18.0. The set value is never `.default` at read time — UIKit resolves it to one of the concrete cases. <https://sosumi.ai/documentation/uikit/uiwritingtoolsbehavior>
- `UITextView.writingToolsBehavior` — `var writingToolsBehavior: UIWritingToolsBehavior { get set }`, since: iOS 18.0. <https://sosumi.ai/documentation/uikit/uitextview/writingtoolsbehavior>
- `UIWritingToolsResultOptions` — `struct UIWritingToolsResultOptions: OptionSet`; instance options `.plainText`, `.richText`, `.list`, `.table`; type property `.presentationIntent` implies the others and switches Writing Tools to `PresentationIntent`-based output, since: iOS 18.0. <https://sosumi.ai/documentation/uikit/uiwritingtoolsresultoptions>
- `UITextView.allowedWritingToolsResultOptions` — `var allowedWritingToolsResultOptions: UIWritingToolsResultOptions { get set }`, since: iOS 18.0. Including `.table` raises `NSInvalidArgumentException` on `UITextView`. <https://sosumi.ai/documentation/uikit/uitextview/allowedwritingtoolsresultoptions>
- `UIWritingToolsCoordinator.preferredBehavior` / `behavior` — `preferredBehavior` is the requested level; `behavior` is the actual level the system grants, since: iOS 18.2.
- `UIWritingToolsCoordinator.preferredResultOptions` / `resultOptions` — same pattern for content kinds, since: iOS 18.2.
- `NSWritingToolsBehavior` — same case set as UIKit (`.none`, `.default`, `.complete`, `.limited`), since: macOS 15.0. <https://sosumi.ai/documentation/appkit/nswritingtoolsbehavior>
- `NSWritingToolsResultOptions` — same option set (`.plainText`, `.richText`, `.list`, `.table`, plus type `.presentationIntent`), since: macOS 15.0. <https://sosumi.ai/documentation/appkit/nswritingtoolsresultoptions>
- `NSTextView.writingToolsBehavior` — `var writingToolsBehavior: NSWritingToolsBehavior { get set }`, since: macOS 15.0. <https://sosumi.ai/documentation/appkit/nstextview/writingtoolsbehavior>
- `NSTextView.allowedWritingToolsResultOptions` — `var allowedWritingToolsResultOptions: NSWritingToolsResultOptions { get set }`, since: macOS 15.0. <https://sosumi.ai/documentation/appkit/nstextview/allowedwritingtoolsresultoptions>

## Protected ranges

- `UITextViewDelegate.textView(_:writingToolsIgnoredRangesInEnclosingRange:)` — `optional func textView(_ textView: UITextView, writingToolsIgnoredRangesInEnclosingRange enclosingRange: NSRange) -> [NSValue]`. Return ranges as `[NSValue]` (each wrapping an `NSRange` via `NSValue(range:)`), since: iOS 18.0. <https://sosumi.ai/documentation/uikit/uitextviewdelegate/textview(_:writingtoolsignoredrangesinenclosingrange:)>
- `NSTextViewDelegate.textView(_:writingToolsIgnoredRangesInEnclosingRange:)` — `@MainActor optional func textView(_ textView: NSTextView, writingToolsIgnoredRangesInEnclosingRange enclosingRange: NSRange) -> [NSValue]`, since: macOS 15.0. <https://sosumi.ai/documentation/appkit/nstextviewdelegate/textview(_:writingtoolsignoredrangesinenclosingrange:)>
- `Foundation.PresentationIntent` — `struct PresentationIntent`; assign on `AttributedString` runs to declare structure (headings, code blocks, lists, tables) so Writing Tools skips code/quote regions without an explicit ignored-range callback, since: iOS 15.0 / macOS 12.0. <https://sosumi.ai/documentation/foundation/presentationintent>

## Lifecycle

- `UITextView.isWritingToolsActive` — `var isWritingToolsActive: Bool { get }`; true while a Writing Tools session is mutating the view, since: iOS 18.0. <https://sosumi.ai/documentation/uikit/uitextview/iswritingtoolsactive>
- `UITextViewDelegate.textViewWritingToolsWillBegin(_:)` — `optional func textViewWritingToolsWillBegin(_ textView: UITextView)`, since: iOS 18.0. <https://sosumi.ai/documentation/uikit/uitextviewdelegate/textviewwritingtoolswillbegin(_:)>
- `UITextViewDelegate.textViewWritingToolsDidEnd(_:)` — `optional func textViewWritingToolsDidEnd(_ textView: UITextView)`, since: iOS 18.0. <https://sosumi.ai/documentation/uikit/uitextviewdelegate/textviewwritingtoolsdidend(_:)>
- `NSTextView.isWritingToolsActive` — `var isWritingToolsActive: Bool { get }`, since: macOS 15.0. <https://sosumi.ai/documentation/appkit/nstextview/iswritingtoolsactive>
- `NSTextViewDelegate.textViewWritingToolsWillBegin(_:)` — `@MainActor optional func textViewWritingToolsWillBegin(_ textView: NSTextView)`. The parameter is the text view, not a `Notification`, since: macOS 15.0. <https://sosumi.ai/documentation/appkit/nstextviewdelegate/textviewwritingtoolswillbegin(_:)>
- `NSTextViewDelegate.textViewWritingToolsDidEnd(_:)` — `@MainActor optional func textViewWritingToolsDidEnd(_ textView: NSTextView)`, since: macOS 15.0. <https://sosumi.ai/documentation/appkit/nstextviewdelegate/textviewwritingtoolsdidend(_:)>

## Coordinator state

- `UIWritingToolsCoordinator.state` — `var state: UIWritingToolsCoordinator.State { get }`, since: iOS 18.2.
- `UIWritingToolsCoordinator.State` — `enum State`; cases `.inactive`, `.noninteractive`, `.interactiveResting`, `.interactiveStreaming`. The lowercase `.noninteractive` (no inner capital) is the actual case spelling. Treat unknown future values defensively (`@unknown default`), since: iOS 18.2. <https://sosumi.ai/documentation/uikit/uiwritingtoolscoordinator/state>
- `NSWritingToolsCoordinator.State` — same case set on AppKit, since: macOS 15.2. <https://sosumi.ai/documentation/appkit/nswritingtoolscoordinator/state-swift.enum>

## Delegate

- `UIWritingToolsCoordinator.Delegate` — `protocol Delegate : NSObjectProtocol`; nested under the coordinator class (the type is `UIWritingToolsCoordinator.Delegate`, not a top-level `UIWritingToolsCoordinatorDelegate`), since: iOS 18.2. <https://sosumi.ai/documentation/uikit/uiwritingtoolscoordinator/delegate-swift.protocol>
- `writingToolsCoordinator(_:requestsContextsFor:completion:)` — provides text to evaluate; uses a `completion` handler, not Swift `async`, since: iOS 18.2.
- `writingToolsCoordinator(_:replace:in:proposedText:reason:animationParameters:completion:)` — applies replacement text to the host view, since: iOS 18.2.
- `writingToolsCoordinator(_:select:in:completion:)` — updates the view's current text selection, since: iOS 18.2.
- `writingToolsCoordinator(_:willChangeTo:completion:)` — notifies the delegate of state changes, since: iOS 18.2.
- `writingToolsCoordinator(_:requestsPreviewFor:of:in:completion:)` — preview image and layout for animated rewrites, since: iOS 18.2.
- `writingToolsCoordinator(_:prepareFor:for:in:completion:)` — pre-animation hook, since: iOS 18.2.
- `writingToolsCoordinator(_:finish:for:in:completion:)` — post-animation cleanup, since: iOS 18.2.
- `writingToolsCoordinator(_:requestsRangeInContextWithIdentifierFor:completion:)` — point-to-character mapping in view coordinates, since: iOS 18.2.
- `writingToolsCoordinator(_:requestsBoundingBezierPathsFor:in:completion:)` — bounding paths for given text, since: iOS 18.2.
- `writingToolsCoordinator(_:requestsUnderlinePathsFor:in:completion:)` — underline shape for proofreading marks, since: iOS 18.2.
- `writingToolsCoordinator(_:requestsSingleContainerSubrangesOf:in:completion:)` — split a range across multiple containers, since: iOS 18.2.
- `writingToolsCoordinator(_:requestsDecorationContainerViewFor:in:completion:)` — supply a decoration view for a range, since: iOS 18.2.
- `NSWritingToolsCoordinator.Delegate` — same protocol shape on AppKit, since: macOS 15.2. <https://sosumi.ai/documentation/appkit/nswritingtoolscoordinator/delegate-swift.protocol>

## Supporting types

- `UIWritingToolsCoordinator.Context` — `class Context`; carries the text Writing Tools evaluates and reports the resolved range it actually used, since: iOS 18.2. <https://sosumi.ai/documentation/uikit/uiwritingtoolscoordinator/context>
- `UIWritingToolsCoordinator.ContextScope` — options describing how much of the document Writing Tools is requesting, since: iOS 18.2.
- `UIWritingToolsCoordinator.TextReplacementReason` — `enum TextReplacementReason`; cases `.interactive`, `.noninteractive`, since: iOS 18.2. <https://sosumi.ai/documentation/uikit/uiwritingtoolscoordinator/textreplacementreason>
- `UIWritingToolsCoordinator.TextAnimation` — animation kinds Writing Tools performs during interactive updates, since: iOS 18.2.
- `UIWritingToolsCoordinator.AnimationParameters` — animation timing/curve information passed to the delegate, since: iOS 18.2.
- `UIWritingToolsCoordinator.TextUpdateReason` — reason value for app-driven `updateRange(...)` calls, since: iOS 18.2.

## Custom UITextInput integration

- `UITextInteraction` — `@MainActor class UITextInteraction`; bundled selection / edit menu / Writing Tools interaction; attach via `addInteraction(_:)` after assigning `textInput`, since: iOS 13.0 (Writing Tools support added with the system feature). <https://sosumi.ai/documentation/uikit/uitextinteraction>

## Discrepancies vs SKILL.md (2026-04-29)

- SKILL.md uses `.default` to mean the full inline experience. Sosumi shows the full inline case is `.complete`; `.default` lets the system choose, and the resolved value is never `.default` at read time.
- SKILL.md says `writingToolsAllowedInputOptions`. The actual property is `allowedWritingToolsResultOptions` and its type is `UIWritingToolsResultOptions` (not `WritingToolsAllowedInputOptions`).
- SKILL.md lists option-set members as `.plainText`, `.richText`, `.table`. Sosumi shows the full set is `.plainText`, `.richText`, `.list`, `.table`, plus type property `.presentationIntent`. UITextView raises `NSInvalidArgumentException` if `.table` is included.
- SKILL.md uses `[NSRange]` as the return type of `writingToolsIgnoredRangesIn`. The actual delegate signature is `writingToolsIgnoredRangesInEnclosingRange:` and returns `[NSValue]` (each wrapping an `NSRange`).
- SKILL.md names the protocol `UIWritingToolsCoordinatorDelegate`. The actual type is `UIWritingToolsCoordinator.Delegate` (nested inside the coordinator class).
- SKILL.md depicts delegate methods as `async` Swift functions returning values. The published surface uses `completion:` handler-based methods (e.g., `writingToolsCoordinator(_:requestsContextsFor:completion:)`).
- SKILL.md references state cases `.idle`, `.nonInteractive`, `.interactiveStreaming`. The actual cases are `.inactive`, `.noninteractive`, `.interactiveResting`, `.interactiveStreaming`.
- SKILL.md describes the `Context` initializer as `.init(attributedString:range:)` and uses a `TextRange` nested type. Sosumi shows `Context` is a class with a `resolvedRange` property and no documented `TextRange` nested type.
- SKILL.md says AppKit's `textViewWritingToolsWillBegin(_:)` takes a `Notification`. Sosumi shows it takes the `NSTextView` itself, matching the UIKit shape.
- SKILL.md mentions `requestsUnderlinePathFor:` (singular). The actual method is `writingToolsCoordinator(_:requestsUnderlinePathsFor:in:completion:)` (plural, with completion).

## Signatures verified against Sosumi

| URL | Status | Last fetched |
|---|---|---|
| https://sosumi.ai/documentation/uikit/uiwritingtoolscoordinator | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/uikit/uiwritingtoolscoordinator/delegate-swift.protocol | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/uikit/uiwritingtoolscoordinator/state | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/uikit/uiwritingtoolscoordinator/context | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/uikit/uiwritingtoolscoordinator/textreplacementreason | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/uikit/uiwritingtoolsbehavior | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/uikit/uiwritingtoolsresultoptions | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/uikit/uitextview/writingtoolsbehavior | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/uikit/uitextview/allowedwritingtoolsresultoptions | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/uikit/uitextview/iswritingtoolsactive | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/uikit/uitextview/writingtoolscoordinator | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/uikit/uitextviewdelegate | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/uikit/uitextviewdelegate/textview(_:writingtoolsignoredrangesinenclosingrange:) | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/uikit/uitextviewdelegate/textviewwritingtoolswillbegin(_:) | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/uikit/uitextviewdelegate/textviewwritingtoolsdidend(_:) | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/uikit/uitextinteraction | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/appkit/nswritingtoolscoordinator | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/appkit/nswritingtoolscoordinator/delegate-swift.protocol | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/appkit/nswritingtoolscoordinator/state-swift.enum | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/appkit/nswritingtoolsbehavior | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/appkit/nswritingtoolsresultoptions | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/appkit/nstextview/writingtoolsbehavior | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/appkit/nstextview/allowedwritingtoolsresultoptions | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/appkit/nstextview/iswritingtoolsactive | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/appkit/nstextviewdelegate/textview(_:writingtoolsignoredrangesinenclosingrange:) | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/appkit/nstextviewdelegate/textviewwritingtoolswillbegin(_:) | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/appkit/nstextviewdelegate/textviewwritingtoolsdidend(_:) | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/presentationintent | 200 | 2026-04-29 |
