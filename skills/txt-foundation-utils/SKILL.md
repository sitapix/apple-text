---
name: txt-foundation-utils
description: Use when using Foundation or NaturalLanguage text utilities — NSRegularExpression, NSDataDetector, NLTagger, NLTokenizer, or NSString bridging
license: MIT
---

# Foundation Text Utilities Reference

Use this skill when you need the exact Foundation or NaturalLanguage tool for a text-processing problem.

## When to Use

- You need `NSRegularExpression`, `NSDataDetector`, or NaturalLanguage APIs.
- You are measuring text or bridging `String` and `NSString`.
- The question is about utility APIs, not parser choice alone.

## Quick Decision

- Need parser choice guidance -> `/skill txt-parsing`
- Need the exact utility API or compatibility details -> stay here
- Need attributed-text model guidance instead of utilities -> `/skill txt-attributed-string`

## Core Guidance

## NSRegularExpression

ICU-compatible regex engine. Reference type.

```swift
let pattern = "\\b[A-Z][a-z]+\\b"
let regex = try NSRegularExpression(pattern: pattern, options: [.caseInsensitive])

// Find all matches
let text = "Hello World from Swift"
let fullRange = NSRange(text.startIndex..., in: text)
let matches = regex.matches(in: text, range: fullRange)

for match in matches {
    if let range = Range(match.range, in: text) {
        print(text[range])
    }
}

// First match only
let firstMatch = regex.firstMatch(in: text, range: fullRange)

// Number of matches
let count = regex.numberOfMatches(in: text, range: fullRange)

// Replace
let replaced = regex.stringByReplacingMatches(
    in: text, range: fullRange,
    withTemplate: "[$0]"
)

// Enumerate matches
regex.enumerateMatches(in: text, range: fullRange) { result, flags, stop in
    guard let result else { return }
    // Process match
}
```

### Options

```swift
NSRegularExpression.Options:
    .caseInsensitive      // i
    .allowCommentsAndWhitespace  // x
    .ignoreMetacharacters  // literal match
    .dotMatchesLineSeparators    // s
    .anchorsMatchLines     // m
    .useUnixLineSeparators
    .useUnicodeWordBoundaries
```

### Capture Groups

```swift
let regex = try NSRegularExpression(pattern: "(\\w+)@(\\w+\\.\\w+)")
let text = "user@example.com"
if let match = regex.firstMatch(in: text, range: NSRange(text.startIndex..., in: text)) {
    // match.range(at: 0) — full match
    // match.range(at: 1) — first group ("user")
    // match.range(at: 2) — second group ("example.com")
    let user = String(text[Range(match.range(at: 1), in: text)!])
    let domain = String(text[Range(match.range(at: 2), in: text)!])
}
```

### Modern Alternative: Swift Regex (iOS 16+)

```swift
let regex = /(?<user>\w+)@(?<domain>\w+\.\w+)/
if let match = text.firstMatch(of: regex) {
    let user = match.user
    let domain = match.domain
}

// With RegexBuilder
import RegexBuilder
let pattern = Regex {
    Capture { OneOrMore(.word) }
    "@"
    Capture { OneOrMore(.word); "."; OneOrMore(.word) }
}
```

**When to use NSRegularExpression vs Swift Regex:**
- NSRegularExpression: Dynamic patterns (user input), pre-iOS 16, NSRange-based APIs
- Swift Regex: Static patterns, type-safe captures, iOS 16+

## NSDataDetector

Detects semantic data in natural language text. Subclass of NSRegularExpression.

```swift
let types: NSTextCheckingResult.CheckingType = [.link, .phoneNumber, .address, .date]
let detector = try NSDataDetector(types: types.rawValue)

let text = "Call 555-1234 on March 15, 2025 or visit https://apple.com"
let matches = detector.matches(in: text, range: NSRange(text.startIndex..., in: text))

for match in matches {
    switch match.resultType {
    case .link:
        print("URL: \(match.url!)")
    case .phoneNumber:
        print("Phone: \(match.phoneNumber!)")
    case .address:
        print("Address: \(match.addressComponents!)")
    case .date:
        print("Date: \(match.date!)")
    case .transitInformation:
        print("Flight: \(match.components!)")
    default: break
    }
}
```

### Supported Types

