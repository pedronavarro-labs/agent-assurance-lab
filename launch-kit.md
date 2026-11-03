# Boundary Signal — launch kit

This document contains the launch copy and visual references for the 1.0 preview.

## Product line

**Boundary Signal**  
*Verifiable boundaries for AI agents.*

## GitHub release note

### Boundary Signal 1.0 preview: from tool drift to an auditable decision

Boundary Signal is a local-first assurance console for AI agent tool surfaces.

It fingerprints approved and observed tool definitions, evaluates policy, records runtime evidence and produces a decision that CI can enforce.

The preview includes:

- a red-and-carbon operations console;
- deterministic checks for added, removed and modified tools;
- policy evaluation for unsafe tools and declared effects;
- runtime evidence for undeclared writes;
- signed approval evidence and SARIF output;
- a typed FastAPI service with local SQLite run history;
- a reproducible attack demo that works without a live agent or network access.

Start here: [`docs/demo-runbook.md`](demo-runbook.md).

![Boundary Signal attack story](attack-story.svg)

## LinkedIn update 1 — product launch

**Suggested image:** [`docs/launch-card.svg`](launch-card.svg). It includes the Boundary Signal mark and is sized for a social launch card.

> AI agents need a boundary that can be checked, not just described.
>
> I’m building Boundary Signal: a local-first assurance console that fingerprints tool definitions, evaluates policy and verifies runtime evidence before an agent is allowed to continue.
>
> The first 1.0 preview covers three failure modes:
> 
> • a tool is added after approval;
> • an existing tool changes its schema;
> • a handler declared read-only performs a write at runtime.
>
> Each scenario produces an auditable decision and can fail CI. No live agent or network access is required for the demo.
>
> The project is open source and the reproducible attack demo is included in the repository.
>
> Boundary Signal — verifiable boundaries for AI agents.
>
> #AI #Cybersecurity #AIAgents #MCP #AppSec #OpenSource

## LinkedIn update 2 — technical follow-up

**Suggested image:** [`docs/launch-card.svg`](launch-card.svg) or [`brand/boundary-signal-logo.png`](../brand/boundary-signal-logo.png).

> The dangerous part of an AI agent is not only what it is allowed to call. It is what the tool actually does.
>
> That is why Boundary Signal separates two checks:
>
> 1. static drift: compare the approved and observed tool surface using canonical SHA-256 fingerprints;
> 2. runtime evidence: compare session effects with the declared contract.
>
> A tool called `read_file` can keep the same name and still change its schema. A handler can also be labelled read-only while writing data. Both cases deserve a visible, reviewable decision.
>
> The demo reproduces both cases locally and returns a non-zero exit status so CI can block the change.
>
> #Cybersecurity #AIAgents #SoftwareSupplyChain #Python #DevSecOps

## Visual rules

- Use the Boundary Signal mark or full logo in every launch visual.
- Use signal red `#E11D2E`, carbon `#101010`, bone `#F3F0EC` and graphite `#2B2B2B`.
- Do not introduce blue into screenshots, diagrams or social artwork.
- Keep the product name as **Boundary Signal**; mention `agent-assurance-lab` only as the repository/package name.

## Profile copy proposal

### GitHub short bio

> Building Boundary Signal — verifiable boundaries for AI agents. Cybersecurity, agentic AI and reproducible assurance tooling.

### GitHub profile README opening

> I build security tooling for the boundary between AI agents and the systems they can reach.
>
> My current project is [Boundary Signal](https://github.com/pedronavarro-labs/agent-assurance-lab), a local-first assurance console that fingerprints agent tools, evaluates policy and verifies runtime evidence.

These profile changes are prepared as copy only; they should be applied after explicit approval of the final wording.
