from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from app.models.observation import (
    AnalysisStatus,
    BehaviourState,
    EvidenceItem,
    EvidenceSource,
    ModalityResult,
)


class InvalidVideoError(ValueError):
    pass


class VideoTooLongError(ValueError):
    pass


@dataclass
class VideoAnalysis:
    result: ModalityResult
    duration: float
    fps: float
    width: int
    height: int
    frame_images: list[np.ndarray]


class VideoAnalyser:
    def analyse(self, path: Path, max_seconds: int = 30) -> VideoAnalysis:
        capture = cv2.VideoCapture(str(path))
        try:
            fps = float(capture.get(cv2.CAP_PROP_FPS))
            frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            if not capture.isOpened() or fps <= 0 or frame_count < 2 or width < 1 or height < 1:
                raise InvalidVideoError("The uploaded file is not a decodable video")
            duration = frame_count / fps
            if duration > max_seconds:
                raise VideoTooLongError(f"Video must be {max_seconds} seconds or shorter")
            indices = np.linspace(0, frame_count - 1, min(24, frame_count), dtype=int)
            frames = []
            for index in indices:
                capture.set(cv2.CAP_PROP_POS_FRAMES, int(index))
                ok, frame = capture.read()
                if ok:
                    frames.append(frame)
            if len(frames) < 2:
                raise InvalidVideoError("The video did not contain enough readable frames")
        finally:
            capture.release()

        grays = [cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (160, 90)) for frame in frames]
        motion = [
            float(np.mean(cv2.absdiff(previous, current) > 25))
            for previous, current in zip(grays, grays[1:], strict=False)
        ]
        average = float(np.mean(motion))
        peak = float(np.max(motion))
        stillness = float(np.mean(np.array(motion) < 0.01))
        burst_threshold = max(0.03, average * 1.75)
        bursts = float(np.mean(np.array(motion) > burst_threshold))
        warnings = []
        if average > 0.35:
            warnings.append("Large whole-frame changes may indicate camera movement.")
        evidence = []
        if stillness >= 0.6:
            evidence.append(
                EvidenceItem(
                    key="extended_stillness",
                    observation="extended periods of little visible movement",
                    source=EvidenceSource.VIDEO,
                )
            )
        if bursts >= 0.15:
            evidence.append(
                EvidenceItem(
                    key="motion_bursts",
                    observation="several bursts of visible movement",
                    source=EvidenceSource.VIDEO,
                )
            )
        if not evidence:
            evidence.append(
                EvidenceItem(
                    key="moderate_motion",
                    observation="a moderate amount of visible movement",
                    source=EvidenceSource.VIDEO,
                )
            )
        representative = sorted({0, len(frames) // 2, len(frames) - 1})
        representative_timestamps = [
            round(float(indices[index]) / fps, 3) for index in representative
        ]
        result = ModalityResult(
            status=AnalysisStatus.COMPLETED,
            label=BehaviourState.UNCERTAIN,
            confidence=0.25,
            evidence=evidence,
            detected_features=[item.key for item in evidence],
            explanation=(
                "Motion features were extracted, but motion alone cannot reliably determine "
                "a behavioural state."
            ),
            quality_warnings=warnings,
            representative_frames=representative_timestamps,
            feature_values={
                "average_motion": round(average, 4),
                "peak_motion": round(peak, 4),
                "stillness_ratio": round(stillness, 4),
                "motion_burst_ratio": round(bursts, 4),
                "fps": round(fps, 2),
            },
        )
        images = [frames[index] for index in representative]
        return VideoAnalysis(result, duration, fps, width, height, images)
