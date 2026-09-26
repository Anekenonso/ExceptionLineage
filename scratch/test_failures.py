import urllib.request
import urllib.error
import json

def test_failures():
    # 1. Non-existent invoice (should transition to FAILED with graph retrieval error or fail-safe)
    payload = json.dumps({"invoice_id": "INV-9999", "exception_id": "EX-9999"}).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/investigations",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"Unknown invoice INV-9999 result: status={data.get('status')}, failure_reason={data.get('failure_reason')}")
            inv_id = data.get("investigation_id")
            # Fetch events
            with urllib.request.urlopen(f"http://127.0.0.1:8000/api/investigations/{inv_id}/events?include_agent_events=true") as ev_resp:
                events = json.loads(ev_resp.read().decode("utf-8"))
                print(f"   Events count: {len(events)}, last event: {events[-1] if events else 'None'}")
    except Exception as e:
        print(f"Unknown invoice error: {e}")

    # 2. Malformed investigation ID
    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/api/investigations/invalid-id-xyz", timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"Invalid ID result: {data}")
    except urllib.error.HTTPError as e:
        print(f"Invalid ID HTTP error code (expected 404): {e.code}, body: {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"Invalid ID error: {e}")

if __name__ == "__main__":
    test_failures()
