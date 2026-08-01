# Animal Kingdom cloud workflow

The raw Animal Kingdom package is private in Google Cloud Storage. Raw media is never
committed to this repository, and the audit commands do not make the bucket public.

## Configuration

Set these values in the repository-root `.env`:

```text
GCS_DATASET_BUCKET=cat-behaviour-research-raluca-2026
GCS_DATASET_PREFIX=raw/animal-kingdom
```

Authenticate locally with `gcloud init`. A service-account key is not required for local
research or Colab. Never commit Google credentials.

## Read-only inventory

```powershell
python -m app.video_dataset.cli cloud-inventory `
  --output video_dataset/reports/cloud-inventory.json
```

The inventory records object names, byte sizes, generations, CRC32C values, storage
classes, and composite-object counts. It neither downloads nor modifies objects.

## No-large-download Animal Kingdom audit

```powershell
python -m app.video_dataset.cli animal-kingdom-cloud-audit `
  --output-dir video_dataset/reports/animal-kingdom-v1
```

This command:

1. inventories the configured bucket prefix;
2. verifies that the action annotation ZIP and video archive objects exist;
3. downloads only the approximately 59 MB action annotation/code ZIP;
4. parses the 140-entry action taxonomy;
5. aggregates frame annotations by original source-video ID;
6. maps selected visible actions into stable project labels;
7. writes a report and candidate manifest.

It does **not** download, extract, or list the contents of the 15.6 GB video archive.
Consequently, candidate member paths use the documented `video/{ID}.mp4` convention but
are marked unverified until cloud preprocessing reads the archive.

Generated reports are ignored by Git. The small reviewed baseline summary under
`video_dataset/baselines/` is tracked.

## Generated artifacts

- `cloud-inventory.json`: safe cloud metadata, no credentials or media URLs.
- `cloud-audit-summary.json`: confirms which objects were read.
- `action-report.json`: source-video and mapped-action counts plus limitations.
- `candidate-manifest.json`: one candidate per source video and mapped action.

Candidates are deliberately not marked `included`. Animal Kingdom action annotations do
not contain species, and the supplied package does not contain a machine-readable licence
identifier. Species suitability and the research agreement must be recorded before clips
become trainable.

## Action mapping

The initial mapping keeps visible actions separate:

`drinking`, `eating`, `exploring`, `grooming`, `hissing`, `keeping_still`, `licking`,
`locomotion`, `lying_down`, `playing`, `resting`, `running`, `sitting`, `sleeping`, and
`walking`.

These labels are video evidence, not emotional, behavioural-state, medical, or diagnostic
claims. They must not be directly converted into states such as fearful or unwell.

## Next cloud stage

The candidate manifest is the input to a cloud/Colab sampling job. That job should stream
selected archive members, create small review previews, and write them under a versioned
`curated/review-v1/` prefix. A human then labels species suitability before any model is
trained. Grouping and final train/validation/test splits must use the original source-video
ID so a video never crosses splits.

## Colab species review

The deterministic plan is tracked at
`video_dataset/review/animal-kingdom-review-v1.plan.json`. It requests 20 examples per
mapped action where available and contains 203 unique source videos. `lying_down` has only
one source video and `sleeping` only 18, so those classes cannot reach 20.

After these repository changes are committed and pushed, open:

<https://colab.research.google.com/github/ralucabiras/explainable-cat-behaviour-interpreter/blob/main/backend/video_dataset/notebooks/animal_kingdom_review.ipynb>

Use a CPU runtime. The notebook will:

1. authenticate your Google account;
2. clone this repository to obtain the frozen review plan;
3. stream the 15.6 GB compressed action archive once;
4. extract only the 203 selected videos to temporary Colab storage;
5. present each video with species, suitability, visible-action, and notes controls;
6. checkpoint labels privately to
   `gs://cat-behaviour-research-raluca-2026/curated/review-v1/review-labels.json`.

Use `unclear` instead of guessing. A clip is `suitable` only when the animal and mapped
action are visible enough to support an observable-action model. Wild felines and other
animals should still receive their correct species category; suitability is a separate
decision.

After downloading the completed labels locally, validate them with:

```powershell
python -m app.video_dataset.cli review-validate `
  --plan video_dataset/review/animal-kingdom-review-v1.plan.json `
  --labels review-labels.json `
  --require-complete
```
