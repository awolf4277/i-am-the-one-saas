from datetime import datetime
from pathlib import Path
import shutil

root = Path(r"X:\i-am-the-one-saas")
path = root / "backend" / "app" / "__init__.py"

text = path.read_text(encoding="utf-8")

route_signature = '/api/stores/<slug>/products/<product_id>'

if route_signature in text:
    print("Inventory update route already exists. No changes made.")
    raise SystemExit(0)

target = '    @app.post("/api/stores/<slug>/checkout")'

if target not in text:
    raise RuntimeError("Could not find checkout route insertion point.")

timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup_dir = root / "backups" / "inventory-fix"
backup_dir.mkdir(parents=True, exist_ok=True)

backup_path = backup_dir / f"__init__.before-inventory-route-{timestamp}.py"
shutil.copy2(path, backup_path)

route_code = r'''
    @app.route(
        "/api/stores/<slug>/products/<product_id>",
        methods=["PUT"],
    )
    def owner_update_store_product(slug: str, product_id: str):
        ok, error = require_owner()
        if not ok:
            return error

        payload = request.get_json(silent=True) or {}

        if "stock" not in payload:
            return jsonify(
                {
                    "ok": False,
                    "error": "Stock is required.",
                }
            ), 400

        try:
            stock = int(payload.get("stock"))
        except (TypeError, ValueError):
            return jsonify(
                {
                    "ok": False,
                    "error": "Stock must be a whole number.",
                }
            ), 400

        if stock < 0:
            return jsonify(
                {
                    "ok": False,
                    "error": "Stock cannot be negative.",
                }
            ), 400

        con = connect(app)

        try:
            existing = con.execute(
                """
                SELECT p.id
                FROM products AS p
                INNER JOIN stores AS s
                    ON s.id = p.store_id
                WHERE p.id = ?
                  AND s.slug = ?
                LIMIT 1
                """,
                (product_id, slug),
            ).fetchone()

            if not existing:
                return jsonify(
                    {
                        "ok": False,
                        "error": f"Product not found: {product_id}",
                    }
                ), 404

            updated_at = now_iso()

            con.execute(
                """
                UPDATE products
                SET stock = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (stock, updated_at, product_id),
            )

            con.commit()

            row = con.execute(
                """
                SELECT
                    p.id,
                    p.store_id,
                    s.slug AS store_slug,
                    p.sku,
                    p.name,
                    p.category,
                    p.description,
                    p.price_cents,
                    p.stock,
                    p.image_url,
                    p.updated_at
                FROM products AS p
                INNER JOIN stores AS s
                    ON s.id = p.store_id
                WHERE p.id = ?
                LIMIT 1
                """,
                (product_id,),
            ).fetchone()

            return jsonify(
                {
                    "ok": True,
                    "message": "Stock updated.",
                    "product": product_dict(row),
                }
            )
        finally:
            con.close()


'''

text = text.replace(target, route_code + target, 1)
path.write_text(text, encoding="utf-8")

print(f"Backup created: {backup_path}")
print("Added authenticated product inventory PUT route.")