| Type | Properties | Example |
|------|-----------|---------|
| `.link` | `url` | "https://apple.com" |
| `.phoneNumber` | `phoneNumber` | "555-1234" |
| `.address` | `addressComponents` | "1 Apple Park Way, Cupertino" |
| `.date` | `date`, `duration`, `timeZone` | "March 15, 2025" |
| `.transitInformation` | `components` (airline, flight) | "UA 123" |

### Modern Alternative: DataDetection (iOS 18+)

```swift
import DataDetection
// New API with structured results and better accuracy
```

## NaturalLanguage Framework (iOS 12+)

Replaces deprecated `NSLinguisticTagger`.

### NLTagger

Tag text with linguistic information:

```swift
import NaturalLanguage

let tagger = NLTagger(tagSchemes: [.lexicalClass, .nameType, .lemma])
tagger.string = "Apple released new iPhones in Cupertino"

// Enumerate tags
tagger.enumerateTags(
    in: tagger.string!.startIndex..<tagger.string!.endIndex,
    unit: .word,
    scheme: .lexicalClass
) { tag, range in
    if let tag {
        print("\(tagger.string![range]): \(tag.rawValue)")
        // "Apple": Noun, "released": Verb, etc.
    }
    return true
}
```

### Tag Schemes

| Scheme | Tags | Purpose |
|--------|------|---------|
| `.tokenType` | `.word`, `.punctuation`, `.whitespace` | Token classification |
| `.lexicalClass` | `.noun`, `.verb`, `.adjective`, `.adverb`, etc. | Part of speech |
| `.nameType` | `.personalName`, `.placeName`, `.organizationName` | Named entity recognition |
| `.lemma` | (base form string) | Word lemmatization |
| `.language` | (BCP 47 code) | Per-word language |
| `.script` | (ISO 15924 code) | Writing script |

### NLTokenizer

Segment text into tokens:

```swift
let tokenizer = NLTokenizer(unit: .word)  // .word, .sentence, .paragraph, .document
tokenizer.string = "Hello, world! How are you?"

tokenizer.enumerateTokens(in: tokenizer.string!.startIndex..<tokenizer.string!.endIndex) { range, attrs in
    print(tokenizer.string![range])
    return true
}
// Output: "Hello", "world", "How", "are", "you"
```

### NLLanguageRecognizer

Identify language of text:

```swift
let recognizer = NLLanguageRecognizer()
recognizer.processString("Bonjour le monde")
let language = recognizer.dominantLanguage  // .french

// With probabilities
let hypotheses = recognizer.languageHypotheses(withMaximum: 3)
// [.french: 0.95, .italian: 0.03, .spanish: 0.02]

// Constrain to specific languages
recognizer.languageConstraints = [.english, .french, .german]

// Language hints (prior probabilities)
recognizer.languageHints = [.french: 0.8, .english: 0.2]
```

### NLEmbedding

Word and sentence embeddings for semantic similarity:

```swift
// Built-in word embeddings
if let embedding = NLEmbedding.wordEmbedding(for: .english) {
    let distance = embedding.distance(between: "king", and: "queen")

    // Find nearest neighbors
    embedding.enumerateNeighbors(for: "swift", maximumCount: 5) { neighbor, distance in
        print("\(neighbor): \(distance)")
        return true
    }
}

// Sentence embedding (iOS 14+)
if let sentenceEmbedding = NLEmbedding.sentenceEmbedding(for: .english) {
    let distance = sentenceEmbedding.distance(
        between: "The cat sat on the mat",
        and: "A feline rested on the rug"
    )
}
```

### Custom NLModel (via Create ML)

```swift
// Load trained model
let model = try NLModel(mlModel: MyTextClassifier().model)

// Classify text
let label = model.predictedLabel(for: "This is great!")
// e.g., "positive"

// With confidence
let hypotheses = model.predictedLabelHypotheses(for: "This is great!", maximumCount: 3)
```

## NSStringDrawingContext

Controls text drawing behavior, especially scaling:

```swift
let context = NSStringDrawingContext()
context.minimumScaleFactor = 0.5  // Allow shrinking to 50%

let boundingRect = CGRect(x: 0, y: 0, width: 200, height: 50)
attributedString.draw(with: boundingRect,
                      options: [.usesLineFragmentOrigin],
                      context: context)

// Check what scale was actually used
print("Scale used: \(context.actualScaleFactor)")
// 1.0 = no shrinking needed, < 1.0 = text was shrunk
```

