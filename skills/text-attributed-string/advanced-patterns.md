# Attributed String Advanced Patterns

Use this sidecar when `text-attributed-string` needs deeper detail on custom scopes, paragraph-style setup, or the attribute catalog without loading every appendix into the main skill.

## Custom Attributes

### Step 1: Define Attribute Keys

```swift
enum HighlightColorAttribute: AttributedStringKey {
    typealias Value = String
    static let name = "highlightColor"
}

enum UserIDAttribute: CodableAttributedStringKey {
    typealias Value = String
    static let name = "userID"
}

enum SpoilerAttribute: CodableAttributedStringKey, MarkdownDecodableAttributedStringKey {
    typealias Value = Bool
    static let name = "spoiler"
    static let markdownName = "spoiler"
}
```

### Step 2: Create an Attribute Scope

```swift
extension AttributeScopes {
    struct MyAppAttributes: AttributeScope {
        let highlightColor: HighlightColorAttribute
        let userID: UserIDAttribute
        let spoiler: SpoilerAttribute
        let foundation: FoundationAttributes
        let uiKit: UIKitAttributes
    }

    var myApp: MyAppAttributes.Type { MyAppAttributes.self }
}
```

### Step 3: Enable Dynamic Lookup

```swift
extension AttributeDynamicLookup {
    subscript<T: AttributedStringKey>(
        dynamicMember keyPath: KeyPath<AttributeScopes.MyAppAttributes, T>
    ) -> T {
        self[T.self]
    }
}
```

### Step 4: Use the Attributes

```swift
var str = AttributedString("Secret message")
str.spoiler = true
str.userID = "user_123"

let md = try AttributedString(
    markdown: "This is ^[hidden](spoiler: true)",
    including: \.myApp
)
```

## NSParagraphStyle

Paragraph-level formatting works with both `NSAttributedString` and `AttributedString`.

### Common Properties

```swift
let style = NSMutableParagraphStyle()
style.alignment = .justified
style.lineSpacing = 4
style.paragraphSpacing = 12
style.paragraphSpacingBefore = 8
style.firstLineHeadIndent = 20
style.headIndent = 10
style.tailIndent = -10
style.lineBreakMode = .byWordWrapping
style.lineBreakStrategy = .standard
style.minimumLineHeight = 20
style.maximumLineHeight = 30
style.lineHeightMultiple = 1.2
style.hyphenationFactor = 0.5
style.baseWritingDirection = .natural
style.allowsDefaultTighteningForTruncation = true
```

### Tab Stops

```swift
style.tabStops = [
    NSTextTab(textAlignment: .left, location: 100),
    NSTextTab(textAlignment: .right, location: 300),
    NSTextTab(textAlignment: .center, location: 200),
    NSTextTab(textAlignment: .decimal, location: 400),
]
style.defaultTabInterval = 36
```

### Text Lists

```swift
let list = NSTextList(markerFormat: .disc, options: 0)
style.textLists = [list]
```

### Using With AttributedString

```swift
var str = AttributedString("Hello")
str.paragraphStyle = style
```

## Persistence & Serialization

### Export Formats

```swift
let range = NSRange(location: 0, length: attrStr.length)

// RTF (no attachments, no custom attributes)
let rtfData = try attrStr.data(from: range,
    documentAttributes: [.documentType: NSAttributedString.DocumentType.rtf])

// RTFD (with attachments)
let rtfdData = try attrStr.data(from: range,
    documentAttributes: [.documentType: NSAttributedString.DocumentType.rtfd])

// HTML (slow, uses WebKit internally)
let htmlData = try attrStr.data(from: range,
    documentAttributes: [.documentType: NSAttributedString.DocumentType.html])

// Plain text (strips all formatting)
let plainData = try attrStr.data(from: range,
    documentAttributes: [.documentType: NSAttributedString.DocumentType.plain])
```

### Import Formats

