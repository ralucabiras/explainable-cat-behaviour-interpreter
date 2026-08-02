import json
import subprocess
from pathlib import Path
from typing import Any


class ColabReviewController:
    def __init__(
        self,
        plan: dict[str, Any],
        extract_root: Path,
        labels_uri: str,
    ) -> None:
        import ipywidgets as widgets
        from IPython.display import display

        self.widgets = widgets
        self.display = display
        self.plan = plan
        self.extract_root = extract_root
        self.labels_uri = labels_uri
        self.labels_path = extract_root / "review-labels.json"
        self.labels = self._load_checkpoint()
        self.index = 0
        self.saves_since_checkpoint = 0

        self.progress = widgets.HTML()
        self.status = widgets.HTML()
        self.video_output = widgets.Output()
        self.species = widgets.Dropdown(
            options=[
                "unreviewed",
                "domestic_cat",
                "wild_feline",
                "other_mammal",
                "non_mammal",
                "unclear",
            ],
            description="Species:",
        )
        self.suitability = widgets.Dropdown(
            options=["unreviewed", "suitable", "unsuitable", "unclear"],
            description="Suitable:",
        )
        self.visible = widgets.SelectMultiple(
            options=sorted(plan["coverage_by_action"]),
            description="Visible:",
            rows=7,
        )
        self.notes = widgets.Textarea(description="Notes:")

        top_navigation = self._navigation()
        bottom_navigation = self._navigation()
        display(
            widgets.VBox(
                [
                    self.progress,
                    top_navigation,
                    self.video_output,
                    self.species,
                    self.suitability,
                    self.visible,
                    self.notes,
                    bottom_navigation,
                    self.status,
                ]
            )
        )
        self.load_item(0)

    def _navigation(self):
        previous = self.widgets.Button(description="Previous")
        save_next = self.widgets.Button(description="Save & next", button_style="success")
        checkpoint = self.widgets.Button(description="Checkpoint now")
        previous.on_click(self._previous)
        save_next.on_click(self._save_next)
        checkpoint.on_click(self._checkpoint_clicked)
        return self.widgets.HBox([previous, save_next, checkpoint])

    def load_item(self, index: int) -> None:
        from IPython.display import Video, clear_output

        self.index = max(0, min(index, len(self.plan["items"]) - 1))
        item = self.plan["items"][self.index]
        previous = self.labels.get(item["id"], {})
        self.progress.value = (
            f"<b>Review {self.index + 1}/{len(self.plan['items'])}: "
            f"{item['source_clip_id']}</b><br>Mapped actions: {', '.join(item['actions'])}"
        )
        self.species.value = previous.get("species", "unreviewed")
        self.suitability.value = previous.get("suitability", "unreviewed")
        visible = previous.get("visible_actions", item["actions"])
        self.visible.value = tuple(action for action in visible if action in self.visible.options)
        self.notes.value = previous.get("notes", "")
        self.status.value = f"Saved: {len(self.labels)}/{len(self.plan['items'])}"
        with self.video_output:
            clear_output(wait=True)
            self.display(
                Video(
                    str(self.extract_root / item["archive_member"]),
                    embed=True,
                    width=640,
                )
            )

    def save_current(self) -> bool:
        if self.species.value == "unreviewed" or self.suitability.value == "unreviewed":
            self.status.value = (
                "<span style='color:#b45309'>Choose both species and suitability "
                "before saving.</span>"
            )
            return False
        item = self.plan["items"][self.index]
        self.labels[item["id"]] = {
            "item_id": item["id"],
            "species": self.species.value,
            "suitability": self.suitability.value,
            "visible_actions": list(self.visible.value),
            "notes": self.notes.value.strip(),
        }
        self.saves_since_checkpoint += 1
        return True

    def checkpoint(self) -> None:
        payload = {
            "schema_version": "1.0.0",
            "plan_version": self.plan["plan_version"],
            "labels": [self.labels[key] for key in sorted(self.labels)],
        }
        self.labels_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            ["gcloud", "storage", "cp", str(self.labels_path), self.labels_uri],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or "Could not upload checkpoint")
        self.saves_since_checkpoint = 0
        self.status.value = (
            f"<span style='color:#047857'>Checkpoint uploaded with "
            f"{len(self.labels)} labels.</span>"
        )

    def _load_checkpoint(self) -> dict[str, dict]:
        result = subprocess.run(
            ["gcloud", "storage", "cp", self.labels_uri, str(self.labels_path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if result.returncode:
            return {}
        payload = json.loads(self.labels_path.read_text(encoding="utf-8"))
        if payload.get("plan_version") != self.plan["plan_version"]:
            raise ValueError("Cloud checkpoint belongs to a different review plan")
        return {item["item_id"]: item for item in payload.get("labels", [])}

    def _previous(self, _) -> None:
        self.load_item(self.index - 1)

    def _save_next(self, _) -> None:
        try:
            if not self.save_current():
                return
            is_last = self.index == len(self.plan["items"]) - 1
            if self.saves_since_checkpoint >= 5 or is_last:
                self.checkpoint()
            if not is_last:
                self.load_item(self.index + 1)
            else:
                self.status.value = "<b>Review complete. Final checkpoint uploaded.</b>"
        except Exception as error:  # callbacks must surface errors in the visible UI
            self.status.value = f"<span style='color:#b91c1c'>Error: {error}</span>"

    def _checkpoint_clicked(self, _) -> None:
        try:
            self.checkpoint()
        except Exception as error:  # callbacks must surface errors in the visible UI
            self.status.value = f"<span style='color:#b91c1c'>Error: {error}</span>"


def launch_review(
    plan: dict[str, Any], extract_root: str | Path, labels_uri: str
) -> ColabReviewController:
    return ColabReviewController(plan, Path(extract_root), labels_uri)
