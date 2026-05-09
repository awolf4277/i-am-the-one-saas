# Copyright Â© 2026 Andrew Wolverton. All Rights Reserved.
from __future__ import annotations

import os

from app import create_app

app = create_app()
application = app

print(f"WSGI loaded successfully. Routes registered: {len(app.url_map._rules)}", flush=True)

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5050"))
    app.run(host="0.0.0.0", port=port)