```swift
// RTF — safe on any thread
let attrStr = try NSAttributedString(data: rtfData,
    options: [.documentType: NSAttributedString.DocumentType.rtf],
    documentAttributes: nil)

// HTML — MUST be on main thread (uses WebKit internally)
let attrStr = try NSAttributedString(data: htmlData,
    options: [
        .documentType: NSAttributedString.DocumentType.html,
        .characterEncoding: String.Encoding.utf8.rawValue
    ],
    documentAttributes: nil)
```

**HTML import is main-thread only.** It uses WebKit internally. Background calls deadlock or crash. It's also slow — not suitable for bulk conversions.

### What Survives Each Format

| Attribute | RTF | RTFD | HTML | NSKeyedArchiver | AttributedString Codable |
|-----------|-----|------|------|-----------------|--------------------------|
| Font (name, size, weight) | Yes | Yes | Approximate | Yes | Yes |
| Foreground/background color | Yes | Yes | Yes | Yes | Yes |
| Underline / strikethrough | Yes | Yes | Yes | Yes | Yes |
| Paragraph style | Yes | Yes | Partial | Yes | Yes |
| Text attachments | **No** | Yes | No | Yes | No |
| Links | Partial | Partial | Yes | Yes | Yes |
| Shadow | No | No | No | Yes | Partial |
| Kern / tracking / baseline | Yes | Yes | No | Yes | Yes |
| **Custom attributes** | **No** | **No** | **No** | **Yes** | Only with custom scope |

### NSKeyedArchiver (Full Fidelity)

The only approach that preserves **everything**, including custom attributes:

```swift
// Archive
let data = try NSKeyedArchiver.archivedData(
    withRootObject: attrStr, requiringSecureCoding: true)

// Unarchive
let restored = try NSKeyedUnarchiver.unarchivedObject(
    ofClass: NSAttributedString.self, from: data)
```

### AttributedString Codable (iOS 15+)

Custom attributes require `@CodableConfiguration`:

```swift
struct Document: Codable {
    @CodableConfiguration(from: \.myApp)
    var body: AttributedString = AttributedString()
}

let data = try JSONEncoder().encode(doc)
let decoded = try JSONDecoder().decode(Document.self, from: data)
```

**Without `@CodableConfiguration` or explicit scope, custom attributes are silently dropped.**

### When to Use Which

| Approach | Best For | Limitation |
|----------|----------|-----------|
| RTF | Interchange with other editors, pasteboard | No attachments, no custom attrs |
| RTFD | Rich text with embedded images | Large files, no custom attrs |
| HTML | Web display, email bodies | Main-thread-only import, lossy, slow |
| NSKeyedArchiver | Full-fidelity persistence within your app | Not portable, binary format |
| AttributedString Codable | Modern Swift, JSON storage | Must declare scopes explicitly |

## Quick Reference

| Key | Value Type | Purpose |
|-----|-----------|---------|
| `.font` | UIFont/NSFont | Typeface and size |
| `.foregroundColor` | UIColor/NSColor | Text color |
| `.backgroundColor` | UIColor/NSColor | Background highlight |
| `.paragraphStyle` | NSParagraphStyle | Paragraph formatting |
| `.kern` | NSNumber (CGFloat) | Character spacing |
| `.tracking` | NSNumber (CGFloat) | Tracking |
| `.strikethroughStyle` | NSNumber (Int) | Strikethrough |
| `.underlineStyle` | NSNumber (Int) | Underline |
| `.underlineColor` | UIColor/NSColor | Underline color |
| `.strokeColor` | UIColor/NSColor | Stroke color |
| `.strokeWidth` | NSNumber (CGFloat) | Stroke width |
| `.shadow` | NSShadow | Drop shadow |
| `.link` | URL or String | Hyperlink |
| `.attachment` | NSTextAttachment | Inline attachment |
| `.baselineOffset` | NSNumber (CGFloat) | Baseline shift |
| `.obliqueness` | NSNumber (CGFloat) | Italic simulation |
| `.expansion` | NSNumber (CGFloat) | Horizontal stretch |
| `.writingDirection` | [NSNumber] | Embedding or override |
| `.ligature` | NSNumber (Int) | Ligature control |
