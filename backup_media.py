"""
Enhanced Media Backup Tool
Creates, restores, and manages media file backups across devices
"""

import os
import shutil
import json
import zipfile
from pathlib import Path
from datetime import datetime
import sys

class MediaBackupManager:
    def __init__(self):
        self.media_dir = Path('media')
        self.backups_dir = Path('backups')
        self.backups_dir.mkdir(exist_ok=True)
    
    def create_backup(self, description=''):
        """Create a backup of current media files"""
        if not self.media_dir.exists():
            print("❌ No media folder found")
            return None
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'media_backup_{timestamp}'
        backup_zip = self.backups_dir / f'{backup_name}.zip'
        manifest_file = self.backups_dir / f'{backup_name}_manifest.json'
        
        # Create manifest
        manifest = {
            'timestamp': datetime.now().isoformat(),
            'description': description,
            'files': [],
            'total_size': 0
        }
        
        # Create zip file
        with zipfile.ZipFile(backup_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in self.media_dir.rglob('*'):
                if not file_path.is_file():
                    continue
                
                rel_path = file_path.relative_to(self.media_dir)
                zipf.write(file_path, arcname=rel_path)
                
                file_size = file_path.stat().st_size
                manifest['files'].append({
                    'path': str(rel_path),
                    'size': file_size
                })
                manifest['total_size'] += file_size
        
        # Save manifest
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        backup_size_mb = backup_zip.stat().st_size / (1024 * 1024)
        print(f"✅ Backup created: {backup_name}.zip")
        print(f"   Size: {backup_size_mb:.1f} MB")
        print(f"   Files: {len(manifest['files'])}")
        print(f"   Location: {backup_zip}")
        
        return backup_name
    
    def restore_backup(self, backup_name, overwrite=False):
        """Restore media files from a backup"""
        backup_zip = self.backups_dir / f'{backup_name}.zip'
        manifest_file = self.backups_dir / f'{backup_name}_manifest.json'
        
        if not backup_zip.exists():
            print(f"❌ Backup not found: {backup_name}.zip")
            return False
        
        # Check for existing files
        if self.media_dir.exists() and any(self.media_dir.iterdir()) and not overwrite:
            print("⚠️  Media folder already has files!")
            response = input("Overwrite existing files? (y/n): ")
            if response.lower() != 'y':
                print("Restore cancelled")
                return False
        
        # Extract backup
        try:
            self.media_dir.mkdir(exist_ok=True)
            with zipfile.ZipFile(backup_zip, 'r') as zipf:
                zipf.extractall(self.media_dir)
            
            # Load and display manifest
            if manifest_file.exists():
                with open(manifest_file, 'r') as f:
                    manifest = json.load(f)
                
                print(f"✅ Backup restored: {backup_name}")
                print(f"   Created: {manifest['timestamp']}")
                if manifest['description']:
                    print(f"   Description: {manifest['description']}")
                print(f"   Files restored: {len(manifest['files'])}")
                print(f"   Total size: {manifest['total_size'] / (1024*1024):.1f} MB")
            else:
                print(f"✅ Backup restored successfully")
            
            return True
            
        except Exception as e:
            print(f"❌ Error restoring backup: {e}")
            return False
    
    def list_backups(self, verbose=False):
        """List all available backups"""
        backups = list(self.backups_dir.glob('media_backup_*.zip'))
        
        if not backups:
            print("No backups found")
            return
        
        print("\n📦 Available Backups:")
        print("-" * 70)
        
        for backup_zip in sorted(backups, reverse=True):
            backup_name = backup_zip.stem
            manifest_file = self.backups_dir / f'{backup_name}_manifest.json'
            
            size_mb = backup_zip.stat().st_size / (1024 * 1024)
            
            if manifest_file.exists():
                with open(manifest_file, 'r') as f:
                    manifest = json.load(f)
                
                print(f"\n📁 {backup_name}")
                print(f"   Size: {size_mb:.1f} MB")
                print(f"   Files: {len(manifest['files'])}")
                print(f"   Created: {manifest['timestamp']}")
                
                if manifest['description']:
                    print(f"   Note: {manifest['description']}")
                
                if verbose:
                    for file_info in manifest['files'][:5]:
                        print(f"     - {file_info['path']}")
                    if len(manifest['files']) > 5:
                        print(f"     ... and {len(manifest['files']) - 5} more files")
            else:
                print(f"\n📁 {backup_name}")
                print(f"   Size: {size_mb:.1f} MB")
        
        print("\n" + "-" * 70)
    
    def delete_backup(self, backup_name):
        """Delete a specific backup"""
        backup_zip = self.backups_dir / f'{backup_name}.zip'
        manifest_file = self.backups_dir / f'{backup_name}_manifest.json'
        
        if not backup_zip.exists():
            print(f"❌ Backup not found: {backup_name}")
            return False
        
        try:
            backup_zip.unlink()
            if manifest_file.exists():
                manifest_file.unlink()
            print(f"✅ Backup deleted: {backup_name}")
            return True
        except Exception as e:
            print(f"❌ Error deleting backup: {e}")
            return False
    
    def cleanup_old_backups(self, keep=5):
        """Keep only the most recent N backups"""
        backups = sorted(
            self.backups_dir.glob('media_backup_*.zip'),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        if len(backups) <= keep:
            print(f"✅ Only {len(backups)} backups exist (keeping {keep})")
            return
        
        to_delete = backups[keep:]
        print(f"🗑️  Removing {len(to_delete)} old backups...")
        
        for backup_zip in to_delete:
            backup_name = backup_zip.stem
            self.delete_backup(backup_name)
        
        print(f"✅ Cleanup complete! Kept {keep} most recent backups")

def main():
    manager = MediaBackupManager()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python backup_media.py create [description]")
        print("  python backup_media.py restore <backup_name>")
        print("  python backup_media.py list [-v]")
        print("  python backup_media.py delete <backup_name>")
        print("  python backup_media.py cleanup [keep=5]")
        print("\nExample:")
        print("  python backup_media.py create 'Before major changes'")
        print("  python backup_media.py restore media_backup_20241215_143022")
        print("  python backup_media.py list -v")
        return
    
    command = sys.argv[1]
    
    if command == 'create':
        description = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else ''
        manager.create_backup(description)
    
    elif command == 'restore':
        if len(sys.argv) < 3:
            print("❌ Please provide backup name")
            print("Usage: python backup_media.py restore <backup_name>")
            return
        backup_name = sys.argv[2]
        manager.restore_backup(backup_name)
    
    elif command == 'list':
        verbose = '-v' in sys.argv or '--verbose' in sys.argv
        manager.list_backups(verbose)
    
    elif command == 'delete':
        if len(sys.argv) < 3:
            print("❌ Please provide backup name")
            return
        backup_name = sys.argv[2]
        manager.delete_backup(backup_name)
    
    elif command == 'cleanup':
        keep = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        manager.cleanup_old_backups(keep)
    
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == '__main__':
    main()
