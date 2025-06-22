import argparse
import zipfile
import tempfile
from pathlib import Path
import sys
import os
import logging
from datetime import datetime, timedelta

from core.ssh_copy import RemoteFetcher, SSHConnectionError
from core.progress import ProgressTracker
from core.uploader import SharePointUploader
from core.auth import get_access_token
from core.utils import load_config

# Initialize logger at module level
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sharepoint-uploader.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def compress_directory(source_dir: Path, output_path: Path = None, compression_level: int = 6) -> Path:
    """
    Compress a directory into a ZIP file.
    
    Args:
        source_dir: Directory to compress
        output_path: Output ZIP file path (optional)
        compression_level: Compression level 0-9 (0=no compression, 9=maximum)
    
    Returns:
        Path to the created ZIP file
    """
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = source_dir.parent / f"{source_dir.name}_{timestamp}.zip"
    
    logger.info(f"🗜️  Compressing {source_dir} to {output_path}...")
    
    # Count total files first for ETA
    total_files = sum(1 for _ in source_dir.rglob('*') if _.is_file())
    logger.info(f"📁 Found {total_files} files to compress")
    
    start_time = datetime.now()
    
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=compression_level) as zipf:
        processed_files = 0
        
        for file_path in source_dir.rglob('*'):
            if file_path.is_file():
                try:
                    # Calculate relative path for the archive
                    arcname = file_path.relative_to(source_dir)
                    
                    # Sanitize archive name for Windows compatibility
                    sanitized_arcname = str(arcname).replace('|', '_').replace('<', '_').replace('>', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_')
                    
                    zipf.write(file_path, sanitized_arcname)
                    processed_files += 1
                    
                    # Show progress with ETA
                    if processed_files % 10 == 0 or processed_files == total_files:
                        progress = (processed_files / total_files) * 100
                        
                        # Calculate ETA
                        elapsed = (datetime.now() - start_time).total_seconds()
                        if processed_files > 0 and elapsed > 0:
                            rate = processed_files / elapsed
                            remaining_files = total_files - processed_files
                            eta_seconds = remaining_files / rate if rate > 0 else 0
                            eta_time = datetime.now() + timedelta(seconds=eta_seconds)
                            eta_str = f" • ETA: {eta_time.strftime('%H:%M:%S')}"
                        else:
                            eta_str = ""
                        
                        logger.info(f"   📦 Progress: {processed_files}/{total_files} files ({progress:.1f}%){eta_str}")
                        
                except (OSError, ValueError, FileNotFoundError) as e:
                    # Skip files with problematic names or access issues
                    logger.warning(f"   ⚠️  Skipping problematic file: {file_path.name} - {e}")
                    continue
    
    # Get compression statistics
    original_size = sum(f.stat().st_size for f in source_dir.rglob('*') if f.is_file())
    compressed_size = output_path.stat().st_size
    compression_ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
    
    logger.info(f"✅ Compression complete!")
    logger.info(f"   📁 Original size: {original_size:,} bytes ({original_size/1024/1024:.2f} MB)")
    logger.info(f"   📦 Compressed size: {compressed_size:,} bytes ({compressed_size/1024/1024:.2f} MB)")
    logger.info(f"   💾 Compression ratio: {compression_ratio:.1f}%")
    
    return output_path


def upload_to_sharepoint(file_path: Path, folder_path: str = "", config_path: str = "config.json") -> bool:
    """
    Upload a file to SharePoint using the new authentication and upload system.
    
    Args:
        file_path: Path to file to upload
        folder_path: Optional folder path in SharePoint
        config_path: Path to configuration file
    
    Returns:
        True if upload successful, False otherwise
    """
    try:
        logger.info(f"🚀 Starting SharePoint upload for {file_path.name}...")
        
        # Get access token using the new authentication system
        logger.info("🔐 Authenticating with Microsoft Graph...")
        access_token = get_access_token()
        logger.info("✅ Authentication successful!")
        
        # Initialize uploader with new system
        logger.info("📤 Initializing SharePoint uploader...")
        uploader = SharePointUploader(access_token, config_path)
        logger.info("✅ Uploader initialized!")
        
        # Upload the file
        logger.info(f"📁 Uploading to folder: {'root' if not folder_path else folder_path}")
        logger.info("⏳ Starting upload...")
        
        result = uploader.upload_file(str(file_path), folder_path)
        
        logger.info("🎉 Upload completed successfully!")
        logger.info(f"📋 File details:")
        logger.info(f"   - Name: {result.get('name', 'Unknown')}")
        logger.info(f"   - ID: {result.get('id', 'Unknown')}")
        logger.info(f"   - Size: {result.get('size', 'Unknown')} bytes")
        
        return True
            
    except Exception as e:
        logger.error(f"❌ SharePoint upload error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="SharePoint Uploader CLI with SSH and Compression Support")
    
    # Core arguments
    parser.add_argument("path", nargs="?", help="Local directory or file path to upload (will be compressed if directory)")
    parser.add_argument("--config", help="Path to configuration file", default="config.json")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    
    # SSH arguments
    parser.add_argument("--use-ssh", action="store_true", help="Use SSH for remote transfer")
    parser.add_argument("--remote-path", help="Remote path for SSH download")
    parser.add_argument("--local-path", help="Local path to download to (temporary if uploading)")
    parser.add_argument("--ssh-host", help="SSH host")
    parser.add_argument("--ssh-user", help="SSH username")
    parser.add_argument("--ssh-pass", help="SSH password")
    parser.add_argument("--ssh-key", help="Path to SSH private key")
    parser.add_argument("--ssh-port", type=int, default=22, help="SSH port (default: 22)")
    
    # Compression arguments
    parser.add_argument("--compress", action="store_true", help="Compress downloaded directory before upload")
    parser.add_argument("--compression-level", type=int, choices=range(10), default=6, 
                       help="Compression level 0-9 (0=no compression, 9=maximum, default=6)")
    parser.add_argument("--keep-original", action="store_true", help="Keep original directory after compression")
    
    # Upload arguments
    parser.add_argument("--upload-to-sharepoint", action="store_true", help="Upload to SharePoint after processing")
    parser.add_argument("--upload-only", help="Upload existing file to SharePoint (skip SSH/compression)")
    parser.add_argument("--sharepoint-folder", help="SharePoint folder path for upload", default="")
    
    args = parser.parse_args()

    # Load configuration
    try:
        config = load_config(args.config)
        logger.info(f"📋 Loaded configuration from {args.config}")
    except Exception as e:
        logger.error(f"❌ Error loading configuration: {e}")
        sys.exit(1)

    # Handle direct path upload (new feature)
    if args.path:
        path_to_upload = Path(args.path)
        if not path_to_upload.exists():
            logger.error(f"❌ Path not found: {path_to_upload}")
            sys.exit(1)
        
        file_to_upload = None
        
        if path_to_upload.is_file():
            # Direct file upload
            file_to_upload = path_to_upload
            logger.info(f"📄 Uploading file: {file_to_upload}")
        elif path_to_upload.is_dir():
            # Directory - compress first
            logger.info(f"📁 Compressing directory: {path_to_upload}")
            file_to_upload = compress_directory(path_to_upload, compression_level=args.compression_level)
            logger.info(f"📦 Compressed to: {file_to_upload}")
        
        if file_to_upload:
            success = upload_to_sharepoint(file_to_upload, args.sharepoint_folder, args.config)
            
            # Clean up compressed file if it was a directory
            if path_to_upload.is_dir() and file_to_upload != path_to_upload:
                try:
                    file_to_upload.unlink()
                    logger.info(f"🧹 Cleaned up compressed file: {file_to_upload}")
                except Exception as e:
                    logger.warning(f"⚠️  Could not clean up compressed file: {e}")
            
            sys.exit(0 if success else 1)
        else:
            logger.error(f"❌ Could not process path: {path_to_upload}")
            sys.exit(1)

    # Handle upload-only mode
    if args.upload_only:
        upload_file = Path(args.upload_only)
        if not upload_file.exists():
            logger.error(f"❌ File not found: {upload_file}")
            sys.exit(1)
            
        success = upload_to_sharepoint(upload_file, args.sharepoint_folder, args.config)
        sys.exit(0 if success else 1)

    # SSH transfer workflow
    if args.use_ssh:
        if not all([args.remote_path, args.ssh_host, args.ssh_user]):
            logger.error("❌ Error: --remote-path, --ssh-host, and --ssh-user are required for SSH transfer.")
            sys.exit(1)
        
        # Determine local path
        if args.local_path:
            local_base_path = Path(args.local_path)
        else:
            # Use temporary directory if uploading to SharePoint
            if args.upload_to_sharepoint:
                local_base_path = Path(tempfile.mkdtemp(prefix="sharepoint_ssh_"))
                logger.info(f"📁 Using temporary directory: {local_base_path}")
            else:
                logger.error("❌ Error: --local-path is required when not uploading to SharePoint.")
                sys.exit(1)
        
        local_base_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize progress tracker
        with ProgressTracker() as progress_tracker:
            # Set up SSH connection
            fetcher = RemoteFetcher(
                progress_tracker=progress_tracker,
                hostname=args.ssh_host,
                port=args.ssh_port,
                username=args.ssh_user,
                password=args.ssh_pass,
                private_key_path=args.ssh_key
            )
            
            try:
                logger.info(f"🔗 Connecting to {args.ssh_host}:{args.ssh_port} as {args.ssh_user}...")
                
                with fetcher:
                    logger.info(f"📥 Downloading from {args.remote_path} to {local_base_path}...")
                    fetcher.fetch_directory(args.remote_path, local_base_path)
                    logger.info("✅ SSH download completed successfully!")
                
                # Determine what to process next
                downloaded_dir = local_base_path / Path(args.remote_path).name
                if not downloaded_dir.exists():
                    # If the expected directory doesn't exist, use the base path
                    downloaded_dir = local_base_path
                
                file_to_upload = None
                
                # Compression step
                if args.compress:
                    logger.info("🗜️  Compression requested...")
                    compressed_file = compress_directory(downloaded_dir, compression_level=args.compression_level)
                    file_to_upload = compressed_file
                    
                    # Clean up original directory if not keeping it
                    if not args.keep_original and downloaded_dir != local_base_path:
                        import shutil
                        shutil.rmtree(downloaded_dir)
                        logger.info(f"🧹 Removed original directory: {downloaded_dir}")
                else:
                    # If not compressing, we need to compress anyway for SharePoint upload
                    if args.upload_to_sharepoint:
                        logger.info("🗜️  Compressing for SharePoint upload...")
                        compressed_file = compress_directory(downloaded_dir, compression_level=args.compression_level)
                        file_to_upload = compressed_file
                
                # SharePoint upload step
                if args.upload_to_sharepoint and file_to_upload:
                    success = upload_to_sharepoint(file_to_upload, args.sharepoint_folder, args.config)
                    
                    # Clean up temporary files
                    if not args.local_path:  # Only clean up if using temporary directory
                        import shutil
                        shutil.rmtree(local_base_path)
                        logger.info(f"🧹 Cleaned up temporary directory: {local_base_path}")
                    
                    if not success:
                        sys.exit(1)
                
                logger.info("🎉 All operations completed successfully!")
                
            except SSHConnectionError as e:
                logger.error(f"❌ SSH connection error: {e}")
                sys.exit(1)
            except Exception as e:
                logger.error(f"❌ Unexpected error: {e}")
                sys.exit(1)
    
    else:
        logger.error("❌ No operation specified. Use --use-ssh or --upload-only.")
        logger.info("💡 Use --help for usage information.")
        sys.exit(1)


if __name__ == "__main__":
    main()