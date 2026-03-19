# Complete Catalog of Apple Text Views

Every text input and display view available on Apple platforms: SwiftUI, UIKit, and AppKit.

---

## PART 1: SwiftUI Views

---

### 1. Text (Display Only)

**What it is:** A non-editable view that displays one or more lines of static text. The fundamental text display primitive in SwiftUI.

**When to use:** Displaying labels, titles, body copy, formatted text, Markdown content, or any read-only text in a SwiftUI interface.

**Lines:** Multi-line by default. Use `.lineLimit(n)` to constrain. `lineLimit(nil)` = unlimited (default). iOS 16+ adds range-based `lineLimit(2...5)` and `lineLimit(n, reservesSpace: true)`.

**Rich text support:**
- Inline Markdown in string literals: `Text("**Bold** and *italic*")`
- Full `AttributedString` support: `Text(attributedString)`
- Concatenation: `Text("Hello ") + Text("World").bold()`
- Supported Markdown: bold, italic, strikethrough, inline code, links (GitHub Flavored Markdown inline subset)
- NOT supported in Markdown rendering: headings, lists, images, tables, blockquotes, code blocks (block-level elements)

**AttributedString support:** Yes (iOS 15+). Renders these attributes: `font`, `foregroundColor`, `backgroundColor`, `strikethroughStyle`, `underlineStyle`, `kern`, `tracking`, `baselineOffset`, `link`. Silently ignores: `paragraphStyle`, `shadow`, `strokeColor`, `strokeWidth`, `textEffect`, `attachment`, `writingDirection`, `ligature`, `obliqueness`, `expansion`, `presentationIntent`.

**Customization:**
- `.font()`, `.foregroundStyle()`, `.fontWeight()`, `.italic()`, `.bold()`, `.strikethrough()`, `.underline()`
- `.lineSpacing()`, `.multilineTextAlignment()`, `.truncationMode()`
- `.minimumScaleFactor()` for font shrinking
- `.fixedSize(horizontal: false, vertical: true)` to prevent truncation
- `.textSelection(.enabled)` (iOS 15+) — on iOS selects ALL text; range selection only on macOS
- iOS 16+: `ViewThatFits` for dynamic layout switching

**Limitations:**
- No editing, no cursor, no selection handles on iOS (only select-all)
- No paragraph style control (line height, indentation, alignment per-paragraph)
- No text attachments or inline images
- No block-level Markdown rendering
- Cannot query layout information (no TextKit access)

**iOS version:** iOS 13+ (basic). iOS 15+ (AttributedString, Markdown, textSelection). iOS 16+ (range-based lineLimit, ViewThatFits).

---

### 2. TextField (Single-Line Input, Multi-Line with axis)

**What it is:** A text input control. By default single-line. Since iOS 16, accepts `axis: .vertical` to expand into multiple lines as the user types.

**When to use:** Name fields, email inputs, search terms, short-form text entry, chat composers, comment boxes. Use the `axis: .vertical` variant for expanding inputs like iMessage-style composers.

**Lines:**
- Default: Single line
- With `axis: .vertical` (iOS 16+): Starts as single line, grows dynamically with content
- `.lineLimit(5)`: Grows up to 5 lines, then scrolls
- `.lineLimit(2...5)`: Maintains minimum 2 lines, expands to maximum 5
- `.lineLimit(5, reservesSpace: true)`: Allocates space for 5 lines upfront

**Rich text support:** No. Plain `String` binding only. No `AttributedString` editing.

**AttributedString support:** No (input). Display of attributed placeholder: no.

**Placeholder / Prompt:**
- `prompt` parameter (iOS 15+): Explicit placeholder text inside the field
- `title` / label: Describes the purpose; used as placeholder when no prompt is set
- On macOS in Forms, label appears at leading edge; prompt appears inside field

**Formatter support:**
- `format:` parameter for numbers, currency, dates: `TextField("Price", value: $price, format: .currency(code: "USD"))`
- `NumberFormatter`, `DateFormatter` via `formatter:` parameter
- Validation happens on Return press, not live

**Styles:**
- `.textFieldStyle(.automatic)` — context-dependent default
- `.textFieldStyle(.plain)` — no decoration
- `.textFieldStyle(.roundedBorder)` — rounded border (most common on iOS)
- `.textFieldStyle(.squareBorder)` — macOS only
- Custom styles via `TextFieldStyle` protocol

**Customization:**
- `.keyboardType()`, `.textContentType()`, `.textInputAutocapitalization()`, `.autocorrectionDisabled()`
- `.submitLabel()` for Return key text
- `.onSubmit {}` for Return key action
- `.focused()` with `@FocusState` for keyboard management
- Writing Tools: supported automatically (iOS 18+)
- `.textFieldStyle()` for visual styling

**Limitations:**
- No rich text editing
- No attributed text input
- No find/replace
- No text attachments
- Formatter validation only on commit, not live
- Before iOS 16: strictly single-line only
- With `axis: .vertical`: no built-in scroll indicator, no fixed-frame editing area

**TextField (axis: .vertical) vs TextEditor comparison:**

| Feature | TextField (axis: .vertical) | TextEditor |
|---------|---------------------------|------------|
| Minimum iOS | 16 | 14 |
| Placeholder | Yes (native) | No (workaround needed) |
| Growth behavior | Starts small, expands | Fixed frame, scrolls |
| Line limit control | lineLimit ranges | lineLimit (iOS 16+) |
| Rich text (iOS 26+) | No | Yes (AttributedString) |
| Find & Replace | No | Yes (.findNavigator) |
| Best for | Short expanding inputs | Long-form text editing |

**iOS version:** iOS 13+ (basic single-line). iOS 15+ (prompt parameter, format parameter). iOS 16+ (axis: .vertical, range-based lineLimit).

---

### 3. TextEditor (Multi-Line Text Editing)

**What it is:** A scrollable, multi-line text editing view. The SwiftUI equivalent of a textarea. Since iOS 26, supports rich text editing with `AttributedString`.

