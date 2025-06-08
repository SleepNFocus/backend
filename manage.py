#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path

# python-dotenv 모듈은 기본적으로 타입 스텁이 없으므로 무시합니다.
from dotenv import load_dotenv

# 프로젝트 최상위(.env가 위치한 곳)에 있는 .env 파일을 로드
load_dotenv(Path(__file__).resolve().parent / ".env")


def main() -> None:
    """Run administrative tasks."""
    # os.environ.get(...)은 반환형이 항상 str이므로 mypy 오류가 없습니다.
    env_value = os.environ.get("DJANGO_ENV", "local")
    env: str = env_value  # 명시적으로 str으로 단언

    # 예: DJANGO_ENV=prod → "config.settings.prod"를 사용
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"config.settings.{env}")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
