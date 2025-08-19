import os
import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create a timestamped database backup and rotate old backups (default keep 7 days)."

    def add_arguments(self, parser):
        parser.add_argument('--output-dir', type=str, default=str(settings.BASE_DIR / 'backups'))
        parser.add_argument('--keep-days', type=int, default=7)

    def handle(self, *args, **options):
        output_dir = Path(options['output_dir'])
        keep_days = int(options['keep_days'])
        output_dir.mkdir(parents=True, exist_ok=True)

        db_cfg = settings.DATABASES['default']
        engine = db_cfg.get('ENGINE', '')

        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        if 'sqlite' in engine:
            db_path = Path(db_cfg.get('NAME'))
            if not db_path.exists():
                self.stderr.write(self.style.ERROR(f'SQLite database file not found: {db_path}'))
                return 1
            dest = output_dir / f'db-sqlite-{timestamp}.sqlite3'
            shutil.copy2(db_path, dest)
            self.stdout.write(self.style.SUCCESS(f'Backup created: {dest}'))
        elif 'postgresql' in engine or 'postgres' in engine:
            dest = output_dir / f'db-postgres-{timestamp}.sql'
            # Use pg_dump from PATH; requires environment variables to be set in DATABASE_URL or settings
            env = os.environ.copy()
            host = db_cfg.get('HOST') or env.get('PGHOST')
            user = db_cfg.get('USER') or env.get('PGUSER')
            password = db_cfg.get('PASSWORD') or env.get('PGPASSWORD')
            port = str(db_cfg.get('PORT') or env.get('PGPORT') or '')
            name = db_cfg.get('NAME')
            if password:
                env['PGPASSWORD'] = password
            cmd = ['pg_dump', '-Fp']
            if host:
                cmd += ['-h', host]
            if port:
                cmd += ['-p', port]
            if user:
                cmd += ['-U', user]
            cmd += ['-f', str(dest), name]
            try:
                subprocess.check_call(cmd, env=env)
                self.stdout.write(self.style.SUCCESS(f'Backup created: {dest}'))
            except FileNotFoundError:
                self.stderr.write(self.style.ERROR('pg_dump not found on PATH. Install PostgreSQL client tools.'))
                return 1
            except subprocess.CalledProcessError as e:
                self.stderr.write(self.style.ERROR(f'pg_dump failed: {e}'))
                return e.returncode
        else:
            self.stderr.write(self.style.ERROR(f'Unsupported database engine: {engine}'))
            return 1

        # Rotation: delete files older than keep_days
        cutoff = datetime.now() - timedelta(days=keep_days)
        removed = 0
        for p in output_dir.glob('db-*'):
            try:
                mtime = datetime.fromtimestamp(p.stat().st_mtime)
                if mtime < cutoff:
                    p.unlink()
                    removed += 1
            except Exception:
                continue
        self.stdout.write(self.style.NOTICE(f'Rotation complete. Removed {removed} old backups.'))
        return 0