**When to use:** Notes editors, long-form text entry, document editing, code editing (basic), any scenario requiring a large editable text area.

**Lines:** Multi-line, scrollable. `.lineLimit()` supported (iOS 16+). No maximum line count — scrolls indefinitely.

**Rich text support:**
- iOS 14-25: Plain `String` only. No rich text.
- iOS 26+: Full `AttributedString` support. Bind to `@State var text: AttributedString` instead of `String`. Supports bold, italic, underline, strikethrough, custom fonts/sizes, foreground/background colors, kerning, tracking, baseline offset, paragraph alignment, line height, text direction, links, and Genmoji.

**AttributedString support:**
- iOS 14-25: No
- iOS 26+: Yes. Two-way binding. `AttributedTextSelection` for tracking/manipulating selected text. `typingAttributes` for knowing/setting formatting at cursor. `transformAttributes(in: &selection)` for modifying selected text attributes. Built-in Markdown parsing via `AttributedString(markdown:)`.

**Customization:**
- `.font()`, `.foregroundStyle()`, `.lineSpacing()`
- `.scrollContentBackground(.hidden)` + `.background()` for custom background (iOS 16+)
- `.keyboardType()`, `.textInputAutocapitalization()`, `.autocorrectionDisabled()`
- `.findNavigator(isPresented:)` for built-in find/replace (iOS 16+)
- `.findDisabled()`, `.replaceDisabled()` to control find/replace features
- `.writingToolsBehavior()` for Apple Intelligence Writing Tools (iOS 18+): `.automatic`, `.complete`, `.limited`, `.disabled`
- `@FocusState` / `.focused()` for keyboard management

**Limitations:**
- No native placeholder text (workaround: ZStack overlay with Text + `.allowsHitTesting(false)`)
- No built-in character limit (workaround: `.onChange` truncation)
- No native read-only mode (workaround: `.constant()` binding or UIViewRepresentable)
- Before iOS 16: Cannot hide default background color (workaround: `UITextView.appearance().backgroundColor = .clear`)
- Before iOS 26: No rich text, no attributed strings
- No syntax highlighting (must use TextKit views for this)
- No text attachments/inline images (even in iOS 26)
- No line numbers

**iOS version:** iOS 14+ (basic plain text). iOS 16+ (find/replace, scrollContentBackground, lineLimit). iOS 18+ (Writing Tools, text selection parameter). iOS 26+ (AttributedString rich text editing, AttributedTextSelection).

---

### 4. SecureField (Password Input)

**What it is:** A text input that masks the entered characters with dots for password/sensitive data entry.

**When to use:** Passwords, PINs, security codes, any sensitive text input.

**Lines:** Single line only.

**Rich text support:** No.

**AttributedString support:** No.

**Customization:**
- `.textContentType(.password)`, `.textContentType(.newPassword)` for AutoFill
- `.textFieldStyle()` — same styles as TextField
- `.submitLabel()`, `.onSubmit {}`
- `@FocusState` / `.focused()`

**Limitations:**
- Single line only; no multi-line secure input
- No built-in show/hide toggle (must implement manually by switching between SecureField and TextField)
- Text erases when user attempts to edit mid-string (iOS behavior)
- No copy/paste of masked text
- No attributed text or rich formatting
- Focus transfer between SecureField and TextField (for show/hide) requires careful handling

**iOS version:** iOS 13+.

---

### 5. Label (Icon + Text Display)

**What it is:** A standard display view combining an icon (SF Symbol or custom image) with a text title. Not a text input.

**When to use:** Menu items, list rows, toolbar items, settings rows, anywhere an icon-text pair is needed.

**Lines:** Typically single line. Title text follows standard Text truncation rules.

**Rich text support:** The title closure can contain any View, so you can use a styled Text.

**AttributedString support:** Not directly (it is a structural view, not a text-rendering view). The title builder can contain `Text(attributedString)`.

**Styles:**
- `.labelStyle(.automatic)` — default for context
- `.labelStyle(.titleAndIcon)` — both icon and title
- `.labelStyle(.titleOnly)` — title only
- `.labelStyle(.iconOnly)` — icon only
- Custom styles via `LabelStyle` protocol

**Customization:**
- `.font()`, `.foregroundStyle()` apply to the label content
- Custom `title:` and `icon:` closures accept any View
- Full accessibility: title is automatically the accessibility label

**Limitations:**
- Not a text input; display only
- No text selection
- No editing

**iOS version:** iOS 14+.

---

### 6. .searchable Modifier (Search Input)

**What it is:** A modifier that adds a system search bar to a NavigationStack/NavigationView. Not a standalone view but a text input mechanism.

**When to use:** Filtering lists, searching content, any searchable interface.

**Lines:** Single line.

**Rich text support:** No.

**Customization:**
- `prompt:` for placeholder text
- `placement:` for positioning (`.automatic`, `.navigationBarDrawer`, `.sidebar`, `.toolbar`)
- Search suggestions via closure
- `.searchScopes()` for scope bar
- `.onSubmit(of: .search)` for search submission
- `isPresented` binding (iOS 17+) for tracking active state

**Limitations:**
- Must be inside a NavigationStack/NavigationView
- Cannot be used standalone like a TextField
- No token support (unlike UISearchTextField)

**iOS version:** iOS 15+. iOS 16+ (search scopes, suggestions). iOS 17+ (isPresented binding).

---

## PART 2: UIKit Views

---

### 7. UITextView (Multi-Line Rich Text)

**What it is:** The primary multi-line text editing/display view in UIKit. A UIScrollView subclass with full TextKit integration.

**When to use:** Notes editors, document editing, code editors, rich text display, chat message display, any multi-line text scenario on iOS.

**Lines:** Unlimited multi-line. Scrollable. `textContainer.maximumNumberOfLines` to limit (0 = unlimited).

**Rich text support:** Full. Supports any NSAttributedString attributes including paragraph styles, text attachments, links, custom attributes.

