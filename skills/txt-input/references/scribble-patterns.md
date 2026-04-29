# Scribble / Apple Pencil Handwriting Patterns

Use this sidecar when `txt-input` needs the full Scribble API surface for custom views.

## UIScribbleInteraction (Customization)

For views that already support text input but need to customize Scribble behavior:

```swift
let scribble = UIScribbleInteraction(delegate: self)
textView.addInteraction(scribble)
```

```swift
extension CustomEditor: UIScribbleInteractionDelegate {
    // Disable Scribble in certain regions (e.g., drawing canvas area)
    func scribbleInteraction(_ interaction: UIScribbleInteraction,
                            shouldBeginAt location: CGPoint) -> Bool {
        return !isDrawingArea(at: location)
    }

    // Suppress autocomplete UI during active handwriting
    func scribbleInteractionDidFinishWriting(_ interaction: UIScribbleInteraction) {
        showAutocompleteSuggestions()
    }
}

// Check if user is actively writing (suppress transient UI)
if scribbleInteraction.isHandlingWriting {
    // Don't show autocomplete popover yet
}

// Check if pencil input is expected (pre-size layout)
if UIScribbleInteraction.isPencilInputExpected {
    // Use larger touch targets
}
```

## UIIndirectScribbleInteraction (Non-Text-Input Views)

For views that are NOT text inputs but should become editable when written on (e.g., a list where writing below creates a new item):

```swift
let indirect = UIIndirectScribbleInteraction(delegate: self)
view.addInteraction(indirect)
```

Four required delegate methods:

```swift
extension ListView: UIIndirectScribbleInteractionDelegate {
    // Report writable regions
    func indirectScribbleInteraction(_ interaction: UIIndirectScribbleInteraction,
                                    requestElementsIn rect: CGRect,
                                    completion: @escaping ([ElementIdentifier]) -> Void) {
        let elements = writableElements(in: rect)
        completion(elements)
    }

    // Return frame for each element
    func indirectScribbleInteraction(_ interaction: UIIndirectScribbleInteraction,
                                    frameForElement elementIdentifier: ElementIdentifier) -> CGRect {
        return frame(for: elementIdentifier)
    }

    // Focus the element (create text input if needed)
    func indirectScribbleInteraction(_ interaction: UIIndirectScribbleInteraction,
                                    focusElementIfNeeded elementIdentifier: ElementIdentifier,
                                    referencePoint point: CGPoint,
                                    completion: @escaping ((UIResponder & UITextInput)?) -> Void) {
        let textField = createOrFocusTextField(for: elementIdentifier)
        completion(textField)
    }

    // Report focus state
    func indirectScribbleInteraction(_ interaction: UIIndirectScribbleInteraction,
                                    isElementFocused elementIdentifier: ElementIdentifier) -> Bool {
        return focusedElement == elementIdentifier
    }
}
```

## Language Support

Scribble supports: English, Simplified Chinese, Traditional Chinese, Cantonese, German, French, Spanish, Italian, Portuguese. All processing is on-device.

## Design Guidelines

From Apple's HIG:
- Keep layouts stable during writing (don't reflow while the pencil is down)
- Provide adequate writing space (don't require tiny precision)
- Don't require a tap before writing — Scribble should work on first contact
- Use pencil-friendly spacing between interactive elements
