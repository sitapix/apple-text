---
name: txt-core-text
description: Use when working with Core Text for glyph-level access, custom typesetting, hit testing, font tables, or when TextKit 2 lacks the glyph APIs you need
license: MIT
---

# Core Text for TextKit Developers

Use this skill when you need glyph-level control — either because TextKit 2 has no glyph APIs, or because your use case (custom typesetting, font tables, per-glyph rendering) requires the Core Text layer directly.

## When to Use

- You need glyph positions, advances, or bounding boxes that TextKit 2 hides
- You are doing custom typesetting or non-standard line breaking
- You need font table access or OpenType feature control
- You are rendering text with custom Core Graphics effects per glyph
- You need hit testing or caret positioning outside of a TextKit text container

## Quick Decision

```
Need glyph-level access?
    TextKit 1 available? → Use NSLayoutManager glyph APIs
    TextKit 2 only? → Drop to Core Text (this skill)

Need custom line breaking?
    → CTTypesetter

Need to draw text into a CGContext directly?
    → CTLine or CTFrame

Need font metrics, tables, or OpenType features?
    → CTFont

Need inline non-text elements with custom metrics?
    → CTRunDelegate
```

## Core Guidance

## Architecture

```
CTFramesetter (factory)
    → CTTypesetter (line breaking)
        → CTFrame (laid-out region)
            → CTLine (one visual line)
                → CTRun (contiguous glyphs, same attributes)
                    → CGGlyph[] (actual glyph IDs)
                    → CGPoint[] (positions)
                    → CGSize[]  (advances)
```

Core Text sits directly above Core Graphics. It is a C API using Core Foundation types. Available since iOS 3.2 / macOS 10.5. Both TextKit 1 and TextKit 2 render through Core Text internally — it is the foundation under both, not part of either.

**Thread safety:** Font objects (CTFont, CTFontDescriptor, CTFontCollection) are thread-safe and can be shared across threads. Layout objects (CTTypesetter, CTFramesetter, CTRun, CTLine, CTFrame) are **NOT thread-safe** — use them on a single thread only.

## CTLine — The Most Common Escape Hatch

For most TextKit developers, `CTLine` is the entry point. Create one from an attributed string to get glyph information:

```swift
let attributedString = NSAttributedString(string: "Hello 👋🏽",
    attributes: [.font: UIFont.systemFont(ofSize: 16)])
let line = CTLineCreateWithAttributedString(attributedString)

// Typographic bounds
var ascent: CGFloat = 0, descent: CGFloat = 0, leading: CGFloat = 0
let width = CTLineGetTypographicBounds(line, &ascent, &descent, &leading)
let height = ascent + descent + leading

// Hit testing: point → string index
let index = CTLineGetStringIndexForPosition(line, CGPoint(x: 50, y: 0))

// Caret positioning: string index → x offset
let offset = CTLineGetOffsetForStringIndex(line, 3, nil)

// Image bounds (actual rendered pixels, not typographic)
let ctx = UIGraphicsGetCurrentContext()!
let imageBounds = CTLineGetImageBounds(line, ctx)
```

## CTRun — Glyph-Level Access

Each `CTRun` is a contiguous sequence of glyphs sharing the same attributes:

```swift
let runs = CTLineGetGlyphRuns(line) as! [CTRun]

for run in runs {
    let glyphCount = CTRunGetGlyphCount(run)

    // Get all glyphs
    var glyphs = [CGGlyph](repeating: 0, count: glyphCount)
    CTRunGetGlyphs(run, CFRange(location: 0, length: glyphCount), &glyphs)

    // Get positions (relative to line origin)
    var positions = [CGPoint](repeating: .zero, count: glyphCount)
    CTRunGetPositions(run, CFRange(location: 0, length: glyphCount), &positions)

    // Get advances (width of each glyph)
    var advances = [CGSize](repeating: .zero, count: glyphCount)
    CTRunGetAdvances(run, CFRange(location: 0, length: glyphCount), &advances)

    // Map glyph indices back to string indices (UTF-16)
    var stringIndices = [CFIndex](repeating: 0, count: glyphCount)
    CTRunGetStringIndices(run, CFRange(location: 0, length: glyphCount), &stringIndices)

    // Get the run's attributes
    let attrs = CTRunGetAttributes(run) as! [NSAttributedString.Key: Any]
    let font = attrs[.font] as! CTFont
}
```

## CTFramesetter / CTFrame — Multi-Line Layout

For laying out text into a rectangular (or custom-shaped) region:

