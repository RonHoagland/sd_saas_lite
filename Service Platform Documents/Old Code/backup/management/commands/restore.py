"""
Database restore management command.

Restores from a backup created by the backup command.

Validates backup structure, restores database and files,
and handles rollback on failure.

Usage:
    python manage.py restore <backup_id>
    python manage.py restore <backup_path>
"""

import os
import json
import gzip
import tarfile
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.conf import settings
from django.db import connections
from django.contrib.auth.models import User

from backup.models import Backup, BackupLog


class Command(BaseCommand):
    help = 'Restore database and files from a backup'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'backup_id_or_path',
            type=str,
            help='Backup ID (e.g., backup_20240115_143022) or full path to backup folder',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Validate backup without performing restore',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompt',
        )
    
    def handle(self, *args, **options):
        backup_id_or_path = options['backup_id_or_path']
        backup_folder = self._locate_backup(backup_id_or_path)
        
        if not backup_folder:
            raise CommandError(f"Backup not found: {backup_id_or_path}")
        
        # Validate backup structure
        self.stdout.write('Validating backup structure...')
        metadata = self._validate_backup(backup_folder)
        if not metadata:
            raise CommandError("Backup validation failed")
        
        self.stdout.write(self.style.SUCCESS('✓ Backup validation passed'))
        self._display_backup_info(metadata)
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('\n(DRY RUN - No changes made)'))
            return
        
        # Confirm restore
        if not options['force']:
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠ WARNING: This will overwrite current data with backup data.'
                )
            )
            response = input('Are you sure? Type "yes" to confirm: ')
            if response.lower() != 'yes':
                self.stdout.write('Restore cancelled.')
                return
        
        start_time = timezone.now()
        success = False
        error_message = None
        system_user, _ = User.objects.get_or_create(username='system')
        
        try:
            # Get or create Backup record
            backup = Backup.objects.filter(backup_id=metadata.get('backup_id')).first()
            if not backup:
                backup = Backup.objects.create(
                    backup_id=metadata.get('backup_id'),
                    backup_path=str(backup_folder),
                    status='in_progress',
                    backup_type='restore',
                    app_version=metadata.get('app_version'),
                    created_by=system_user,
                    updated_by=system_user,
                )
            
            self.stdout.write('Restoring database...')
            self._restore_database(backup_folder, metadata)
            
            self.stdout.write('Restoring files...')
            self._restore_files(backup_folder, metadata)
            
            self.stdout.write(self.style.SUCCESS('✓ Restore completed successfully'))
            success = True
            
        except Exception as e:
            error_message = str(e)
            self.stdout.write(self.style.ERROR(f'✗ Restore failed: {error_message}'))
        
        finally:
            # Log operation
            if 'backup' in locals():
                backup.status = 'success' if success else 'failed'
                backup.failure_reason = error_message or ''
                backup.end_time = timezone.now()
                backup.save()
                
                BackupLog.objects.create(
                    backup=backup,
                    operation='restore',
                    status='success' if success else 'error',
                    message=error_message or 'Restore completed',
                    initiated_by='system',
                    duration_seconds=(timezone.now() - start_time).total_seconds(),
                    created_by=system_user,
                    updated_by=system_user,
                )
    
    def _locate_backup(self, backup_id_or_path: str) -> Optional[Path]:
        """
        Locate backup folder by ID or path.
        
        Searches in:
        1. Exact path if provided
        2. Default backup locations from BackupSettings
        3. All known backup paths
        """
        search_path = Path(backup_id_or_path)
        
        # Check if it's a valid path
        if search_path.is_dir():
            if (search_path / 'metadata.json').exists():
                return search_path
        
        # Search by backup ID in default location
        try:
            from backup.models import BackupSettings
            settings_obj = BackupSettings.get_settings()
            backup_root = Path(settings_obj.backup_path)
            
            candidate = backup_root / backup_id_or_path
            if candidate.is_dir() and (candidate / 'metadata.json').exists():
                return candidate
        except Exception:
            pass
        
        # Query database
        try:
            backup = Backup.objects.filter(backup_id=backup_id_or_path).first()
            if backup:
                path = Path(backup.backup_path)
                if path.exists():
                    return path
        except Exception:
            pass
        
        return None
    
    def _validate_backup(self, backup_folder: Path) -> Optional[Dict]:
        """
        Validate backup structure and integrity.
        
        Checks:
        - metadata.json exists and is valid
        - Database dump file exists
        - Files archive exists or is empty
        """
        metadata_file = backup_folder / 'metadata.json'
        if not metadata_file.exists():
            self.stdout.write(self.style.ERROR('Missing metadata.json'))
            return None
        
        try:
            with open(metadata_file) as f:
                metadata = json.load(f)
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR('Invalid metadata.json'))
            return None
        
        # Validate metadata fields
        required_fields = ['backup_id', 'timestamp', 'app_version']
        for field in required_fields:
            if field not in metadata:
                self.stdout.write(self.style.ERROR(f'Missing metadata field: {field}'))
                return None
        
        # Check database file
        db_file = backup_folder / 'database.sql.gz'
        if not db_file.exists():
            db_file = backup_folder / 'database.db.gz'
        
        if not db_file.exists():
            self.stdout.write(self.style.ERROR('Database backup file not found'))
            return None
        
        # Check files archive
        files_archive = backup_folder / 'files.tar.gz'
        if not files_archive.exists():
            self.stdout.write(self.style.WARNING('Files archive not found (will skip file restore)'))
            metadata['files_archive'] = None
        
        return metadata
    
    def _display_backup_info(self, metadata: Dict):
        """Display backup information."""
        self.stdout.write('\nBackup Information:')
        self.stdout.write(f'  ID: {metadata.get("backup_id")}')
        self.stdout.write(f'  Created: {metadata.get("timestamp")}')
        self.stdout.write(f'  App Version: {metadata.get("app_version")}')
        self.stdout.write(f'  Schema Version: {metadata.get("schema_version", "unknown")}')
        self.stdout.write(f'  Database: {metadata.get("database_version", "unknown")}')
        self.stdout.write(f'  Files: {metadata.get("file_count", 0)} files')
    
    def _restore_database(self, backup_folder: Path, metadata: Dict):
        """Restore database from backup."""
        db_config = settings.DATABASES.get('default', {})
        
        # Find database file (could be .sql.gz or .db.gz)
        db_file = backup_folder / 'database.sql.gz'
        if not db_file.exists():
            db_file = backup_folder / 'database.db.gz'
        
        if not db_file.exists():
            raise CommandError("Database backup file not found")
        
        if db_config.get('ENGINE') == 'django.db.backends.postgresql':
            self._restore_postgresql(db_file, db_config)
        
        else:
            raise CommandError(f"Unsupported database backend: {db_config.get('ENGINE')}")
    

    
    def _restore_postgresql(self, db_file: Path, db_config: Dict):
        """Restore PostgreSQL database."""
        db_name = db_config.get('NAME', 'brixacore')
        db_user = db_config.get('USER', 'postgres')
        db_host = db_config.get('HOST', 'localhost')
        db_port = db_config.get('PORT', '5432')
        
        # Decompress to temp file
        temp_sql = db_file.parent / 'database_temp.sql'
        with gzip.open(db_file, 'rb') as f_in:
            with open(temp_sql, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        try:
            # Drop existing database and recreate
            self._drop_postgresql_db(db_name, db_user, db_host, db_port, db_config)
            self._create_postgresql_db(db_name, db_user, db_host, db_port, db_config)
            
            # Restore from dump
            env = {}
            if 'PASSWORD' in db_config:
                env['PGPASSWORD'] = db_config['PASSWORD']
            
            cmd = [
                'psql',
                '-h', db_host,
                '-p', str(db_port),
                '-U', db_user,
                '-d', db_name,
                '-f', str(temp_sql)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env={**os.environ, **env} if env else None,
            )
            
            if result.returncode != 0:
                raise CommandError(f"psql restore failed: {result.stderr}")
            
            self.stdout.write(f'Database restored: {db_name}')
        
        finally:
            if temp_sql.exists():
                temp_sql.unlink()
    
    def _drop_postgresql_db(self, db_name: str, db_user: str, db_host: str, 
                           db_port: str, db_config: Dict):
        """Drop existing PostgreSQL database."""
        try:
            import os
            env = {}
            if 'PASSWORD' in db_config:
                env['PGPASSWORD'] = db_config['PASSWORD']
            
            cmd = [
                'dropdb',
                '-h', db_host,
                '-p', str(db_port),
                '-U', db_user,
                '--if-exists',
                db_name
            ]
            
            subprocess.run(
                cmd,
                capture_output=True,
                env={**os.environ, **env} if env else None,
                check=True,
            )
        except Exception:
            # Database might not exist, that's fine
            pass
    
    def _create_postgresql_db(self, db_name: str, db_user: str, db_host: str,
                             db_port: str, db_config: Dict):
        """Create empty PostgreSQL database."""
        try:
            import os
            env = {}
            if 'PASSWORD' in db_config:
                env['PGPASSWORD'] = db_config['PASSWORD']
            
            cmd = [
                'createdb',
                '-h', db_host,
                '-p', str(db_port),
                '-U', db_user,
                db_name
            ]
            
            subprocess.run(
                cmd,
                capture_output=True,
                env={**os.environ, **env} if env else None,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise CommandError(f"Failed to create database: {e.stderr}")
    
    def _restore_files(self, backup_folder: Path, metadata: Dict):
        """Restore files and documents from archive."""
        files_archive = backup_folder / 'files.tar.gz'
        
        if not files_archive.exists():
            self.stdout.write('No files archive found, skipping file restore')
            return
        
        storage_root = Path(settings.MEDIA_ROOT) if hasattr(settings, 'MEDIA_ROOT') else None
        if not storage_root:
            self.stdout.write(self.style.WARNING('MEDIA_ROOT not configured, skipping file restore'))
            return
        
        # Create backup of current files
        backup_files = storage_root.parent / f'{storage_root.name}_backup'
        if storage_root.exists():
            shutil.rmtree(backup_files, ignore_errors=True)
            shutil.copytree(storage_root, backup_files)
        
        try:
            # Clear existing files
            if storage_root.exists():
                shutil.rmtree(storage_root)
            storage_root.mkdir(parents=True, exist_ok=True)
            
            # Extract archive
            with tarfile.open(files_archive, 'r:gz') as tar:
                tar.extractall(path=storage_root)
            
            self.stdout.write(f'Files restored: {metadata.get("file_count", 0)} files')
            
            # Clean up backup
            if backup_files.exists():
                shutil.rmtree(backup_files)
        
        except Exception as e:
            # Restore from backup
            if backup_files.exists():
                if storage_root.exists():
                    shutil.rmtree(storage_root)
                shutil.move(backup_files, storage_root)
            
            raise CommandError(f"Failed to restore files: {str(e)}")
