import urllib.request
import json
import sys

def test_all():
    print("Testing health endpoint...", flush=True)
    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=5) as resp:
            print(f"Health: {resp.read().decode('utf-8')}", flush=True)
    except Exception as e:
        print(f"Health failed: {e}", flush=True)

    for i in range(1, 9):
        inv_id = f"INV-100{i}"
        exc_id = f"EX-00{i}"
        payload = json.dumps({"invoice_id": inv_id, "exception_id": exc_id}).encode("utf-8")
        req = urllib.request.Request(
            "http://127.0.0.1:8000/api/investigations",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                status = data.get("status")
                summary = data.get("summary")
                validation_results = data.get("validation_results", [])
                passed = sum(1 for r in validation_results if r.get("status") == "PASS")
                failed = sum(1 for r in validation_results if r.get("status") == "FAIL")
                unknown = sum(1 for r in validation_results if r.get("status") == "UNKNOWN")
                print(f"{inv_id} -> {status} (PASS: {passed}, FAIL: {failed}, UNKNOWN: {unknown})", flush=True)
                print(f"   Summary: {summary}", flush=True)
        except Exception as e:
            print(f"{inv_id} -> ERROR: {e}", flush=True)

if __name__ == "__main__":
    test_all()
