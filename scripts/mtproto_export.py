import json
import os
import zipfile


def build_media_archives(items, output_dir, max_batch_bytes=35 * 1024 * 1024, max_archive_bytes=40 * 1024 * 1024):
    eligible = [item for item in items if item.get("path")]
    batches = []
    current = []
    current_size = 0
    for item in eligible:
        size = item["bytes"]
        if size > max_batch_bytes:
            if current:
                batches.append(current)
                current = []
                current_size = 0
            batches.append([item])
            continue
        if current and current_size + size > max_batch_bytes:
            batches.append(current)
            current = []
            current_size = 0
        current.append(item)
        current_size += size
    if current:
        batches.append(current)

    archives = []
    for index, batch in enumerate(batches, 1):
        archive_path = os.path.join(output_dir, f"midias_parte_{index}.zip")
        manifest = [
            {
                "name": item["name"],
                "category": item["category"],
                "bytes": item["bytes"],
                "sha256": item["sha256"],
            }
            for item in batch
        ]
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
            for item in batch:
                archive.write(item["path"], arcname=item["name"])
        archive_size = os.path.getsize(archive_path)
        if archive_size > max_archive_bytes:
            if len(batch) == 1:
                batch[0]["status"] = "exceeds_safe_upload_size"
                os.remove(archive_path)
                continue
            raise ValueError("An archive batch exceeded the safe upload size")
        for item in batch:
            item["status"] = "packaged"
        archives.append(archive_path)
    return archives