**TextKit integration:**
- TextKit 2 by default (iOS 16+). `textView.textLayoutManager` to access.
- TextKit 1 via `UITextView(usingTextLayoutManager: false)`.
- **CRITICAL:** Accessing `textView.layoutManager` triggers irreversible TextKit 1 fallback.
- Viewport-based layout for performance with large documents (TextKit 2).
- Custom layout fragments, exclusion paths, multi-column layout.

**Key properties:**
- `text` / `attributedText` for content
- `isEditable`, `isSelectable` for interaction mode
- `dataDetectorTypes` for auto-detected links, phone numbers, addresses
- `typingAttributes` for formatting at cursor
- `textContainerInset` for padding
- `isScrollEnabled` — set `false` for auto-sizing to content
- `allowsEditingTextAttributes` for user-controlled formatting (BIU bar)

**As display-only (isEditable=false):**
- Rich text display with selectable text and tappable links
- Set `isEditable = false`, `isSelectable = true`
- Better than UILabel when you need: text selection, link tapping, TextKit layout queries, exclusion paths
- Remove padding: `textContainerInset = .zero`, `textContainer.lineFragmentPadding = 0`

**Writing Tools:** Automatic support (iOS 18+). `writingToolsBehavior` property. Must use TextKit 2 for full experience. `isWritingToolsActive` property to detect activity.

**Limitations:**
- No intrinsic content size when `isScrollEnabled = true` (must set height constraint or disable scrolling)
- Heavier than UILabel for simple display
- TextKit 1 fallback is irreversible once triggered
- No built-in line numbers

**iOS version:** iOS 2+. TextKit 2 default: iOS 16+. Writing Tools: iOS 18+.

---

### 8. UITextField (Single-Line Input)

**What it is:** A single-line text input control for UIKit.

**When to use:** Form fields, name/email/phone input, search input, any single-line text entry.

**Lines:** Single line only. No multi-line support.

**Rich text support:** Limited. Has `attributedText` and `attributedPlaceholder` properties for display, but no TextKit API access. Cannot do per-character formatting during editing.

**Key properties:**
- `text`, `attributedText`, `placeholder`, `attributedPlaceholder`
- `font`, `textColor`, `textAlignment`
- `borderStyle`: `.none`, `.line`, `.bezel`, `.roundedRect`
- `clearButtonMode` for X button
- `leftView`, `rightView` for accessory views
- `isSecureTextEntry` for password mode
- `keyboardType`, `returnKeyType`, `textContentType`

**Delegate:**
- `UITextFieldDelegate` for should/did begin/end editing, shouldChangeCharacters (live validation), shouldReturn

**TextKit:** Uses TextKit 2 internally (iOS 15+). No public layoutManager access. No fallback concerns.

**Limitations:**
- Single line only; cannot expand
- No scrolling
- No TextKit API access for custom layout
- No find/replace
- No text attachments

**iOS version:** iOS 2+. TextKit 2 internal: iOS 15+.

---

### 9. UILabel (Display Only)

**What it is:** A non-editable, non-selectable text display view. The most lightweight text view in UIKit.

**When to use:** Titles, captions, body text display, any read-only text where selection is not needed.

**Lines:** `numberOfLines = 0` for unlimited. Default is 1.

**Rich text support:** Yes (display only) via `attributedText`. Supports full NSAttributedString rendering.

**Key properties:**
- `text`, `attributedText`
- `font`, `textColor`, `textAlignment`
- `numberOfLines` (0 = unlimited)
- `lineBreakMode`
- `adjustsFontSizeToFitWidth`, `minimumScaleFactor` for auto-shrinking
- `preferredMaxLayoutWidth` for Auto Layout intrinsic size

**TextKit:** Uses TextKit 2 internally (iOS 16+). No public API access. Cannot query glyph rects, line fragment info, or perform hit testing against layout.

**Limitations:**
- No editing, no selection, no copying
- No TextKit API access (use UITextView with `isEditable = false` if you need layout queries)
- No tappable links (use UITextView for that)
- No scrolling
- Rendering may differ between iOS 15 (TextKit 1) and iOS 16+ (TextKit 2) due to internal engine change

**iOS version:** iOS 2+. TextKit 2 internal: iOS 16+.

---

### 10. UISearchTextField (Search Input with Tokens)

**What it is:** A UITextField subclass optimized for search with token support. Used inside UISearchBar/UISearchController.

**When to use:** Search interfaces with filter tokens (e.g., Mail app search with "From:", "Subject:" chips).

**Lines:** Single line.

**Rich text support:** No.

**Token support:**
- `tokens` property: array of `UISearchToken` objects
- Each token has text and optional icon
- Tokens appear contiguously before the search text
- `insertToken(_:at:)`, `removeToken(at:)`
- `tokenBackgroundColor` for styling
- `allowsCopyingTokens`, `allowsDeletingTokens` for user interaction control
- Tokens cannot be placed after text (always before)

**Limitations:**
- Single line only
- Tokens only before text, not inline
- Only available via UISearchBar/UISearchController by default
- No equivalent in SwiftUI (must use UIViewRepresentable)

**iOS version:** iOS 13+.

---

## PART 3: AppKit Views

---

### 11. NSTextView (Multi-Line Rich Text — macOS)

**What it is:** The primary text editing view for macOS. Subclass of NSText. Full TextKit integration. The most powerful text view on any Apple platform.

**When to use:** Document editors, code editors, rich text editors, any text editing scenario on macOS.

**Lines:** Unlimited multi-line. Scrollable (must be embedded in NSScrollView).

**Rich text support:** Full. NSAttributedString with all attributes, text attachments, tables, lists.

**TextKit integration:**
- TextKit 2 by default (macOS Ventura 13+).
- Has `willSwitchToNSLayoutManagerNotification` / `didSwitchToNSLayoutManagerNotification` for fallback detection (macOS only).
- Full TextKit 1 and TextKit 2 API access.
- Manual text system wiring: NSTextStorage -> NSLayoutManager -> NSTextContainer -> NSTextView (TextKit 1) or NSTextContentStorage -> NSTextLayoutManager -> NSTextContainer -> NSTextView (TextKit 2).

