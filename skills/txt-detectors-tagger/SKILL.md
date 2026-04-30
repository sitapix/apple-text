---
name: txt-detectors-tagger
description: Configure NSDataDetector, NLTagger, NLTokenizer, NLLanguageRecognizer, and NSString-bridging utilities for Apple text. Use when extracting links/phones/dates/addresses from prose, tagging part of speech or named entities, segmenting tokens or sentences, identifying language, or computing word and sentence embeddings — and whenever a String/NSRange/NSString boundary needs careful conversion. Trigger on 'detect URLs', 'find phone numbers', 'language detection', 'tokenize sentences', 'part of speech', 'sentiment analysis' even without naming any of the actual APIs. Do NOT use for choosing between Swift Regex and NSRegularExpression — that decision lives in txt-regex.
license: MIT
---

# Foundation and NaturalLanguage Text Utilities

Authored against iOS 26.x / Swift 6.x / Xcode 26.x.

This skill covers the Foundation and NaturalLanguage utilities for analyzing already-typed text: NSDataDetector for semantic data extraction, NLTagger and NLTokenizer for linguistic analysis, NLLanguageRecognizer for language ID, NLEmbedding for semantic similarity, and the `String`/`NSString`/`NSRange` bridging required to feed any of these from a Swift codebase. Before quoting any specific API signature, fetch the current Apple docs via Sosumi (`sosumi.ai/documentation/<framework>/<api>`) — the Foundation and NaturalLanguage surfaces gain new methods at almost every Xcode release, and a stale signature will land in caller code unchanged.

This is a utility reference, not a parser-choice document. The Swift Regex vs NSRegularExpression decision belongs in `txt-regex`. AttributedString lifecycle lives in `txt-attributed-string`. Apply this skill once the parser/model choice is settled and you need the exact NaturalLanguage call.

## Contents

