#!/usr/bin/env python3
"""
Run the Debate Simulator API server.

Loads the LLM model at startup for fast inference during debates.

Usage:
    python scripts/run_server.py [--port PORT] [--no-model] [--reload]

Options:
    --port PORT     Port to run on (default: 8000)
    --no-model      Skip model loading (for testing API without LLM)
    --reload        Enable auto-reload for development
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def main():
    parser = argparse.ArgumentParser(description="Run the Debate Simulator API")
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8000,
        help="Port to run on (default: 8000)"
    )
    parser.add_argument(
        "--no-model",
        action="store_true",
        help="Skip model loading (for testing API structure)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("DEBATE SIMULATOR API SERVER")
    print("=" * 60)

    # Load model if not skipped
    if not args.no_model:
        print("\n--- Loading LLM Model ---")
        print("This may take 1-2 minutes...")

        try:
            from src.utils.model_loader import load_base_model, ADAPTERS_PATH
            from peft import PeftModel

            model, tokenizer = load_base_model()
            print("✓ Base model loaded")

            # Try to load education adapter
            adapter_path = ADAPTERS_PATH / "education"
            if adapter_path.exists():
                model = PeftModel.from_pretrained(model, adapter_path)
                print(f"✓ Adapter loaded from {adapter_path}")
            else:
                print("  (No adapter found, using base model)")

            # Set model in debate service
            from src.serving.debate_service import debate_service
            debate_service.set_model(model, tokenizer)
            print("✓ Model ready for inference")

        except Exception as e:
            print(f"✗ Failed to load model: {e}")
            print("  Server will run with fallback responses")
    else:
        print("\n--- Skipping Model Loading ---")
        print("  API will return fallback responses")

    # Start server
    print(f"\n--- Starting Server ---")
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print(f"Reload: {args.reload}")
    print(f"\nAPI URL: http://localhost:{args.port}")
    print(f"Health: http://localhost:{args.port}/health")
    print("\nPress Ctrl+C to stop\n")

    import uvicorn
    uvicorn.run(
        "src.serving.api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        reload_dirs=[str(PROJECT_ROOT / "src")] if args.reload else None,
    )


if __name__ == "__main__":
    main()