**Unique capabilities (vs UITextView):**
- `isRichText` property to toggle rich text mode
- `usesRuler` — built-in ruler for paragraph formatting
- `usesFontPanel` — automatic Font panel integration
- `usesInspectorBar` — inspector bar for formatting
- `allowsUndo` — built-in undo manager
- `isFieldEditor` — field editor mode
- `complete(_:)` — built-in text completion
- Automatic spelling/grammar checking UI
- Link, list, and table support built-in
- `attributedString()` method (not property) to get content
- `textStorage` property for direct TextKit access

**Scroll view setup:**
```
NSScrollView > NSClipView > NSTextView
```
Must create via `NSTextView.scrollableTextView()` or manual NSScrollView embedding.

**Writing Tools:** Automatic support (macOS 15+). Must use TextKit 2 for full experience.

**Limitations:**
- Must be embedded in NSScrollView for scrolling
- Complex setup compared to UITextView
- Shared field editor pattern can cause unexpected TextKit fallback across windows

**macOS version:** macOS 10.0+. TextKit 2 default: macOS Ventura (13+).

---

### 12. NSTextField (Single/Multi-Line — macOS)

**What it is:** A text field for display or single-line input. Uses the field editor pattern — a shared NSTextView handles actual editing.

**When to use:** Form fields, labels (non-editable), single-line inputs, wrapping text display.

**Lines:**
- Default: Single line
- `init(wrappingLabelWithString:)` — creates a wrapping, non-editable label
- Layout set to "Wraps" — text wraps to multiple lines but Return key commits editing (does not insert newline)
- `maximumNumberOfLines` to limit

**Rich text support:** Has `attributedStringValue` property. Can display attributed text. Editing is limited by the field editor.

**Field editor architecture:**
- All NSTextFields in a window share a single NSTextView (the field editor)
- When a text field becomes first responder, the field editor inserts itself
- One field editor per window (memory efficient)
- **CRITICAL:** If ANY text field triggers TextKit 1 fallback on the field editor, ALL text fields in that window are affected
- Custom field editor via `NSWindowDelegate.windowWillReturnFieldEditor(_:to:)`

**Key properties:**
- `stringValue`, `attributedStringValue`
- `placeholderString`, `placeholderAttributedString`
- `font`, `textColor`, `alignment`
- `isBezeled`, `isBordered`, `isEditable`, `isSelectable`
- `lineBreakMode`, `maximumNumberOfLines`

**Convenience initializers:**
- `NSTextField(labelWithString:)` — non-editable, non-selectable label
- `NSTextField(wrappingLabelWithString:)` — wrapping non-editable label
- `NSTextField(labelWithAttributedString:)` — attributed label
- `NSTextField(string:)` — editable text field

**Limitations:**
- Return key commits editing, does not insert newline (even in wrapping mode)
- For true multi-line editing with newlines, use NSTextView instead
- Shared field editor means TextKit configuration affects all fields in window
- No direct TextKit API access on the text field itself (must access field editor)

**macOS version:** macOS 10.0+. TextKit 2 field editor default: macOS Monterey (12+).

---

### 13. NSSecureTextField (Password — macOS)

**What it is:** An NSTextField subclass that masks input with bullet characters for password entry.

**When to use:** Password fields, sensitive data input on macOS.

**Lines:** Single line only.

**Rich text support:** No.

**Security features:**
- Displays bullets instead of actual text
- Prevents copy and cut operations
- Enters Secure Keyboard Entry mode when first responder (blocks keyloggers)
- Restores previous Secure Keyboard Entry state when resigning first responder

**Limitations:**
- Single line only
- No copy/paste of text content
- No show/hide toggle (must implement manually)
- Same field editor constraints as NSTextField

**macOS version:** macOS 10.0+.

---

### 14. NSTokenField (Token Input — macOS)

**What it is:** An NSTextField subclass that converts text into visually distinct tokens (chips/tags).

**When to use:** Tag input, email recipient fields (like Mail.app To: field), any tokenized text entry.

**Lines:** Single line with horizontal scrolling, or wraps tokens to multiple lines depending on configuration.

**Rich text support:** No (tokens are discrete objects, not rich text).

**Token capabilities:**
- Automatic tokenization on delimiter (default: comma)
- Delegate-based auto-completion
- Token editing, deletion, drag-and-drop
- Custom token display via represented objects
- Tokenizing character set is configurable

**Limitations:**
- macOS only (no UIKit equivalent — "puzzling omission from UIKit")
- UISearchTextField has token support on iOS but is search-specific
- No SwiftUI equivalent (must use NSViewRepresentable)
- Limited visual customization of token appearance

**macOS version:** macOS 10.4+.

---

### 15. NSComboBox (Dropdown + Text Input — macOS)

**What it is:** A text field combined with a dropdown list of predefined options. User can type a custom value or select from the list.

**When to use:** Font selectors, predefined options with custom entry allowed, any "select or type" scenario.

**Lines:** Single line.

**Rich text support:** No.

**Capabilities:**
- Predefined list of items (internal or via data source)
- User can type any value (not restricted to list)
- Dropdown button to reveal options
- Auto-completion via delegate

**Limitations:**
- macOS only
- No UIKit equivalent (UIPickerView is selection-only, not combined)
- No SwiftUI equivalent (must use NSViewRepresentable, or use Picker + TextField separately)
- Limited styling options

**macOS version:** macOS 10.0+.

---

### 16. NSSearchField (Search — macOS)

**What it is:** An NSTextField subclass styled for search with rounded corners and a search icon.

**When to use:** Search bars in macOS applications, filtering interfaces.

**Lines:** Single line.

**Rich text support:** No.

