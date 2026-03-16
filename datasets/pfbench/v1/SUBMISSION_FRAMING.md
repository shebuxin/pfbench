# Submission framing notes

## Recommended paper positioning

- Present `pfbench` as a released dataset collection of solved, structured power-flow benchmark artifacts.
- Treat the source repository and factory code as the supporting method used to create and validate the release.
- Keep the archival focus on the frozen package in this directory and the external repository record that will host it.

## Evidence the paper can center

- Frozen release size: 124 solved scenarios and 1240 question items.
- Coverage across 7 network cases and 10 structured query families.
- Explicit scenario-level provenance, full post-mutation network state, and AC/DC power-flow results.
- Schema validation, checksums, release manifest, and transparent failed-scenario logging.

## Suggested manuscript emphasis

- Motivation for structured power-flow benchmark datasets.
- Source case selection and perturbation protocol.
- File inventory, schemas, and intended reuse patterns.
- Quality control: validation, split policy, leakage controls, and limitations.
- Access instructions pointing to the deposited release package and DOI.

## What should remain secondary

- Internal code organization of the factory.
- CLI ergonomics.
- Future OpenAI or agent-evaluation plans that are not part of the frozen dataset release.
