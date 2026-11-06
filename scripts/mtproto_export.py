import json
import os
import zipfile


def build_media_archives(items, output_dir, max_batch_bytes=None, max_archive_bytes=None):
    batch = [item for item in items if item.get("path")]
    if not batch:
        return []
    archive_path = os.path.join(output_dir, "midias_parte_1.zip")
    manifest = [{key: item[key] for key in ("name", "category", "bytes", "sha256")} for item in batch]
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        for item in batch:
            archive.write(item["path"], arcname=item["name"])
            item["status"] = "packaged"
    return [archive_path]