**Unique capabilities:**
- Search icon and cancel button built-in
- Recents menu support — automatically tracks recent searches
- System-wide search sharing: entering a search term in one NSSearchField makes it available in every other search field on the system
- Search menu template for search options
- `sendsWholeSearchString` / `sendsSearchStringImmediately` for controlling when searches fire

**Limitations:**
- macOS only (use .searchable modifier or UISearchBar on iOS)
- No token support (unlike UISearchTextField)
- Single line only

**macOS version:** macOS 10.3+.

---

## PART 4: Special Purpose Views

---

### 17. WKWebView with contentEditable (Web-Based Rich Text)

**What it is:** Using a WKWebView to display an HTML element with `contenteditable="true"`, creating a web-based rich text editor within a native app.

**When to use:** Email composers requiring HTML output, WYSIWYG editors, scenarios where HTML/CSS formatting is the target output, or when native text views lack needed formatting features.

**Lines:** Unlimited multi-line.

**Rich text support:** Full HTML/CSS — the most flexible rich text support available. Any formatting achievable with HTML.

**Capabilities:**
- Full HTML formatting: fonts, colors, alignment, lists, tables, images, headings
- `document.execCommand()` for formatting commands (bold, italic, insertLink, etc.)
- BIU (bold/italic/underline) from iOS long-press menu
- Keyboard shows automatically when tapping contenteditable element
- JavaScript bridge for communication between native code and editor

**Limitations:**
- JavaScript bridge is asynchronous (WKWebView), complicating state sync
- `element.focus()` from `evaluateJavaScript` does not always show keyboard
- Scrolling quirks when contenteditable element has touch listeners
- Hardware keyboard text selection issues in contenteditable
- Significant complexity vs native views
- No TextKit integration
- No Writing Tools integration
- Performance overhead of web rendering
- Harder to match native look and feel

**iOS version:** iOS 8+ (WKWebView). Works on all Apple platforms.

---

### 18. UITextView as Display-Only (isEditable=false)

**What it is:** A UITextView configured as read-only for rich text display. An alternative to UILabel when you need text interaction features.

**When to use:** Displaying rich formatted text with tappable links, selectable text, data detection (phone numbers, addresses), or when you need TextKit layout queries on display-only text.

**Lines:** Unlimited multi-line, scrollable.

**Advantages over UILabel:**
- Text selection and copy
- Tappable links
- Data detectors (phone, address, date, URL)
- TextKit API access for layout queries
- Exclusion paths for text wrapping around shapes
- Text attachments (inline images)

**Configuration:**
```swift
textView.isEditable = false
textView.isSelectable = true
textView.isScrollEnabled = false  // For auto-sizing
textView.textContainerInset = .zero
textView.textContainer.lineFragmentPadding = 0
textView.dataDetectorTypes = [.link, .phoneNumber]
```

**Limitations:**
- Heavier than UILabel (UIScrollView subclass)
- No intrinsic content size when scrolling enabled
- Responds to keyboard events even when non-editable (can interfere with responder chain)

**iOS version:** iOS 2+.

---

### 19. UITextInput Protocol (Custom Text Views)

**What it is:** A protocol for building completely custom text input views from scratch. Requires implementing text positions, ranges, marked text, geometry, and hit testing.

**When to use:** Custom code editors, game text input, terminal emulators, any text input that cannot be achieved by subclassing existing views.

**Protocol hierarchy:**
```
UIResponder
    > UIKeyInput (minimal: insertText, deleteBackward, hasText)
        > UITextInput (full: positions, ranges, marked text, geometry, selection)
```

**UIKeyInput (simpler alternative):** Just three methods. Sufficient for basic Latin keyboard input. Does NOT support: CJK multistage input, autocorrection, selection, copy/paste.

**UITextInput (full):** ~30 required methods covering text access, position arithmetic, range creation, selection, marked text (CJK/IME), geometry for system UI, hit testing, document bounds, tokenizer for word/sentence boundaries.

**iOS 17+ additions:**
- `UITextSelectionDisplayInteraction` — system selection UI (cursor, handles, highlights) for custom views
- `UITextLoupeSession` — magnifier for precise cursor positioning

**Limitations:**
- Enormous implementation effort (~30 methods)
- Must do own text layout and font management (use Core Text)
- Must correctly implement marked text for CJK input
- Must call `inputDelegate` methods when modifying text/selection externally
- Must provide accurate geometry for system UI positioning

**iOS version:** iOS 3.2+ (UITextInput). iOS 17+ (UITextSelectionDisplayInteraction).

---

### 20. NSTextInputClient Protocol (Custom Text Views — macOS)

**What it is:** The macOS equivalent of UITextInput for building custom text input views in AppKit.

**When to use:** Custom macOS text engines, code editors, terminal emulators built on AppKit.

**Key methods:** `insertText(_:replacementRange:)`, `setMarkedText(_:selectedRange:replacementRange:)`, `unmarkText()`, `selectedRange()`, `markedRange()`, geometry methods, attributed content access.

**NSTextInputContext:** Manages input context (keyboard layout, input method). Must call `invalidateCharacterCoordinates()` after layout changes.

**macOS Sonoma+ additions:**
- `NSTextInsertionIndicator` — system text cursor for custom views

**macOS version:** macOS 10.0+ (as part of text input protocols).

---

## PART 5: TextKit Architecture

---

### TextKit 2 Components

| Component | Role |
|-----------|------|
| `NSTextContentManager` | High-level coordinator; document as semantic elements |
| `NSTextContentStorage` | Bridge to NSTextStorage; transactional edits |
| `NSTextLayoutManager` | Layout orchestration; creates layout fragments on-demand |
| `NSTextContainer` | Geometry constraints for text layout |
| `NSTextViewportLayoutController` | Performance: only lays out visible fragments |
| `NSTextLayoutFragment` | Immutable laid-out text blocks |
| `NSTextLineFragment` | Individual visual lines within fragments |
| `NSTextElement` | Abstract content unit (paragraph, attachment) |

**TextKit 2 vs TextKit 1:**

