import base64
import json
import os
import subprocess
import time
from pathlib import Path

from curl_cffi import requests


def _read_video_as_data_uri(video_path: Path) -> str:
    video_b64 = base64.b64encode(video_path.read_bytes()).decode("utf-8")
    return f"data:video/mp4;base64,{video_b64}"


def _ffprobe_has_audio(video_path: Path) -> bool:
    try:
        p = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "a",
                "-show_entries",
                "stream=index",
                "-of",
                "csv=p=0",
                str(video_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        return bool(p.stdout.strip())
    except Exception:
        return False


def _transcode_for_sora(video_path: Path, verbose: bool) -> Path:
    out_dir = Path(os.getenv("SORA2API_TEST_TRANSCODE_DIR", str(video_path.parent)))
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{video_path.stem}.sora.mp4"

    has_audio = _ffprobe_has_audio(video_path)
    if has_audio:
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-map",
            "0:v:0",
            "-map",
            "0:a:0",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-ar",
            "44100",
            "-ac",
            "2",
            "-shortest",
            str(out_path),
        ]
    else:
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-f",
            "lavfi",
            "-i",
            "anullsrc=channel_layout=stereo:sample_rate=44100",
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-ar",
            "44100",
            "-ac",
            "2",
            "-shortest",
            str(out_path),
        ]

    if verbose:
        print("[ffmpeg] " + " ".join(cmd))

    p = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if p.returncode != 0 or not out_path.exists():
        raise AssertionError(f"ffmpeg transcode failed (code={p.returncode}):\n{p.stderr}\n{p.stdout}")

    return out_path


def test_chat_completions_video_url_stream():
    base_url = os.getenv("SORA2API_BASE_URL", "http://localhost:8000").rstrip("/")
    api_key = os.getenv("SORA2API_API_KEY", "han1234")
    verbose = os.getenv("SORA2API_TEST_VERBOSE", "1").strip().lower() not in {"0", "false", "no", "off"}
    video_name = os.getenv("SORA2API_TEST_VIDEO", "aaaa.mp4")
    transcode = os.getenv("SORA2API_TEST_TRANSCODE", "1").strip().lower() not in {"0", "false", "no", "off"}

    video_path = Path(__file__).parent / video_name
    assert video_path.exists(), f"Missing test video: {video_path}"

    if transcode:
        video_path = _transcode_for_sora(video_path, verbose)

    video_data_uri = _read_video_as_data_uri(video_path)
    video_b64 = video_data_uri.split("base64,", 1)[1] if "base64," in video_data_uri else video_data_uri

    payload = {
        "model": "sora2-portrait-10s",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "video_url",
                        "video_url": {"url": video_data_uri},
                    }
                ],
            }
        ],
        "stream": True,
    }

    if verbose:
        print(f"[test] POST {base_url}/v1/chat/completions")
        print(f"[test] video={video_path.name} bytes={video_path.stat().st_size}")
        print(f"[test] model={payload['model']} stream={payload['stream']}")
        print(f"[test] video_base64_len={len(video_b64)} prefix={video_b64[:48]}")

    resp = requests.post(
        f"{base_url}/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        stream=True,
        timeout=60,
    )

    if verbose:
        print(f"[test] status_code={resp.status_code}")
        content_type = resp.headers.get("content-type") if hasattr(resp, "headers") else None
        if content_type:
            print(f"[test] content-type={content_type}")

    assert resp.status_code == 200, resp.text

    got_data_event = False
    start = time.time()
    last_json = None
    last_data = None

    for line in resp.iter_lines():
        if not line:
            continue

        if isinstance(line, bytes):
            line = line.decode("utf-8", errors="ignore")

        if not line.startswith("data: "):
            continue

        got_data_event = True
        data = line[len("data: ") :]
        last_data = data

        if verbose:
            printable = data if len(data) <= 800 else data[:800] + "..."
            print(f"[sse] {printable}")

        if data == "[DONE]":
            break

        try:
            last_json = json.loads(data)
        except Exception:
            pass

        if time.time() - start > 30:
            break

    assert got_data_event, "No SSE 'data:' events received from streaming endpoint"

    if verbose:
        if last_json is not None:
            print("[test] last_json=")
            print(json.dumps(last_json, ensure_ascii=False, indent=2))
        elif last_data is not None:
            print(f"[test] last_data={last_data}")


if __name__ == "__main__":
    test_chat_completions_video_url_stream()
