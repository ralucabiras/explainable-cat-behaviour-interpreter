# Observable Cat-Action Annotation Guide

This dataset labels visible actions, not emotions, intentions, health conditions, or
diagnoses. Annotators must use `uncertain` whenever the visible evidence does not clearly
meet one action definition.

## Labels

| Label | Include | Exclude |
| --- | --- | --- |
| `resting` | Cat is lying, sitting, or sleeping with little purposeful movement for most of the clip. | Brief pauses between other actions, hiding when the body cannot be observed. |
| `locomotion` | Walking, trotting, running, climbing, or sustained movement from one place to another. | A single posture adjustment, toy-directed pouncing. |
| `playing` | Repeated toy-directed, object-directed, or clearly reciprocal play actions such as chasing or pouncing. | Hunting live prey, defensive striking, one ambiguous jump. |
| `grooming` | Repeated licking, washing, scratching, or coat-care movements directed at the cat's own body. | Social grooming, one brief lick, suspected overgrooming as an emotional or medical label. |
| `eating` | Visible ingestion or repeated food-directed chewing/licking. | Merely approaching or sniffing food, drinking unless later introduced as a separate class. |
| `uncertain` | Multiple actions with no dominant action, obstruction, camera movement, insufficient duration, or ambiguous evidence. | Do not force a class to improve balance. |

## Clip rules

- Prefer clips of 2–30 seconds with one dominant action.
- Include only domestic cats with sufficient visible body information.
- Exclude edited compilations, heavy overlays, synthetic footage, and clips where the
  relevant action is mostly off-screen.
- Keep the original source video, uploader, and cat in one `group_id`; clips from the
  same group must never cross dataset splits.
- Record exact license provenance before setting a clip to `included`.
- A behaviour-state interpretation such as fearful, relaxed, stressed, aggressive, or
  unwell is never a video action label.

## Review

One annotator labels all candidates. A second person independently labels at least 20%
of included clips. Disagreements are retained in review notes and resolved before the
test split is frozen. Report Cohen's kappa for that double-labelled subset.