| Aspect | TextKit 1 | TextKit 2 |
|--------|-----------|-----------|
| Core unit | Glyphs | Text elements/fragments |
| Layout | Contiguous (entire document) | On-demand, viewport-aware |
| Content model | Linear character stream | Semantic element hierarchy |
| Edits | Direct storage mutation | Transactional blocks |
| Large documents | Slow (processes all) | Fast (viewport only) |
| Complex scripts | Error-prone | Correct by default |
| Default since | Always (legacy) | iOS 16 / macOS 13 |

---

## PART 6: Decision Matrix

---

### "I need a small name input field"
**Best choice:** SwiftUI `TextField` / UIKit `UITextField`
- Single line, placeholder support, keyboard type customization, text content type for AutoFill (.name, .emailAddress)

### "I need a multi-line notes editor"
**Best choice:** SwiftUI `TextEditor` (iOS 26+ for rich text) / UIKit `UITextView` / AppKit `NSTextView`
- For plain text notes: TextEditor (iOS 14+)
- For rich text notes: TextEditor with AttributedString (iOS 26+) or UITextView with NSAttributedString
- For full-featured notes: UITextView or NSTextView with TextKit 2

### "I need a code editor with syntax highlighting"
**Best choice:** UIKit `UITextView` with TextKit 2 / AppKit `NSTextView` with TextKit 2
- SwiftUI has no native syntax highlighting support
- Use custom NSTextLayoutFragment rendering or a library like Sourceful/STTextView
- TextKit 2 viewport layout is essential for large files
- Third-party: STTextView (TextKit 2 native, macOS/iOS), Sourceful, Highlightr

### "I need to display rich formatted text (not editable)"
**Best choice depends on complexity:**
- Simple inline formatting (bold/italic/links): SwiftUI `Text` with AttributedString or Markdown
- Full paragraph styles, attachments, data detection: `UITextView` with `isEditable = false`
- macOS: `NSTextView` with `isEditable = false`
- Full Markdown with headings/lists/tables: Third-party (MarkdownUI) or UITextView with manual rendering

### "I need a chat message composer"
**Best choice:** SwiftUI `TextField(axis: .vertical)` with `.lineLimit(1...6)` (iOS 16+)
- Starts as single line, grows as user types (iMessage behavior)
- Has placeholder text support
- For pre-iOS 16: TextEditor with custom sizing logic

### "I need a search bar"
**Best choice:** SwiftUI `.searchable()` modifier (iOS 15+) / UIKit `UISearchController` + `UISearchBar`
- SwiftUI: `.searchable(text:prompt:)` on NavigationStack
- UIKit with tokens: UISearchTextField
- macOS: NSSearchField (with system-wide search term sharing)

### "I need a password field"
**Best choice:** SwiftUI `SecureField` / UIKit `UITextField` with `isSecureTextEntry = true` / AppKit `NSSecureTextField`
- All mask input with bullets
- All support AutoFill with `.textContentType(.password)`
- For show/hide toggle: switch between SecureField/TextField or toggle isSecureTextEntry

### "I need a Markdown editor with preview"
**Best choice:** Split view: `TextEditor` (plain text editing) + `Text` or WKWebView (rendered preview)
- iOS 26+: TextEditor with AttributedString for inline Markdown editing
- Pre-iOS 26: TextEditor for plain Markdown source, SwiftUI Text or MarkdownUI for preview
- For WYSIWYG Markdown: UITextView with custom TextKit rendering or WKWebView with contentEditable

### "I need an email body composer with rich text"
**Best choice:** `UITextView` with `allowsEditingTextAttributes = true` / WKWebView with contentEditable
- UITextView: Native BIU formatting bar, text attachments for images, HTML export via NSAttributedString
- WKWebView: Full HTML output, most flexible formatting, but complex JavaScript bridge
- iOS 26+: TextEditor with AttributedString for simpler rich text (but no HTML output)
- macOS: NSTextView with ruler, font panel, inspector bar

### "I need a comments/review text area"
**Best choice:** SwiftUI `TextField(axis: .vertical)` with `.lineLimit(3...8)` or `TextEditor`
- TextField (axis: .vertical): Better for shorter comments with placeholder text
- TextEditor: Better for longer reviews with no length expectation
- Character count: Implement via `.onChange` modifier

### "I need a text field that grows as you type"
**Best choice:** SwiftUI `TextField(axis: .vertical)` (iOS 16+)
- Starts single-line, expands as content grows
- `.lineLimit(n)` caps growth at n lines, then scrolls
- `.lineLimit(2...5)` for min/max range
- Pre-iOS 16: UITextView with `isScrollEnabled = false` and Auto Layout, updating height constraint on `textViewDidChange`

---

## PART 7: Quick Reference Table

| View | Framework | Input? | Lines | Rich Text | TextKit Access | Placeholder | Min OS |
|------|-----------|--------|-------|-----------|---------------|-------------|--------|
| Text | SwiftUI | No | Multi | Display only (Markdown, AttributedString) | No | N/A | iOS 13 |
| TextField | SwiftUI | Yes | 1 (multi w/ axis iOS 16+) | No | No | Yes | iOS 13 |
| TextEditor | SwiftUI | Yes | Multi | iOS 26+ (AttributedString) | No | No (workaround) | iOS 14 |
| SecureField | SwiftUI | Yes | 1 | No | No | Yes | iOS 13 |
| Label | SwiftUI | No | 1 | Via title builder | No | N/A | iOS 14 |
| .searchable | SwiftUI | Yes | 1 | No | No | Yes (prompt) | iOS 15 |
| UITextView | UIKit | Yes | Multi | Full | Full (TK1+TK2) | No (manual) | iOS 2 |
| UITextField | UIKit | Yes | 1 | Limited | No | Yes | iOS 2 |
| UILabel | UIKit | No | Multi | Display only | No | N/A | iOS 2 |
| UISearchTextField | UIKit | Yes | 1 | No | No | Yes | iOS 13 |
| NSTextView | AppKit | Yes | Multi | Full | Full (TK1+TK2) | No | macOS 10.0 |
| NSTextField | AppKit | Yes | 1 (wraps) | Limited | Via field editor | Yes | macOS 10.0 |
| NSSecureTextField | AppKit | Yes | 1 | No | No | Yes | macOS 10.0 |
| NSTokenField | AppKit | Yes | 1+ | No (tokens) | No | Yes | macOS 10.4 |
| NSComboBox | AppKit | Yes | 1 | No | No | No | macOS 10.0 |
| NSSearchField | AppKit | Yes | 1 | No | No | Yes | macOS 10.3 |
| WKWebView (contentEditable) | WebKit | Yes | Multi | Full HTML/CSS | No (web) | Via HTML | iOS 8 |
| UITextInput protocol | UIKit | Custom | Custom | Custom | Custom | Custom | iOS 3.2 |
| NSTextInputClient | AppKit | Custom | Custom | Custom | Custom | Custom | macOS 10.0 |

