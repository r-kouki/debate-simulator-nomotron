#!/usr/bin/env python3
"""Test script to verify real-time argument streaming from XP server."""

import requests
import json
import time

BASE_URL = "http://localhost:5040/api"

def test_streaming_debate():
    """Test creating a debate and streaming arguments in real-time."""
    print("="*60)
    print("TESTING XP SERVER REAL-TIME STREAMING")
    print("="*60)

    # Check health
    print("\n[1/3] Checking server health...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"  Status: {response.json()['status']}")
    print(f"  CrewAI Available: {response.json()['crewai_available']}")

    # Create debate
    print("\n[2/3] Creating debate...")
    debate_payload = {
        "topic": "Should schools teach coding from elementary school?",
        "rounds": 1,
        "use_internet": False,
        "recommend_guests": False
    }

    response = requests.post(f"{BASE_URL}/debates", json=debate_payload)
    debate_data = response.json()
    debate_id = debate_data["id"]
    print(f"  Debate ID: {debate_id}")
    print(f"  Status: {debate_data['status']}")

    # Stream progress
    print("\n[3/3] Streaming debate progress...")
    print("  Listening for SSE events...\n")

    stream_url = f"{BASE_URL}/debates/{debate_id}/stream"

    with requests.get(stream_url, stream=True, timeout=120) as response:
        event_count = 0
        argument_count = 0

        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')

                if line.startswith('data: '):
                    data_str = line[6:]  # Remove 'data: ' prefix
                    try:
                        data = json.loads(data_str)
                        event_type = data.get('type', 'unknown')
                        event_count += 1

                        # Print event info
                        if event_type == 'debate_started':
                            print(f"  ✓ Debate started: {data.get('topic')}")

                        elif event_type == 'log':
                            step = data.get('step', 'Unknown')
                            message = data.get('message', '')
                            progress = data.get('progress', 0)
                            print(f"  [{progress:5.1f}%] {step}: {message}")

                        elif event_type == 'argument':
                            argument_count += 1
                            side = data.get('side', 'unknown').upper()
                            round_num = data.get('round', 0)
                            content = data.get('content', '')[:100]
                            print(f"\n  🎯 ARGUMENT #{argument_count} RECEIVED ({side}, Round {round_num}):")
                            print(f"     {content}...\n")

                        elif event_type == 'debate_complete':
                            winner = data.get('winner', 'unknown').upper()
                            judge_score = data.get('judgeScore', {})
                            print(f"\n  🏆 DEBATE COMPLETE!")
                            print(f"     Winner: {winner}")
                            print(f"     Pro: {judge_score.get('proScore')}, Con: {judge_score.get('conScore')}")
                            break

                        elif event_type == 'error':
                            print(f"  ✗ Error: {data.get('message')}")
                            break

                    except json.JSONDecodeError:
                        continue

        print(f"\n  Total events received: {event_count}")
        print(f"  Total arguments received: {argument_count}")

    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    try:
        test_streaming_debate()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except requests.exceptions.ConnectionError:
        print("\n✗ ERROR: Cannot connect to server. Is it running on port 5040?")
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
