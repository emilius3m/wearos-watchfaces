"""Upload built Watch Face .aab bundles to Google Play via androidpublisher v3."""

import argparse
import json
import os
import sys
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

TOOLS_DIR = Path(__file__).resolve().parent
PLAY_RELEASE_DIR = TOOLS_DIR.parent
DEFAULT_KEY_PATH = PLAY_RELEASE_DIR / 'play-service-account.json'
SCOPES = ['https://www.googleapis.com/auth/androidpublisher']

sys.path.insert(0, str(TOOLS_DIR))
from build_play_releases import FACES  # noqa: E402


def resolve_key_path(cli_key: str | None) -> Path:
    """Resolve and validate the service account JSON key path."""
    raw = cli_key or os.environ.get('PLAY_SERVICE_ACCOUNT_JSON') or str(DEFAULT_KEY_PATH)
    path = Path(raw).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(
            f'Service account JSON key not found: {path}\n'
            'Pass --key PATH, set PLAY_SERVICE_ACCOUNT_JSON, or save the key as:\n'
            f'  {DEFAULT_KEY_PATH}'
        )
    return path


def create_publisher(key_path: Path):
    """Build an authenticated Google Play Developer API v3 client."""
    creds = service_account.Credentials.from_service_account_file(str(key_path), scopes=SCOPES)
    return build('androidpublisher', 'v3', credentials=creds, cache_discovery=False), creds.service_account_email


def list_app_tracks(service, package_name: str) -> list[str]:
    """Return available track identifiers for package_name without committing an edit."""
    edit = service.edits().insert(body={}, packageName=package_name).execute()
    edit_id = edit['id']
    try:
        resp = service.edits().tracks().list(packageName=package_name, editId=edit_id).execute()
        return [t['track'] for t in resp.get('tracks', [])]
    finally:
        service.edits().delete(packageName=package_name, editId=edit_id).execute()


def commit_edit(service, package_name: str, edit_id: str, changes_not_sent: bool) -> dict:
    """Commit an edit, falling back cleanly if changesNotSentForReview is disallowed."""
    kwargs = {'packageName': package_name, 'editId': edit_id}
    if changes_not_sent:
        kwargs['changesNotSentForReview'] = True
    try:
        return service.edits().commit(**kwargs).execute()
    except HttpError as exc:
        if changes_not_sent and 'changesNotSentForReview' in str(exc):
            kwargs.pop('changesNotSentForReview', None)
            return service.edits().commit(**kwargs).execute()
        raise


def upload_face(service, spec: dict, track: str, status: str, changes_not_sent: bool) -> dict:
    """Upload one watch face .aab to a track and commit the edit."""
    package_name = spec['package']
    aab_path = PLAY_RELEASE_DIR / f"{package_name}.aab"
    if not aab_path.is_file():
        raise FileNotFoundError(f'Built bundle missing: {aab_path}')

    edit = service.edits().insert(body={}, packageName=package_name).execute()
    edit_id = edit['id']
    try:
        media = MediaFileUpload(str(aab_path), mimetype='application/octet-stream', resumable=True)
        bundle = service.edits().bundles().upload(
            packageName=package_name,
            editId=edit_id,
            media_body=media,
        ).execute()
        version_code = bundle['versionCode']
        release_body = {
            'track': track,
            'releases': [
                {
                    'name': f"{spec['version_name']} ({version_code})",
                    'versionCodes': [str(version_code)],
                    'status': status,
                }
            ],
        }
        service.edits().tracks().update(
            packageName=package_name,
            editId=edit_id,
            track=track,
            body=release_body,
        ).execute()
        commit_edit(service, package_name, edit_id, changes_not_sent)
        return {'package': package_name, 'versionCode': version_code, 'track': track, 'status': status}
    except Exception:
        try:
            service.edits().delete(packageName=package_name, editId=edit_id).execute()
        except Exception:
            pass
        raise


def parse_args() -> argparse.Namespace:
    """Parse CLI options."""
    parser = argparse.ArgumentParser(description='Upload Watch Face AABs to Google Play via androidpublisher v3.')
    parser.add_argument('--key', help='Path to Google Cloud service account JSON key.')
    parser.add_argument('--apps', nargs='+', choices=[f['slug'] for f in FACES],
                        help='Watch face slugs to process (default: all 4).')
    parser.add_argument('--track', default='wear:Alpha',
                        help='Target Play track (default: wear:Alpha).')
    parser.add_argument('--status', default='completed',
                        choices=['completed', 'draft', 'inProgress', 'halted'],
                        help='Release status on track (default: completed).')
    parser.add_argument('--list-tracks', action='store_true',
                        help='Inspect available tracks for each app without uploading.')
    parser.add_argument('--changes-not-sent-for-review', action='store_true',
                        help='Stage changes without immediately submitting for review when supported.')
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    key_path = resolve_key_path(args.key)
    service, sa_email = create_publisher(key_path)
    selected = [f for f in FACES if not args.apps or f['slug'] in args.apps]
    print(f'Authenticated as: {sa_email}')

    for spec in selected:
        pkg = spec['package']
        if args.list_tracks:
            tracks = list_app_tracks(service, pkg)
            print(f'[TRACKS] {pkg}: {tracks}')
            continue
        try:
            res = upload_face(service, spec, args.track, args.status, args.changes_not_sent_for_review)
            print(f"[OK] {res['package']} -> track={res['track']} versionCode={res['versionCode']} status={res['status']}")
        except HttpError as exc:
            detail = exc.content.decode('utf-8', errors='replace') if getattr(exc, 'content', None) else str(exc)
            try:
                detail = json.dumps(json.loads(detail), indent=2)
            except Exception:
                pass
            print(f'[ERROR] {pkg}: {detail}', file=sys.stderr)
            return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
