"""
Streamlit 앱 런처.
- 실행 시 현재 Claude Code OAuth 토큰을 secrets.toml에 자동 갱신
- ANTHROPIC_API_KEY 환경변수로 Streamlit 서브프로세스에 주입
"""
import os
import re
import subprocess
import sys
import pathlib

ROOT = pathlib.Path(__file__).parent


def get_current_key() -> str:
    return os.getenv("ANTHROPIC_API_KEY", "") or os.getenv("CLAUDE_CODE_OAUTH_TOKEN", "")


def update_secrets(key: str):
    secrets_path = ROOT / ".streamlit" / "secrets.toml"
    secrets_path.parent.mkdir(exist_ok=True)
    secrets_path.write_text(f'ANTHROPIC_API_KEY = "{key}"\n', encoding="utf-8")
    print(f"[run.py] secrets.toml 갱신 완료: {key[:30]}...")


def main():
    key = get_current_key()
    if not key:
        print("[run.py] 경고: ANTHROPIC_API_KEY / CLAUDE_CODE_OAUTH_TOKEN 환경변수 없음")
        print("[run.py] 기존 secrets.toml 키로 시도합니다.")
    else:
        update_secrets(key)

    env = os.environ.copy()
    if key:
        env["ANTHROPIC_API_KEY"] = key

    port = sys.argv[1] if len(sys.argv) > 1 else "8501"

    print(f"[run.py] Streamlit 시작 → http://localhost:{port}")
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", "app.py",
         "--server.port", port,
         "--server.headless", "false"],
        env=env,
        cwd=str(ROOT),
    )


if __name__ == "__main__":
    main()
