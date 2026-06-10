# QueryMind v2 Architecture

## Design principles
- Thin API layer, no business logic in routes.
- Pure domain models without framework coupling.
- Service layer orchestrates pipeline.
- External systems accessed only via adapters.
- Deterministic fallback behavior and explicit confidence.

## Pipeline
1. Intent classification
2. NL to query translation
3. Query execution
4. Result reasoning
5. Fact validation
6. Response formatting

## Non-functional requirements
- Every stage must be unit testable.
- Mock mode must be explicit and deterministic.
- API responses must expose confidence and fact-check details.
- Fallbacks must preserve original intent as much as possible.