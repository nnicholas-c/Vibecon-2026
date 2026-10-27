import subprocess
import sys
from pathlib import Path


def test_step4_mocked_google_gmail_journeys():
    """Runs the in-process mocked Google/Gmail journeys (own throwaway DB)."""
    root = Path(__file__).resolve().parents[1]
    out = subprocess.run([sys.executable, "scripts/step4_mock_check.py"], cwd=root, capture_output=True, text=True, timeout=600)
    assert out.returncode == 0, out.stdout[-3000:]
    assert "FAIL " not in out.stdout
