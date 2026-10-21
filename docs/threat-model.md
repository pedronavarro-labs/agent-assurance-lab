# Threat model notes

## `listChanged` during a session

The `listChanged` fixture represents a server announcing that its tool catalogue changed. Agent Assurance treats the event as a signal and compares the new snapshot with the approved definitions. A changed description or schema produces a failure.

## Declared read-only tool with a write effect

The read-only fixture documents a limitation: a manifest and a tool snapshot describe declarations, not necessarily the implementation behind a handler. Static analysis cannot prove that a handler never writes data without runtime evidence. This case belongs in the dynamic replay and benchmark layers rather than being silently reported as safe.
