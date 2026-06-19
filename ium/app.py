#!/usr/bin/env python3
"""Ium API server launcher

Usage:
    python app.py              # default: 127.0.0.1:8000
    python app.py --reload     # dev mode (auto-reload)
    python app.py --host 0.0.0.0 --port 5000
"""
import os
import sys

# Ensure backend/ is on PYTHONPATH so "app.main" resolves
_BACKEND_DIR = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, _BACKEND_DIR)

if __name__ == "__main__":
    import argparse
    import uvicorn
    from dotenv import load_dotenv

    # Load env files
    load_dotenv()
    backend_env = os.path.join(_BACKEND_DIR, ".env")
    if os.path.exists(backend_env):
        load_dotenv(backend_env)

    parser = argparse.ArgumentParser(description="Ium API server")
    parser.add_argument("--host", default="127.0.0.1", help="bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="port (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="dev mode (auto-reload)")
    parser.add_argument("--workers", type=int, default=1, help="worker count (default: 1, cannot use with --reload)")
    parser.add_argument("--skip-emotion", action="store_true", help="skip emotion model loading")
    args = parser.parse_args()

    # Default env values
    if not os.getenv("DATABASE_URL"):
        os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./backend/local_ium.db"
        print("[WARN] DATABASE_URL not set, using SQLite")
    if not os.getenv("MEDIA_CACHE_DIR"):
        os.environ["MEDIA_CACHE_DIR"] = "./backend/local_media_cache"
    os.makedirs(os.environ["MEDIA_CACHE_DIR"], exist_ok=True)

    if args.skip_emotion:
        os.environ["SKIP_EMOTION"] = "true"
        print("[INFO] SKIP_EMOTION=true")

    print("=" * 50)
    print("  Ium API Server")
    print(f"  URL: http://{args.host}:{args.port}")
    print(f"  Mode: {'dev(reload)' if args.reload else 'prod'}")
    print(f"  DB: {os.environ['DATABASE_URL'].split('://')[0]}")
    print("=" * 50)

    # Pass app as import string so --reload / --workers work correctly
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,
        log_level="info",
    )
