# Composition Engine Architecture

## Role of `__main__`
`__main__` is orchestration only. It loads config, invokes the engine layers in order, records status, and assembles approved outputs. It does not perform chart interpretation, prose composition, critique, or revision.

## Layer Order
`input_normalization -> significance_ranking -> interpretation -> composition -> critique -> revision -> final_assembly`

## Layer Responsibilities
- `input_normalization`: normalize structured chart facts
- `significance_ranking`: determine which factors matter most for the current section
- `interpretation`: convert ranked factors into chart-specific interpretation notes
- `composition`: convert interpretation notes into approved prose
- `critique`: evaluate draft quality against rubric rules
- `revision`: rewrite failed drafts
- `final_assembly`: collect approved section outputs into final report artifacts

## Core Rules
- Each layer has one primary responsibility
- Layers pass structured data forward whenever possible
- Each layer validates input before processing
- Invalid output does not move downstream
- Revision may re-enter the pipeline without rebuilding unrelated steps
- Voice rules, rubric rules, and stylebook rules should remain external where practical
