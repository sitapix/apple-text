# Multi-Container Layout & NSTextTable

Deep reference for linked text containers (multi-column, multi-page) and AppKit's `NSTextTable`/`NSTextTableBlock`. Loaded by `txt-exclusion-paths` when the task moves past simple text wrapping into multi-region or table layout.

## Multi-Container (Linked) Layout

A single `NSLayoutManager` (TK1) or `NSTextLayoutManager` (TK2) can manage text across **multiple** `NSTextContainer` instances. When text overflows the first container, it flows into the second, and so on. This is how you build multi-column, multi-page, or magazine-style layouts.

### TextKit 1 — Multiple Containers

```swift
let textStorage = NSTextStorage(attributedString: content)
let layoutManager = NSLayoutManager()
textStorage.addLayoutManager(layoutManager)

// Column 1
let container1 = NSTextContainer(size: CGSize(width: 300, height: 500))
layoutManager.addTextContainer(container1)
let textView1 = UITextView(frame: .zero, textContainer: container1)

// Column 2
let container2 = NSTextContainer(size: CGSize(width: 300, height: 500))
layoutManager.addTextContainer(container2)
let textView2 = UITextView(frame: .zero, textContainer: container2)

// Text automatically flows from container1 -> container2
```

**Key rules:**
- Container order matters — `layoutManager.textContainers` is an ordered array
- Text fills containers in order; overflow goes to the next
- Each container can have its own `exclusionPaths`
- Each container gets its own `UITextView`/`NSTextView`
- You manage the views' frames yourself (the text system only handles text flow)

### TextKit 2 — Multiple Containers

TextKit 2 uses a slightly different model. `NSTextLayoutManager` manages a single `NSTextContainer` by default, but `NSTextContentManager` can drive multiple layout managers:

```swift
let contentManager = NSTextContentStorage()
contentManager.attributedString = content

// Layout manager per column
let layoutManager1 = NSTextLayoutManager()
let container1 = NSTextContainer(size: CGSize(width: 300, height: 500))
layoutManager1.textContainer = container1
contentManager.addTextLayoutManager(layoutManager1)

let layoutManager2 = NSTextLayoutManager()
let container2 = NSTextContainer(size: CGSize(width: 300, height: 500))
layoutManager2.textContainer = container2
contentManager.addTextLayoutManager(layoutManager2)
```

### Detecting Overflow

```swift
// TextKit 1: Check if text overflows a container
let glyphRange = layoutManager.glyphRange(for: container1)
let charRange = layoutManager.characterRange(forGlyphRange: glyphRange,
                                              actualGlyphRange: nil)
let hasOverflow = charRange.upperBound < textStorage.length
```

### Practical: Two-Column Layout

```swift
class TwoColumnView: UIView {
    let textStorage = NSTextStorage()
    let layoutManager = NSLayoutManager()
    var leftTextView: UITextView!
    var rightTextView: UITextView!

    func setup() {
        textStorage.addLayoutManager(layoutManager)

        let leftContainer = NSTextContainer(size: .zero)
        leftContainer.widthTracksTextView = true
        leftContainer.heightTracksTextView = true
        layoutManager.addTextContainer(leftContainer)
        leftTextView = UITextView(frame: .zero, textContainer: leftContainer)
        leftTextView.isEditable = false
        addSubview(leftTextView)

        let rightContainer = NSTextContainer(size: .zero)
        rightContainer.widthTracksTextView = true
        rightContainer.heightTracksTextView = true
        layoutManager.addTextContainer(rightContainer)
        rightTextView = UITextView(frame: .zero, textContainer: rightContainer)
        rightTextView.isEditable = false
        addSubview(rightTextView)
    }

    override func layoutSubviews() {
        super.layoutSubviews()
        let columnWidth = (bounds.width - 16) / 2  // 16pt gap
        leftTextView.frame = CGRect(x: 0, y: 0,
                                     width: columnWidth, height: bounds.height)
        rightTextView.frame = CGRect(x: columnWidth + 16, y: 0,
                                      width: columnWidth, height: bounds.height)
    }
}
```

### Editing Caveat

Editing in linked containers is fragile. Works well for read-only; editing across container boundaries requires careful cursor management — selection, caret, and IME marked text all assume a single container in the common UITextView/NSTextView paths.

## NSTextTable / NSTextBlock (AppKit)

### What They Are

AppKit provides `NSTextTable` and `NSTextTableBlock` for rendering tables directly inside attributed strings. These are **paragraph-level attributes** — each table cell is a paragraph whose `NSParagraphStyle.textBlocks` includes an `NSTextTableBlock`.