---

## PART 8: UIKit & AppKit Detailed Configuration Reference

---

### UITextView — Full Configuration

#### TextKit Mode Selection

```swift
// TextKit 2 (default on iOS 16+)
let textView = UITextView()

// Explicit TextKit 2
let textView = UITextView(usingTextLayoutManager: true)

// Explicit TextKit 1
let textView = UITextView(usingTextLayoutManager: false)
```

**Interface Builder:** Attribute Inspector > "Text Layout" > System Default / TextKit 2 / TextKit 1

#### Detecting Current Mode

```swift
if let textLayoutManager = textView.textLayoutManager {
    // TextKit 2 mode
    let contentStorage = textLayoutManager.textContentManager as? NSTextContentStorage
} else {
    // TextKit 1 mode (or fell back)
    let layoutManager = textView.layoutManager
}
```

**CRITICAL: Accessing `textView.layoutManager` triggers irreversible TextKit 1 fallback.** The view replaces its NSTextLayoutManager with an NSLayoutManager permanently.

```swift
// WRONG -- triggers fallback even as a check
if textView.layoutManager != nil { ... }

// CORRECT -- check TextKit 2 first
if textView.textLayoutManager != nil {
    // TextKit 2
} else {
    // Already TextKit 1
    let lm = textView.layoutManager
}
```

**Debug fallback:** Set symbolic breakpoint on `_UITextViewEnablingCompatibilityMode`

#### Fallback Triggers

UITextView falls back to TextKit 1 when:
- `textView.layoutManager` is accessed
- `textView.textContainer.layoutManager` is accessed
- Incompatible content (some attachment types)
- Some delegate methods only available in TextKit 1

#### Key Properties

```swift
textView.text: String?                    // Plain text
textView.attributedText: NSAttributedString? // Attributed text
textView.font: UIFont?                    // Default font
textView.textColor: UIColor?              // Default text color
textView.textAlignment: NSTextAlignment   // .left, .center, .right, .justified, .natural
textView.isEditable: Bool                 // Allow editing
textView.isSelectable: Bool               // Allow selection
textView.dataDetectorTypes: UIDataDetectorTypes  // .link, .phoneNumber, .address, etc.
textView.textContainerInset: UIEdgeInsets // Inset from view edges
textView.typingAttributes: [NSAttributedString.Key: Any]  // Attributes for new text
```

#### Text Container Access

```swift
textView.textContainer                    // The NSTextContainer
textView.textContainer.lineFragmentPadding  // Padding within container (default: 5)
textView.textContainer.maximumNumberOfLines // Line limit (0 = unlimited)
textView.textContainer.exclusionPaths       // Areas to exclude from layout
```

#### Scrolling

UITextView is a UIScrollView subclass:
```swift
textView.isScrollEnabled = true
textView.scrollRangeToVisible(NSRange(location: 100, length: 0))
```

---

### UITextField — Full Configuration

Single-line text input. Uses TextKit 2 since iOS 15. No public layout manager access.

```swift
textField.text: String?
textField.attributedText: NSAttributedString?
textField.placeholder: String?
textField.attributedPlaceholder: NSAttributedString?
textField.font: UIFont?
textField.textColor: UIColor?
textField.textAlignment: NSTextAlignment
textField.borderStyle: UITextField.BorderStyle  // .none, .line, .bezel, .roundedRect
textField.clearButtonMode: UITextField.ViewMode
textField.leftView: UIView?
textField.rightView: UIView?
```

**No TextKit 1 fallback concerns** — no public `layoutManager` property was ever exposed.

---

### UILabel — Full Configuration

Display-only text. No editing. No public text system API.

```swift
label.text: String?
label.attributedText: NSAttributedString?
label.font: UIFont!
label.textColor: UIColor!
label.textAlignment: NSTextAlignment
label.numberOfLines: Int        // 0 = unlimited
label.lineBreakMode: NSLineBreakMode
label.adjustsFontSizeToFitWidth: Bool
label.minimumScaleFactor: CGFloat
label.allowsDefaultTighteningForTruncation: Bool
label.preferredMaxLayoutWidth: CGFloat  // For Auto Layout intrinsic size
```

**Uses TextKit 2 internally (iOS 16+)** but no API to access it.

---

### NSTextView — Full Configuration

Primary text editing view for macOS. Subclass of NSText.

#### TextKit Mode Selection

**macOS Ventura (13+):** TextKit 2 by default.

```swift
// TextKit 2 (explicit creation)
let textLayoutManager = NSTextLayoutManager()
let textContainer = NSTextContainer(size: CGSize(width: width, height: 0))
textLayoutManager.textContainer = textContainer
let textView = NSTextView(frame: bounds, textContainer: textContainer)

// TextKit 1 (legacy path)
let textView = NSTextView(frame: bounds)
// If on macOS 13+, this is TextKit 2.
// To force TextKit 1, access layoutManager (triggers fallback):
_ = textView.layoutManager
```

#### Fallback Notifications (macOS only)