```swift
let framesetter = CTFramesetterCreateWithAttributedString(attributedString)

// Suggest frame size for constrained width
let constraint = CGSize(width: 300, height: .greatestFiniteMagnitude)
let suggestedSize = CTFramesetterSuggestFrameSizeWithConstraints(
    framesetter, CFRange(location: 0, length: 0), nil, constraint, nil)

// Create frame in a path
let path = CGPath(rect: CGRect(origin: .zero, size: suggestedSize), transform: nil)
let frame = CTFramesetterCreateFrame(framesetter, CFRange(location: 0, length: 0), path, nil)

// Get lines and origins
let lines = CTFrameGetLines(frame) as! [CTLine]
var origins = [CGPoint](repeating: .zero, count: lines.count)
CTFrameGetLineOrigins(frame, CFRange(location: 0, length: lines.count), &origins)

// Draw the entire frame
CTFrameDraw(frame, context)
```

## CTTypesetter — Custom Line Breaking

For control over where lines break:

```swift
let typesetter = CTTypesetterCreateWithAttributedString(attributedString)

var start: CFIndex = 0
let stringLength = CFAttributedStringGetLength(attributedString)

while start < stringLength {
    // Suggest line break for a given width
    let count = CTTypesetterSuggestLineBreak(typesetter, start, 300.0)

    // Or suggest with cluster breaking (for CJK)
    // let count = CTTypesetterSuggestClusterBreak(typesetter, start, 300.0)

    let line = CTTypesetterCreateLine(typesetter, CFRange(location: start, length: count))
    // Position and draw the line
    start += count
}
```

## CTFont — Font Metrics and Features

```swift
// Create from UIFont
let uiFont = UIFont.systemFont(ofSize: 16)
let ctFont = CTFontCreateWithName(uiFont.fontName as CFString, uiFont.pointSize, nil)

// Metrics
let ascent = CTFontGetAscent(ctFont)
let descent = CTFontGetDescent(ctFont)
let leading = CTFontGetLeading(ctFont)
let unitsPerEm = CTFontGetUnitsPerEm(ctFont)

// Get glyphs for characters
var characters: [UniChar] = Array("A".utf16)
var glyphs = [CGGlyph](repeating: 0, count: characters.count)
CTFontGetGlyphsForCharacters(ctFont, &characters, &glyphs, characters.count)

// Glyph bounding boxes
var boundingRects = [CGRect](repeating: .zero, count: glyphs.count)
CTFontGetBoundingRectsForGlyphs(ctFont, .default, glyphs, &boundingRects, glyphs.count)

// Glyph path (for custom rendering)
if let path = CTFontCreatePathForGlyph(ctFont, glyphs[0], nil) {
    // Draw the glyph outline
    context.addPath(path)
    context.fillPath()
}

// OpenType features
let features = CTFontCopyFeatures(ctFont) as? [[String: Any]] ?? []
```

## CTRunDelegate — Inline Custom Elements

Reserve space in a line for non-text content (images, custom views):

```swift
var callbacks = CTRunDelegateCallbacks(version: kCTRunDelegateCurrentVersion,
    dealloc: { _ in },
    getAscent: { _ in 20 },   // Height above baseline
    getDescent: { _ in 5 },    // Depth below baseline
    getWidth: { _ in 30 }      // Width of the space
)

let delegate = CTRunDelegateCreate(&callbacks, nil)!

let attrs: [NSAttributedString.Key: Any] = [
    kCTRunDelegateAttributeName as NSAttributedString.Key: delegate
]
let placeholder = NSAttributedString(string: "\u{FFFC}", attributes: attrs)

// Insert into your attributed string
// Then draw your custom content at the run's position after layout
```

## Critical: Coordinate System

**Core Text uses bottom-left origin (Core Graphics). UIKit uses top-left origin.**

### Drawing Core Text in UIKit

```swift
override func draw(_ rect: CGRect) {
    guard let context = UIGraphicsGetCurrentContext() else { return }

    // REQUIRED: Flip coordinate system for Core Text
    context.textMatrix = .identity
    context.translateBy(x: 0, y: bounds.height)
    context.scaleBy(x: 1, y: -1)

    // Now draw
    CTLineDraw(line, context)
    // or CTFrameDraw(frame, context)
}
```

**Forgetting the flip is the #1 Core Text mistake.** Text renders upside-down or at the wrong position.

### Converting Line Origins from CTFrame

`CTFrameGetLineOrigins` returns origins in Core Text coordinates (bottom-left). To use in UIKit:

```swift
let lines = CTFrameGetLines(frame) as! [CTLine]
var origins = [CGPoint](repeating: .zero, count: lines.count)
CTFrameGetLineOrigins(frame, CFRange(location: 0, length: lines.count), &origins)

for (i, line) in lines.enumerated() {
    // Flip y: UIKit y = frameHeight - CoreText y
    let uikitY = frameRect.height - origins[i].y
    // uikitY is now the BASELINE position in UIKit coordinates
}
```

## Bridging TextKit ↔ Core Text

### TextKit 2: Getting Glyph Info from a Layout Fragment

```swift
// In a custom NSTextLayoutFragment or delegate callback:
let attributedString = textElement.attributedString
let line = CTLineCreateWithAttributedString(attributedString as CFAttributedString)
let runs = CTLineGetGlyphRuns(line) as! [CTRun]

for run in runs {
    let glyphCount = CTRunGetGlyphCount(run)
    var positions = [CGPoint](repeating: .zero, count: glyphCount)
    CTRunGetPositions(run, CFRange(location: 0, length: glyphCount), &positions)

    // positions are relative to the line origin
    // Add layoutFragmentFrame.origin to get document coordinates
    // Remember to handle the coordinate flip if drawing in UIKit
}
```

### Font Bridging

```swift
// macOS: NSFont ↔ CTFont is toll-free bridged
let ctFont = nsFont as CTFont
let nsFont = ctFont as NSFont

// iOS: UIFont ↔ CTFont is NOT toll-free bridged
// UIFont → CTFont
let ctFont = CTFontCreateWithName(uiFont.fontName as CFString, uiFont.pointSize, nil)

// CTFont → UIFont
let uiFont = UIFont(name: CTFontCopyPostScriptName(ctFont) as String,
                     size: CTFontGetSize(ctFont))!

// NSAttributedString ↔ CFAttributedString IS toll-free bridged (both platforms)
let cfAttrStr = attributedString as CFAttributedString
```

### Attribute Key Differences

Core Text uses its own attribute keys that differ from UIKit/AppKit:

| Purpose | Core Text Key | UIKit/AppKit Key |
|---------|--------------|-----------------|
| Font | `kCTFontAttributeName` (CTFont) | `.font` (UIFont/NSFont) |
| Foreground color | `kCTForegroundColorAttributeName` (CGColor) | `.foregroundColor` (UIColor/NSColor) |
| Paragraph style | `kCTParagraphStyleAttributeName` (CTParagraphStyle) | `.paragraphStyle` (NSParagraphStyle) |
| Kern | `kCTKernAttributeName` | `.kern` |

**When creating attributed strings for Core Text directly, use the `kCT*` keys.** Mixing Core Text keys and UIKit keys in the same attributed string can cause subtle rendering differences.

In practice, UIKit's `.font` attribute (UIFont) works with Core Text because UIFont wraps a CTFont internally. But `.foregroundColor` (UIColor) does NOT — Core Text needs CGColor.

## Common Pitfalls

1. **Forgetting to flip coordinates** — Core Text is bottom-left origin. UIKit is top-left. Text appears upside-down or at wrong position. Always set `context.textMatrix = .identity` and flip.
2. **Not resetting text matrix** — `CGContext.textMatrix` persists between drawing calls. If a previous operation set a non-identity matrix, your Core Text drawing will be transformed unexpectedly.
3. **String indices are UTF-16** — `CTRunGetStringIndices` returns UTF-16 code unit indices (matching NSString), not Swift Character indices. A single emoji can span 2-4 UTF-16 units.
4. **CTFont ≠ UIFont on iOS** — They are NOT toll-free bridged on iOS. Create CTFont explicitly.
5. **CTFrameGetLines returns non-retained array** — In Swift this is usually managed automatically, but be careful with the CFArray if you bridge to C.
6. **Attribute key mismatch** — `kCTForegroundColorAttributeName` expects CGColor, not UIColor. Passing UIColor silently fails (no color rendered).
7. **Character-glyph mapping is not 1:1** — Ligatures produce fewer glyphs than characters. Complex scripts (Arabic, Devanagari) can produce more glyphs than characters. Always use `CTRunGetStringIndices` for the mapping.
8. **CTParagraphStyle is not NSParagraphStyle** — They are related but not interchangeable. CTParagraphStyle uses a C struct API; NSParagraphStyle has Objective-C properties. NSParagraphStyle internally wraps CTParagraphStyle.

## Related Skills

- Use `/skill txt-textkit2` for the TextKit 2 APIs that sit above Core Text.
- Use `/skill txt-textkit1` when NSLayoutManager's glyph APIs are sufficient (no need to drop lower).
- Use `/skill txt-viewport-rendering` for how Core Text fits into the rendering pipeline.
- Use `/skill txt-attachments` when CTRunDelegate is used for inline non-text content.
