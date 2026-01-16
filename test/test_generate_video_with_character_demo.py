import json
import os
import re
import time

from curl_cffi import requests


class TestGenerateVideoWithCharacterDemo:
    def test_generate_video_with_character_demo(self):
        base_url = os.getenv("SORA2API_BASE_URL", "http://localhost:8000").rstrip("/")
        api_key = os.getenv("SORA2API_API_KEY", "han1234")
        verbose = os.getenv("SORA2API_TEST_VERBOSE", "1").strip().lower() not in {"0", "false", "no", "off"}

        # Default character card payload (can be overridden via env var)
        character_json = os.getenv(
            "SORA2API_CHARACTER_JSON",
            json.dumps(
                {
                    "success": True,
                    "username": "quackchamp386",
                    "display_name": "Sunny Rally Duck",
                    "character_id": "ch_69666ca2a63c81918e80eaf4ddfe8815",
                    "cameo_id": "69666ca2c39081919af589edb0c796d9",
                },
                ensure_ascii=False,
            ),
        )
        character = json.loads(character_json)

        username = str(character.get("username") or "").strip()
        assert username, "Missing username in character json"

        model = os.getenv("SORA2API_VIDEO_MODEL", "sora2-portrait-10s")
        prompt = os.getenv("SORA2API_VIDEO_PROMPT", "角色做一个跳舞的动作")

        # Backend uses '@username + prompt' to trigger character video generation
        full_prompt = f"@{username} {prompt}".strip()

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": full_prompt,
                }
            ],
            "stream": True,
        }

        if verbose:
            print(f"[demo] POST {base_url}/v1/chat/completions")
            print(f"[demo] character={character.get('display_name')} (@{username})")
            print(f"[demo] model={model}")
            print(f"[demo] prompt={full_prompt}")

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
            print(f"[demo] status_code={resp.status_code}")
            ct = resp.headers.get("content-type") if hasattr(resp, "headers") else None
            if ct:
                print(f"[demo] content-type={ct}")

        assert resp.status_code == 200, resp.text

        last_json = None
        last_data = None
        got_data_event = False
        video_url = None
        start = time.time()

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
                last_json = None

            if last_json and isinstance(last_json, dict):
                # Final content is markdown with embedded <video src='...'>
                choices = last_json.get("choices") or []
                if choices:
                    delta = (choices[0] or {}).get("delta") or {}
                    content = delta.get("content")
                    if content and "<video" in content:
                        m = re.search(r"<video\s+src='([^']+)'", content)
                        if m:
                            video_url = m.group(1)

            if time.time() - start > 90:
                break

        assert got_data_event, "No SSE 'data:' events received from streaming endpoint"

        if verbose:
            if video_url:
                print(f"[demo] video_url={video_url}")
            elif last_json is not None:
                print("[demo] last_json=")
                print(json.dumps(last_json, ensure_ascii=False, indent=2))
            elif last_data is not None:
                print(f"[demo] last_data={last_data}")

        # Optional strict mode: require final video URL
        require_url = os.getenv("SORA2API_REQUIRE_VIDEO_URL", "0").strip().lower() in {"1", "true", "yes", "on"}
        if require_url:
            assert video_url, "Did not obtain final <video src='...'> URL from stream"


if __name__ == "__main__":
    TestGenerateVideoWithCharacterDemo().test_generate_video_with_character_demo()
