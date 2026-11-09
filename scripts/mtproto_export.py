import hashlib
import json
from pathlib import Path
import zipfile


def build_media_archives(items, output_dir, max_batch_bytes=40 * 1024 * 1024, max_archive_bytes=49 * 1024 * 1024):
    """Verify source hashes and split below hosted Bot API upload limits."""
    root = Path(output_dir).resolve()
    batches, batch, size = [], [], 0
    for item in items:
        if item.get('status') != 'downloaded':
            continue
        path = Path(item['path']).resolve()
        if not path.is_relative_to(root) or not path.is_file() or path.is_symlink():
            raise ValueError('Media path outside export directory')
        payload = path.read_bytes()
        if hashlib.sha256(payload).hexdigest() != item['sha256'] or len(payload) != item['bytes']:
            raise ValueError('Media SHA-256 verification failed')
        if len(payload) > max_batch_bytes:
            item['status'], item['error'] = 'not_packaged', 'File exceeds archive batch limit'
            continue
        if batch and size + len(payload) > max_batch_bytes:
            batches.append(batch)
            batch, size = [], 0
        batch.append(item)
        size += len(payload)
    if batch:
        batches.append(batch)
    paths = []
    for index, batch in enumerate(batches, 1):
        path = root / f'media_{index}.zip'
        with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            manifest = []
            for sequence, item in enumerate(batch):
                name = f'{sequence}_{Path(item["name"]).name}'
                archive.write(item['path'], arcname=name)
                manifest.append({**{k: item[k] for k in ('category', 'bytes', 'sha256')}, 'name': name})
            archive.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False))
        if path.stat().st_size > max_archive_bytes:
            path.unlink()
            raise ValueError('Archive exceeds Telegram upload limit')
        # Verify bytes actually stored in the ZIP, not just the source files.
        with zipfile.ZipFile(path) as archive:
            for item in manifest:
                if hashlib.sha256(archive.read(item['name'])).hexdigest() != item['sha256']:
                    raise ValueError('Archived media verification failed')
        paths.append(str(path))
    return paths
