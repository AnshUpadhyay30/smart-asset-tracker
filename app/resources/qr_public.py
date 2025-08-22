# app/resources/qr_public.py
# -----------------------------------------------------------------------------
# Public QR delivery (no auth). Designed to work with:
#  1) UPLOAD_FOLDER (preferred)       -> <UPLOAD_FOLDER>/<filename>
#  2) uploads/static/qr_codes         -> <UPLOAD_FOLDER>/static/qr_codes/<filename>
#  3) project static/qr_codes         -> <PROJECT_ROOT>/static/qr_codes/<filename>
#
# Example URLs:
#   GET /api/qr/asset_12.png
#   GET /api/qr/asset/12           (redirects to the file for asset 12)
# -----------------------------------------------------------------------------

import os
from flask import Blueprint, abort, send_from_directory, current_app, redirect
from werkzeug.utils import secure_filename

from app.models import Asset  # used by /qr/asset/<id>

qr_public_bp = Blueprint("qr_public", __name__)

# Allow only safe, expected file types
ALLOWED_EXT = {"png", "jpg", "jpeg", "webp", "gif", "svg", "pdf"}

def _safe_filename(name: str) -> str:
    """Normalize and validate a filename (no traversal, valid extension)."""
    cleaned = secure_filename(os.path.basename(name or ""))
    if not cleaned:
        abort(404)
    ext = cleaned.rsplit(".", 1)[-1].lower() if "." in cleaned else ""
    if ext not in ALLOWED_EXT:
        abort(404)
    return cleaned

def _candidates(filename: str) -> list[tuple[str, str]]:
    """
    Build candidate (directory, filename) pairs to try in order.
    Returns only directories; do not join here (safer with send_from_directory).
    """
    upload_dir = current_app.config.get("UPLOAD_FOLDER") or os.path.join(os.getcwd(), "uploads")
    project_root = os.getcwd()

    return [
        (upload_dir, filename),                                        # /uploads/<file>
        (os.path.join(upload_dir, "static", "qr_codes"), filename),    # /uploads/static/qr_codes/<file>
        (os.path.join(project_root, "static", "qr_codes"), filename),  # <project>/static/qr_codes/<file>
    ]

def _send_first_existing(filename: str):
    """Try candidate folders in order and send the first match."""
    for folder, fname in _candidates(filename):
        path = os.path.join(folder, fname)
        if os.path.isfile(path):
            resp = send_from_directory(folder, fname)
            # Mild caching—fine for generated images; adjust if needed.
            resp.headers["Cache-Control"] = "public, max-age=86400"
            return resp
    abort(404)

@qr_public_bp.get("/qr/<path:filename>")
def get_qr(filename: str):
    """
    Publicly serve a QR image by filename.
    Example: GET /api/qr/asset_12.png
    """
    safe = _safe_filename(filename)
    return _send_first_existing(safe)

@qr_public_bp.get("/qr/asset/<int:asset_id>")
def get_qr_by_asset(asset_id: int):
    """
    Convenience endpoint: get QR for an asset id without knowing the file name.
    Example: GET /api/qr/asset/12  -> redirects to /api/qr/<file>
    """
    asset = Asset.query.get_or_404(asset_id)
    if not asset.qr_code_path:
        abort(404)

    # Keep only the file name; let /api/qr/<file> resolve the final location.
    fname = _safe_filename(os.path.basename(asset.qr_code_path))
    # 302 redirect—lets you keep one canonical responder.
    return redirect(f"/api/qr/{fname}", code=302)