- [NSDataDetector for semantic data](#nsdatadetector-for-semantic-data)
- [NLTagger for linguistic tagging](#nltagger-for-linguistic-tagging)
- [NLTokenizer for segmentation](#nltokenizer-for-segmentation)
- [NLLanguageRecognizer for language ID](#nllanguagerecognizer-for-language-id)
- [NLEmbedding for semantic similarity](#nlembedding-for-semantic-similarity)
- [Custom NLModel](#custom-nlmodel)
- [String / NSString / NSRange bridging](#string--nsstring--nsrange-bridging)
- [Common Mistakes](#common-mistakes)
- [References](#references)

## NSDataDetector for semantic data

`NSDataDetector` is a subclass of `NSRegularExpression` that recognizes URLs, phone numbers, addresses, dates, and transit information in natural-language text. It uses a built-in model rather than a regex pattern — the only configuration is which result types you want.

```swift
let types: NSTextCheckingResult.CheckingType = [.link, .phoneNumber, .address, .date]
let detector = try NSDataDetector(types: types.rawValue)

let text = "Call 555-1234 on March 15 or visit https://apple.com"
let matches = detector.matches(in: text, range: NSRange(text.startIndex..., in: text))

for match in matches {
    switch match.resultType {
    case .link:        print("URL:", match.url ?? "")
    case .phoneNumber: print("Phone:", match.phoneNumber ?? "")
    case .address:     print("Address:", match.addressComponents ?? [:])
    case .date:        print("Date:", match.date ?? .now)
    case .transitInformation: print("Flight:", match.components ?? [:])
    default: break
    }
}
```

The result-type accessors (`url`, `phoneNumber`, `addressComponents`, `date`, `components`) are only populated when the result type matches — always switch on `resultType` and unwrap the matching property. Date results carry `duration` and `timeZone` when the model can infer them; addresses surface `addressComponents` as a `[NSTextCheckingKey: String]` dictionary keyed by `.city`, `.street`, etc.

`UITextView` exposes built-in detection via `dataDetectorTypes`, but the property is silently ignored when `isEditable == true`. For editable views or non-text-view callers, run `NSDataDetector` over the content yourself and apply attributes or actions to the matched ranges.

## NLTagger for linguistic tagging

`NLTagger` annotates text with part-of-speech, named-entity, lemma, language, and script information. Configure it with the schemes you need, set the string, then enumerate tags.

```swift
import NaturalLanguage

let tagger = NLTagger(tagSchemes: [.lexicalClass, .nameType, .lemma])
tagger.string = "Apple released new iPhones in Cupertino"

tagger.enumerateTags(
    in: tagger.string!.startIndex..<tagger.string!.endIndex,
    unit: .word,
    scheme: .lexicalClass,
    options: [.omitWhitespace, .omitPunctuation]
) { tag, range in
    if let tag {
        print("\(tagger.string![range]): \(tag.rawValue)")
    }
    return true
}
```

The schemes available include `.tokenType` (word/punctuation/whitespace), `.lexicalClass` (noun/verb/adjective/etc.), `.nameType` (`.personalName`, `.placeName`, `.organizationName`), `.lemma` (base form of the word), `.language` (per-segment BCP 47 code), and `.script` (ISO 15924 code). Set only the schemes you'll actually query; each one costs work in `enumerateTags`.

Linguistic analysis needs context. A two-word string produces unreliable tags — short fragments confuse the model, and named-entity recognition in particular requires enough surrounding text to anchor names against the rest of the sentence. If your input is very short, treat low-confidence tags as missing rather than authoritative.

The unit determines the granularity of the enumeration: `.word`, `.sentence`, `.paragraph`, or `.document`. The scheme determines what the callback receives. Word-unit lexical-class tagging is the standard "POS tagging" workflow; document-unit `.language` tagging is the right way to ask "what language is this whole text" without instantiating an `NLLanguageRecognizer`.

## NLTokenizer for segmentation

`NLTokenizer` splits text into language-aware tokens. It honors language-specific word boundaries (handling CJK without spaces, Thai without punctuation cues, etc.) which a naive whitespace split cannot.

```swift
let tokenizer = NLTokenizer(unit: .word)
tokenizer.string = "Hello, world! 你好世界。"

tokenizer.enumerateTokens(in: tokenizer.string!.startIndex..<tokenizer.string!.endIndex) { range, attrs in
    print(tokenizer.string![range])
    return true
}
```

Units are `.word`, `.sentence`, `.paragraph`, `.document`. The tokenizer detects the language automatically from the input; for mixed-script content where the auto-detection is unreliable, set `tokenizer.setLanguage(_:)` explicitly. The `attrs` argument carries flags like `.numeric`, `.symbolic`, `.emoji` — useful when you want to drop pure-symbol tokens before downstream processing.

Tokenizer ranges come back as Swift `Range<String.Index>` against the assigned string. To bridge to NSRange for an attribute application or NSRegularExpression call, use `NSRange(range, in: tokenizer.string!)`.

## NLLanguageRecognizer for language ID

`NLLanguageRecognizer` identifies the dominant language of a text and returns a probability distribution across candidate languages. It's the right tool for routing text to language-specific spell checkers, tokenizers, or translation pipelines.

```swift
let recognizer = NLLanguageRecognizer()
recognizer.processString("Bonjour le monde")
let dominant = recognizer.dominantLanguage  // .french

let hypotheses = recognizer.languageHypotheses(withMaximum: 3)
// [.french: 0.95, .italian: 0.03, .spanish: 0.02]
```

Two configuration knobs matter: `languageConstraints` restricts the recognizer to a fixed set of languages (improves accuracy when you know your app only supports a handful), and `languageHints` supplies prior probabilities (useful when the user has already declared a preferred language). For very short strings — single words, hashtags, brand names — language ID is unreliable. Treat it as a hint, not a fact, until you have at least a sentence.

## NLEmbedding for semantic similarity

`NLEmbedding` provides word and sentence vectors for similarity and nearest-neighbor work. The built-in word embeddings cover the languages Apple ships models for; sentence embeddings are available for a smaller subset.

```swift
if let embedding = NLEmbedding.wordEmbedding(for: .english) {
    let distance = embedding.distance(between: "king", and: "queen")
    embedding.enumerateNeighbors(for: "swift", maximumCount: 5) { neighbor, distance in
        print("\(neighbor): \(distance)")
        return true
    }
}

if let sentenceEmbedding = NLEmbedding.sentenceEmbedding(for: .english) {
    let distance = sentenceEmbedding.distance(
        between: "The cat sat on the mat",
        and: "A feline rested on the rug"
    )
}
```

`distance(between:and:)` returns a non-negative distance — smaller is more similar. The default metric is cosine; configure `distanceType` for alternatives. Both word and sentence embeddings are local, fast, and synchronous — they don't talk to a server and don't need a network entitlement.

For tasks that need richer semantics than Apple's stock embeddings provide (domain-specific classifiers, sentiment, custom topic tagging), the path is `NLModel` loaded from a Create ML training run — see below.

## Custom NLModel

For classification beyond the built-in schemes, train a model in Create ML and load it via `NLModel`. The model's `predictedLabel(for:)` returns a single label; `predictedLabelHypotheses(for:maximumCount:)` returns a probability distribution.

```swift
let model = try NLModel(mlModel: MyTextClassifier().model)
let label = model.predictedLabel(for: "This is great!")
let top3 = model.predictedLabelHypotheses(for: "This is great!", maximumCount: 3)
```

The `mlModel` parameter is a Core ML `MLModel` — Create ML's text classifier templates produce one directly. The first call is the slow one; loading the model file and JIT-compiling the Core ML graph happens lazily, so eager-load the `NLModel` off the main thread before the user-facing call.

## String / NSString / NSRange bridging

Swift `String` indexes graphemes; `NSString` indexes UTF-16 code units; `NSRange` is a UTF-16 range. They diverge dramatically on emoji, ZWJ sequences, combining marks, and most non-Latin scripts. Mixing the two count systems is the most common source of "wrong range" bugs in Foundation-text code.

```swift
let text = "Hello 👋🏽 World"
text.count                   // 7  (Characters)
(text as NSString).length    // 11 (UTF-16 code units — 👋🏽 is 4 units)
```

Always convert ranges via the `NSRange(_:in:)` initializer:

```swift
// Range<String.Index> -> NSRange
let nsRange = NSRange(swiftRange, in: text)

// NSRange -> Range<String.Index>
if let swiftRange = Range(nsRange, in: text) {
    let substring = text[swiftRange]
}

// Full-text NSRange
let fullRange = NSRange(text.startIndex..., in: text)
// Equivalent to NSRange(location: 0, length: (text as NSString).length)
```

Bridging is not zero-cost. `String` is UTF-8 internal; `NSString` is UTF-16 internal. The bridge defers copying when it can, but UTF-8↔UTF-16 conversion happens on first index, on `NSString.length` evaluation, and on `NSRange` extraction. In a hot loop, choose one form and stay there — pre-convert to `NSString` once and operate on UTF-16 indices, or stay in `String` and convert ranges only at the API boundary.

`NSAttributedString` ranges are NSRange against the string's UTF-16 view. `AttributedString` indices are typed (`AttributedString.Index`), and converting back to NSRange requires the round-trip through `NSAttributedString` or manual UTF-16-offset bookkeeping. See `txt-attributed-string` for the conversion pattern when both representations are in play.

For text-drawing measurement (`boundingRect(with:options:context:)`, `drawString(...)`), pass `.usesLineFragmentOrigin` for any multi-line text — without it the bounding rect is computed for a single-line baseline-anchored draw, and multi-line widths come back wildly wrong. `NSStringDrawingContext` controls scaling: setting `minimumScaleFactor` allows shrink-to-fit, and after the draw `actualScaleFactor` reports what the system actually used.

## Common Mistakes

1. **Mixing `String.count` and `NSString.length`.** They count different things. Computing an `NSRange` from `String.count` corrupts on emoji and combining marks. Always normalize via `(text as NSString).length` for explicit length, or `NSRange(swiftRange, in: text)` to convert a Swift range.

   ```swift
   // WRONG — will corrupt on emoji
   let bad = NSRange(location: 0, length: text.count)

   // CORRECT
   let good = NSRange(text.startIndex..., in: text)
   ```

2. **Setting `dataDetectorTypes` on an editable text view.** `UITextView.dataDetectorTypes` is silently ignored when `isEditable = true`. For editable views, run `NSDataDetector` over the text and apply `.link` attributes (or your own UI) to the matched ranges yourself.

3. **Trusting NLTagger or NLLanguageRecognizer on tiny inputs.** Linguistic models need context. Two-word queries produce unreliable tags; single-word language ID is essentially a coin flip on common short cognates. Treat low-confidence tags as missing rather than authoritative.

4. **Forgetting `.usesLineFragmentOrigin` on multi-line measurement.** `NSAttributedString.boundingRect(with:options:context:)` computes a single-line baseline-anchored box without it. Multi-line measurement is silently wrong until the option is set.

5. **Setting too many tag schemes on `NLTagger`.** Each scheme costs work in `setString` and `enumerateTags`. Set only the schemes you'll actually query.

6. **Loading `NLModel` on the main thread inside a tap handler.** First-load JIT-compiles the Core ML graph and can take hundreds of milliseconds. Load eagerly off-thread before the model is needed.

7. **Bridging `String`↔`NSString` inside a hot loop.** Each direction can trigger encoding conversion. Pre-bridge once outside the loop and operate on NSString or NSRange consistently within it.

## References

- `/skill txt-regex` — Swift Regex vs NSRegularExpression decision and bridging matches to NSRange
- `/skill txt-attributed-string` — converting `AttributedString` and `NSAttributedString` ranges
- `/skill txt-markdown` — when detector or tagger output feeds Markdown rendering
- `/skill txt-measurement` — full text-measurement reference beyond `boundingRect`
- [NSDataDetector](https://sosumi.ai/documentation/foundation/nsdatadetector)
- [NSRegularExpression](https://sosumi.ai/documentation/foundation/nsregularexpression)
- [NLTagger](https://sosumi.ai/documentation/naturallanguage/nltagger)
- [NLTokenizer](https://sosumi.ai/documentation/naturallanguage/nltokenizer)
- [NLLanguageRecognizer](https://sosumi.ai/documentation/naturallanguage/nllanguagerecognizer)
- [NLEmbedding](https://sosumi.ai/documentation/naturallanguage/nlembedding)
