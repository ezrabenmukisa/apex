from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.config import get_settings

router = APIRouter(prefix="/.well-known", tags=["Invite Links"],)


@router.get("/assetlinks.json", include_in_schema=False)
def android_asset_links():
    settings = get_settings()
    fingerprints = [
        f.strip().upper()
        for f in (
            settings.android_sha256_cert_fingerprint,
            settings.android_debug_sha256_cert_fingerprint,
        )
        if f.strip()
    ]

    if not fingerprints:
        raise HTTPException(
            status_code=503,
            detail="Android signing fingerprint is not configured.",
        )

    return JSONResponse(
        content=[
            {
                "relation": ["delegate_permission/common.handle_all_urls"],
                "target": {
                    "namespace": "android_app",
                    "package_name": "com.apex.app",
                    "sha256_cert_fingerprints": fingerprints,
                },
            }
        ]
    )