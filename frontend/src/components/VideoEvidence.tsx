import { useEffect, useState } from "react";
import { api } from "../api";
import type { Observation } from "../types";

export function VideoEvidence({ observation }: { observation: Observation }) {
  const mediaId = observation.video?.media_id;
  const videoResult = observation.analysis.video;
  const [videoUrl, setVideoUrl] = useState("");
  const [frameUrls, setFrameUrls] = useState<string[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!mediaId) return;
    let active = true;
    const urls: string[] = [];
    void Promise.all([
      api.getMediaBlob(`/media/${mediaId}`),
      ...(videoResult.representative_frames ?? []).map((_, index) =>
        api.getMediaBlob(`/media/${mediaId}/frames/${index}`)),
    ]).then(([video, ...frames]) => {
      if (!active) return;
      const nextVideo = URL.createObjectURL(video);
      const nextFrames = frames.map((frame) => URL.createObjectURL(frame));
      urls.push(nextVideo, ...nextFrames);
      setVideoUrl(nextVideo); setFrameUrls(nextFrames);
    }).catch((reason) => setError(reason instanceof Error ? reason.message : "Media could not be loaded."));
    return () => { active = false; urls.forEach((url) => URL.revokeObjectURL(url)); };
  }, [mediaId, videoResult.representative_frames]);

  if (!mediaId) return null;
  return <section className="card video-evidence">
    <p className="eyebrow">Private video analysis</p>
    <h2>Visible motion evidence</h2>
    {videoUrl && <video controls preload="metadata" src={videoUrl}>Your browser cannot play this video.</video>}
    {error && <p className="error">{error}</p>}
    {frameUrls.length > 0 && <div className="representative-frames">{frameUrls.map((url, index) =>
      <img key={url} src={url} alt={`Representative video frame ${index + 1}`} />)}
    </div>}
    {videoResult.evidence.length > 0 && <ul>{videoResult.evidence.map((item) => <li key={item.key}>{item.observation}</li>)}</ul>}
    {(videoResult.quality_warnings ?? []).map((warning) => <p className="notice" key={warning}>{warning}</p>)}
    <p>{videoResult.explanation}</p>
    <p className="result-disclaimer">Video motion is shown separately and has not affected the final behavioural interpretation.</p>
  </section>;
}