**Platform availability:** Primarily AppKit (NSTextView). UIKit has the classes but rendering support is limited.

### Creating a Table

```swift
// Create a 3-column table
let table = NSTextTable()
table.numberOfColumns = 3
table.collapsesBorders = true

// Create a cell: row 0, column 0
let cell = NSTextTableBlock(table: table,
                             startingRow: 0, rowSpan: 1,
                             startingColumn: 0, columnSpan: 1)
cell.setContentWidth(33.33, type: .percentageValueType)
cell.backgroundColor = .controlBackgroundColor
cell.setWidth(0.5, type: .absoluteValueType, for: .border)
cell.setBorderColor(.separatorColor)
cell.setValue(4, type: .absoluteValueType, for: .padding)

// Attach to paragraph style
let style = NSMutableParagraphStyle()
style.textBlocks = [cell]

// Create the cell content
let cellText = NSAttributedString(
    string: "Cell content\n",  // Note: must end with newline
    attributes: [
        .paragraphStyle: style,
        .font: NSFont.systemFont(ofSize: 13)
    ]
)
```

### Building a Full Table

```swift
func makeTable(rows: Int, columns: Int, data: [[String]]) -> NSAttributedString {
    let table = NSTextTable()
    table.numberOfColumns = columns
    table.collapsesBorders = true

    let result = NSMutableAttributedString()

    for row in 0..<rows {
        for col in 0..<columns {
            let cell = NSTextTableBlock(table: table,
                                         startingRow: row, rowSpan: 1,
                                         startingColumn: col, columnSpan: 1)
            cell.setContentWidth(CGFloat(100 / columns),
                                 type: .percentageValueType)
            cell.setValue(4, type: .absoluteValueType, for: .padding)
            cell.setWidth(0.5, type: .absoluteValueType, for: .border)
            cell.setBorderColor(.separatorColor)

            if row == 0 {
                cell.backgroundColor = .controlAccentColor.withAlphaComponent(0.1)
            }

            let style = NSMutableParagraphStyle()
            style.textBlocks = [cell]

            let text = data[row][col] + "\n"  // Each cell ends with newline
            result.append(NSAttributedString(string: text, attributes: [
                .paragraphStyle: style,
                .font: row == 0 ? NSFont.boldSystemFont(ofSize: 13)
                                : NSFont.systemFont(ofSize: 13)
            ]))
        }
    }

    return result
}
```

### NSTextBlock Properties

| Property | Purpose |
|----------|---------|
| `backgroundColor` | Cell background color |
| `setBorderColor(_:for:)` | Per-edge border color |
| `setWidth(_:type:for:edge:)` | Margin, border, or padding per edge |
| `setWidth(_:type:for:)` | Margin, border, or padding for all edges of a layer |
| `setContentWidth(_:type:)` | Cell content width (absolute or percentage) |
| `verticalAlignment` | `.top`, `.middle`, `.bottom`, `.baseline` |
| `setValue(_:type:for:)` | Set dimension values (minWidth, maxWidth, minHeight, maxHeight) |

### NSTextBlock.Layer

```swift
cell.setWidth(1, type: .absoluteValueType, for: .border)   // Border layer
cell.setValue(8, type: .absoluteValueType, for: .padding)   // Padding layer
cell.setValue(4, type: .absoluteValueType, for: .margin)    // Margin layer
```

### UIKit Alternative: Tables via Attachments

Since UIKit doesn't fully support NSTextTable rendering, use `NSTextAttachmentViewProvider` (TextKit 2) to embed a `UITableView` or custom view:

```swift
// See /skill txt-attachments for full NSTextAttachmentViewProvider pattern
class TableAttachmentViewProvider: NSTextAttachmentViewProvider {
    override func loadView() {
        let tableView = MyCompactTableView(data: extractData(from: textAttachment))
        view = tableView
    }

    override func attachmentBounds(
        for attributes: [NSAttributedString.Key: Any],
        location: NSTextLocation,
        textContainer: NSTextContainer?,
        proposedLineFragment: CGRect,
        position: CGPoint
    ) -> CGRect {
        // Full-width, calculated height
        let width = proposedLineFragment.width
        let height = calculateTableHeight(for: width)
        return CGRect(x: 0, y: 0, width: width, height: height)
    }
}
```

### NSTextTable Pitfalls

- **UIKit rendering is incomplete.** Use attachment view providers on iOS instead.
- **Each cell must end with `\n`.** NSTextTable cells are paragraph-level; missing the trailing newline merges cells.
- **Borders depend on `collapsesBorders`.** With `true`, adjacent cells share a border; with `false`, each cell paints its own.
