import json
import shutil
import subprocess
from pathlib import Path

from pydantic import Field

from app.models.common import APIModel


class CloudObject(APIModel):
    name: str
    size: int = Field(ge=0)
    crc32c: str
    generation: str
    storage_class: str
    component_count: int | None = Field(default=None, ge=1)


class CloudInventory(APIModel):
    bucket: str
    prefix: str
    total_bytes: int
    objects: list[CloudObject]


class GCloudStorage:
    def __init__(self, executable: str | None = None) -> None:
        resolved = executable or shutil.which("gcloud") or shutil.which("gcloud.cmd")
        if not resolved:
            raise ValueError("Google Cloud CLI was not found; install it or pass --gcloud")
        self.executable = resolved

    def inventory(self, bucket: str, prefix: str) -> CloudInventory:
        clean_prefix = prefix.strip("/")
        result = self._run("storage", "ls", "--json", f"gs://{bucket}/{clean_prefix}/**")
        payload = json.loads(result.stdout)
        objects = []
        for item in payload:
            if item.get("type") != "cloud_object":
                continue
            metadata = item["metadata"]
            objects.append(
                CloudObject(
                    name=metadata["name"],
                    size=int(metadata["size"]),
                    crc32c=metadata["crc32c"],
                    generation=metadata["generation"],
                    storage_class=metadata["storageClass"],
                    component_count=metadata.get("componentCount"),
                )
            )
        objects.sort(key=lambda item: item.name)
        return CloudInventory(
            bucket=bucket,
            prefix=clean_prefix,
            total_bytes=sum(item.size for item in objects),
            objects=objects,
        )

    def download(self, uri: str, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        self._run("storage", "cp", "--no-clobber", uri, str(destination))
        return destination

    def _run(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                [self.executable, *arguments],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        except subprocess.CalledProcessError as error:
            detail = (error.stderr or error.stdout or str(error)).strip()
            raise ValueError(f"Google Cloud command failed: {detail}") from error
