# Phase: step18 — Natural copy pass

Version: step18-1. The user says the on-screen text reads as AI-generated, and everything should sound natural while saying the same thing. Text-only: no layout, logic, pricing or flow changes. No tester; quick checks only.

## Voice
Write like a small courier owner explaining the product to another owner over coffee:
- Short, plain sentences. Contractions are fine. Concrete numbers over adjectives.
- Say the thing once. No restating, no "which helps explain", no "seamlessly", "effortlessly", "powerful", "unlock", "leverage", "streamline", "intelligent", "AI-powered", "in seconds", "magic".
- No slogan patterns: no "X, not Y" contrasts, no rule-of-three lists, no colon-led taglines, no rhetorical questions, no exclamation marks, no em dashes as flourish.
- Labels are nouns or verbs people use ("Re-read", "Send quote"), not marketing phrases.
- Error and empty states say what happened and what to do next, in one line.

## Functional requirements
- REQ-1200 [always] The system shall rewrite builder-written user-facing copy in this voice: app labels, helper text, empty and loading states, errors, Morning Brief, presenter notes, /dev, sign-in screen, About, the Our research page prose and "what Drivepast does" lines (keeping every fact, number and source), Settings help text, Activity lines, chat chips, and the booking confirmation message to customers.
- REQ-1201 [always] The system shall keep these exact strings the user wrote: the landing copy in PROMPT.md (headline, body, panel titles, paragraphs and rows, sign text), the customer_line formats from Task 6, the booked event/toast format from Task 3 ("Booked {customer}, ${price} instead of ${usual}, {van} already passes {miles} mi away."), "Auto-sent within your rules", "Our usual price for this run is $55.", "Reading the request", "Pricing against N vans", "Booked automatically" / "Accepted by customer" only if user-specified (they were not; rewrite allowed), the Task 1 suggestion chips and the assistant instruction text from Task 1. (Facts and numbers never change.)
- REQ-1202 [always] The assistant system prompt shall gain one style line: "Talk like a dispatcher to the owner: short plain sentences, numbers first, no filler." Limits and model config unchanged.
- REQ-1203 [always] The system shall list every change as before → after in /app/memory/product/step18/copy_changes.md.
- REQ-1204 [always] The system shall not change testids, routes, API field names or any text used as a key.