### Bounding Rect Calculation

```swift
// Calculate size needed for attributed string
let size = attributedString.boundingRect(
    with: CGSize(width: maxWidth, height: .greatestFiniteMagnitude),
    options: [.usesLineFragmentOrigin, .usesFontLeading],
    context: nil
).size

// Round up for pixel alignment
let ceilSize = CGSize(width: ceil(size.width), height: ceil(size.height))
```

**Options:**
- `.usesLineFragmentOrigin` — Multi-line text (ALWAYS include for multi-line)
- `.usesFontLeading` — Include font leading in height
- `.truncatesLastVisibleLine` — Truncate if exceeds bounds

## String / NSString Bridging

### Key Differences

| Aspect | String (Swift) | NSString (ObjC) |
|--------|---------------|-----------------|
| **Encoding** | UTF-8 internal | UTF-16 internal |
| **Indexing** | `String.Index` (Character) | `Int` (UTF-16 code unit) |
| **Count** | `.count` (Characters) | `.length` (UTF-16 units) |
| **Empty check** | `.isEmpty` | `.length == 0` |
| **Type** | Value type | Reference type |

### Bridging Cost

```swift
let swiftStr: String = "Hello"
let nsStr = swiftStr as NSString     // Bridge (may defer copy)
let backStr = nsStr as String         // Bridge back

// NSRange ↔ Range conversion
let nsRange = NSRange(swiftStr.startIndex..., in: swiftStr)
let swiftRange = Range(nsRange, in: swiftStr)
```

**Performance note:** Bridging is NOT zero-cost. UTF-8 ↔ UTF-16 conversion may occur. For tight loops with Foundation APIs, consider working with NSString directly.

### Common Pattern: NSRange from String

```swift
let text = "Hello 👋🏽 World"

// ✅ CORRECT: Using String for conversion
let nsRange = NSRange(text.range(of: "World")!, in: text)

// ✅ CORRECT: Full range
let fullRange = NSRange(text.startIndex..., in: text)

// ❌ WRONG: Assuming character count = NSString length
let badRange = NSRange(location: 0, length: text.count)  // WRONG for emoji/CJK
```

**Why counts differ:** `"👋🏽".count` = 1 (one Character), `("👋🏽" as NSString).length` = 4 (four UTF-16 code units).

## Quick Reference

| Need | API | Min OS |
|------|-----|--------|
| Pattern matching (dynamic) | NSRegularExpression | All |
| Pattern matching (static) | Swift Regex | iOS 16 |
| Detect links/phones/dates | NSDataDetector | All |
| Detect data (modern) | DataDetection | iOS 18 |
| Part of speech tagging | NLTagger (.lexicalClass) | iOS 12 |
| Named entity recognition | NLTagger (.nameType) | iOS 12 |
| Language detection | NLLanguageRecognizer | iOS 12 |
| Text segmentation | NLTokenizer | iOS 12 |
| Word similarity | NLEmbedding.wordEmbedding | iOS 13 |
| Sentence similarity | NLEmbedding.sentenceEmbedding | iOS 14 |
| Custom classifier | NLModel + Create ML | iOS 12 |
| Text measurement | NSAttributedString.boundingRect | All |
| Draw text with scaling | NSStringDrawingContext | All |

## Common Pitfalls

1. **Assuming String.count == NSString.length** — They use different counting units (Characters vs UTF-16). Always convert ranges explicitly.
2. **Missing `.usesLineFragmentOrigin`** — Without this option, `boundingRect` calculates for single-line text.
3. **NSRegularExpression with user input** — Always `try` the constructor — invalid patterns throw.
4. **NLTagger requires enough text** — Very short strings produce unreliable linguistic analysis.
5. **Bridging in hot loops** — String ↔ NSString conversion has overhead. Keep one type in tight loops.

## Related Skills

- Use `/skill txt-parsing` for Swift Regex vs `NSRegularExpression` choice.
- Use `/skill txt-markdown` when parsing feeds Markdown-rendering workflows.
- Use `/skill txt-attributed-string` when utility output becomes attributed content.
