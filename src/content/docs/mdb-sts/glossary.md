---
title: Glossary
description: MDB / STS / MDF terms QA uses day to day.
---

| Term | Plain meaning |
|------|----------------|
| **MDB** | Metamodel Database — Neo4j graph of models, properties, terms, value sets, synonyms |
| **MDF** | Model Description Format — YAML describing a model (nodes, props, enums) |
| **STS** | Simple Terminology Server — HTTP API reading MDB (`/v2/...`) |
| **PV / PVS** | Permissible value(s) for a property |
| **CDE** | caDSR Common Data Element (often in MDF `Term:` block) |
| **Value set** | Terms allowed for a property in the graph |
| **Changelog** | XML of Cypher applied to Neo4j |
| **Origin** | Term authority (caDSR, NCIt, CRDC, …) |
| **EDP** | Extended Definition Property — a named, versioned PV list stored in MDB and served by STS |
| **Promotion** | Copy a full MDB graph from one CloudOne environment into another (export → S3 → import) |
| **Prerelease** | Model version string with a hyphen (not an official `latest_version` release) |
| **Handle** | Stable name for a model, node, or property in MDF/STS (e.g. `CDS`, `participant`, `race`) |

**Graph (simplified):** model → node → property → value_set → term (+ concept, origin)

See also [EDPs](/mdb-sts/edps/) for `Term:` vs `Enum:` and CRDC vs caDSR origins.
