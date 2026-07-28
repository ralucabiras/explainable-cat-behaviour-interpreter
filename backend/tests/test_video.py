from pathlib import Path

import cv2
import numpy as np
import pytest

from app.ai.video_analyser import InvalidVideoError, VideoAnalyser, VideoTooLongError
from app.models.observation import AnalysisStatus, BehaviourState, EvidenceSource


def test_still_video_returns_explainable_uncertain_result(tmp_path: Path) -> None:
    path = tmp_path / "still.avi"
    _write_video(path, [np.zeros((64, 96, 3), dtype=np.uint8) for _ in range(10)])

    analysis = VideoAnalyser().analyse(path)

    assert analysis.result.status == AnalysisStatus.COMPLETED
    assert analysis.result.label == BehaviourState.UNCERTAIN
    assert analysis.result.feature_values["stillness_ratio"] == 1
    assert analysis.result.evidence[0].source == EvidenceSource.VIDEO
    assert len(analysis.frame_images) == 3


def test_motion_video_reports_motion_without_changing_to_a_behaviour_state(
    tmp_path: Path,
) -> None:
    path = tmp_path / "motion.avi"
    frames = []
    for position in range(12):
        frame = np.zeros((64, 96, 3), dtype=np.uint8)
        cv2.rectangle(frame, (position * 5, 20), (position * 5 + 20, 40), (255, 255, 255), -1)
        frames.append(frame)
    _write_video(path, frames)

    result = VideoAnalyser().analyse(path).result

    assert result.label == BehaviourState.UNCERTAIN
    assert result.feature_values["peak_motion"] > 0


def test_invalid_and_overlong_video_are_rejected(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.mp4"
    invalid.write_bytes(b"not a video")
    with pytest.raises(InvalidVideoError):
        VideoAnalyser().analyse(invalid)

    video = tmp_path / "long.avi"
    _write_video(video, [np.zeros((64, 96, 3), dtype=np.uint8) for _ in range(12)], fps=2)
    with pytest.raises(VideoTooLongError):
        VideoAnalyser().analyse(video, max_seconds=5)


def _write_video(path: Path, frames: list[np.ndarray], fps: float = 10) -> None:
    writer = cv2.VideoWriter(
        str(path),
        cv2.VideoWriter_fourcc(*"MJPG"),
        fps,
        (frames[0].shape[1], frames[0].shape[0]),
    )
    assert writer.isOpened()
    for frame in frames:
        writer.write(frame)
    writer.release()