```swift
NotificationCenter.default.addObserver(
    forName: NSTextView.willSwitchToNSLayoutManagerNotification,
    object: textView, queue: .main
) { notification in
    print("About to fall back to TextKit 1")
}

NotificationCenter.default.addObserver(
    forName: NSTextView.didSwitchToNSLayoutManagerNotification,
    object: textView, queue: .main
) { notification in
    print("Fell back to TextKit 1")
}
```

#### Key Properties

```swift
textView.string: String                    // Plain text content
textView.attributedString(): NSAttributedString  // Full attributed content
textView.textStorage: NSTextStorage?       // Direct storage access
textView.textLayoutManager: NSTextLayoutManager?  // TextKit 2
textView.layoutManager: NSLayoutManager?   // TextKit 1 (triggers fallback!)
textView.textContainer: NSTextContainer?
textView.isEditable: Bool
textView.isSelectable: Bool
textView.isRichText: Bool                  // Allow rich text editing
textView.isFieldEditor: Bool               // Field editor mode
textView.usesRuler: Bool
textView.usesFontPanel: Bool
textView.allowsUndo: Bool
textView.typingAttributes: [NSAttributedString.Key: Any]
```

#### Cocoa Text System Setup

```swift
// Manual setup (TextKit 1)
let textStorage = NSTextStorage()
let layoutManager = NSLayoutManager()
textStorage.addLayoutManager(layoutManager)
let container = NSTextContainer(containerSize: CGSize(width: 500, height: .greatestFiniteMagnitude))
layoutManager.addTextContainer(container)
let textView = NSTextView(frame: frame, textContainer: container)

// Manual setup (TextKit 2)
let textContentStorage = NSTextContentStorage()
let textLayoutManager = NSTextLayoutManager()
textContentStorage.addTextLayoutManager(textLayoutManager)
let container = NSTextContainer(size: CGSize(width: 500, height: 0))
textLayoutManager.textContainer = container
let textView = NSTextView(frame: frame, textContainer: container)
```

---

### NSTextField — Full Configuration

Single-line text display/input. Uses **field editor** pattern.

```swift
textField.stringValue: String
textField.attributedStringValue: NSAttributedString
textField.placeholderString: String?
textField.placeholderAttributedString: NSAttributedString?
textField.font: NSFont?
textField.textColor: NSColor?
textField.alignment: NSTextAlignment
textField.isBezeled: Bool
textField.isBordered: Bool
textField.isEditable: Bool
textField.isSelectable: Bool
textField.lineBreakMode: NSLineBreakMode
textField.maximumNumberOfLines: Int
textField.preferredMaxLayoutWidth: CGFloat
```

### The Field Editor

NSTextField does NOT contain its own text editing infrastructure. macOS uses a **shared NSTextView** called the field editor:

```swift
// Get the field editor for a window
let fieldEditor = window.fieldEditor(true, for: textField) as? NSTextView
```

**Key behaviors:**
- One field editor per window (shared among all text fields)
- When a text field becomes first responder, the field editor inserts itself into the view hierarchy
- Field editor handles all editing, selection, input
- Uses TextKit 2 by default (macOS Monterey+)

**Critical pitfall:** If ANY NSTextField subclass accesses the field editor's `layoutManager`, ALL field editors in that window fall back to TextKit 1.

#### Custom Field Editor

```swift
// In NSWindowDelegate
func windowWillReturnFieldEditor(_ sender: NSWindow,
                                  to client: Any?) -> Any? {
    if client is MySpecialTextField {
        return myCustomFieldEditor  // Custom NSTextView instance
    }
    return nil  // Use default
}
```

---

## Choosing a Text View

| Need | UIKit | AppKit |
|------|-------|--------|
| Multi-line editable rich text | UITextView | NSTextView |
| Single-line text input | UITextField | NSTextField |
| Display-only text | UILabel | NSTextField (non-editable) |
| Custom text rendering | UITextView + custom fragments | NSTextView + custom fragments |
| Multi-page/column layout | Multiple UITextView + shared storage | Multiple NSTextView + shared storage |
| Code editor | UITextView (TextKit 2) | NSTextView (TextKit 2) |

## TextKit 1 vs 2: When to Use Which

### Use TextKit 2 (Default) When:
- Building new text views
- Need viewport-based performance for large documents
- Want Writing Tools integration (iOS 18+)
- Working with international text (Arabic, Devanagari, CJK)
- Custom rendering via layout fragments

### Use TextKit 1 When:
- Need glyph-level access (custom glyph substitution, glyph inspection)
- Maintaining legacy code that heavily uses NSLayoutManager
- Need APIs with no TextKit 2 equivalent yet
- Using features that trigger automatic fallback

## Common Pitfalls

1. **Accessing `layoutManager` triggers fallback** — On both UITextView and NSTextView. Check `textLayoutManager` first.
2. **Field editor is shared** — One TextKit 1 fallback in any text field affects all text fields in the window (macOS).
3. **UILabel has no text system API** — Cannot access layout internals. Use UITextView with `isEditable = false` if you need layout queries.
4. **NSTextView is not NSTextField** — They have different inheritance hierarchies and different text system integration.
5. **UITextView is a UIScrollView** — Setting `isScrollEnabled = false` changes intrinsic content size behavior. Useful for auto-sizing.
6. **SwiftUI Text ignores most AttributedString attributes** — Only ~10 attributes render. paragraphStyle, shadow, attachment, and many others are silently dropped.
7. **SwiftUI.Font is not UIFont/NSFont** — Different type systems. Use `.uiKit.font` with UIFont for UITextView content, `.font` (SwiftUI.Font) for SwiftUI Text.
8. **TextEditor has no placeholder** — Must overlay a Text view with ZStack + allowsHitTesting(false).
9. **TextField axis: .vertical is not TextEditor** — TextField grows from one line; TextEditor is a fixed scrollable area. Choose based on UX intent.
10. **NSTextField wrapping does not equal multi-line editing** — Return key commits editing; it does not insert a newline. Use NSTextView for true multi-line input on macOS.
