"""Refresh warehouse export and open the RideFlow BI HTML dashboard."""

from __future__ import annotations

import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.export_dashboard_data import export


def main() -> None:
    export()
    html = (ROOT / "dashboards" / "rideflow_bi_dashboard.html").resolve()
    webbrowser.open(html.as_uri())
    print(f"Opened {html}")


if __name__ == "__main__":
    main()
