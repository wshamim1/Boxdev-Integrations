"""
Box File Uploader using JWT Authentication

This module provides functionality to upload ZIP files to Box folders
using JWT (JSON Web Token) authentication with a configuration file.

Supports three upload modes:
- upload: Only upload new files (skip existing)
- overwrite: Delete existing files and upload new versions
- update: Create new versions of existing files

Usage:
    python box_uploader_jwt.py -c config.json -u https://box.com/folder/123 -d /path/to/files --mode overwrite

Arguments:
    -c, --config: Path to Box JWT configuration JSON file
    -u, --url: Box folder URL to upload to
    -d, --local-path: Local ZIP file or directory containing ZIP files
    --mode: Upload mode (upload, overwrite, update) - default: overwrite
"""

import os
import re
import json
import argparse
import sys
from pathlib import Path
from box_sdk_gen import (
    BoxClient,
    BoxJWTAuth,
    JWTConfig,
    UploadFileAttributes
)


class BoxUploader:
    """Upload ZIP files to Box using JWT authentication."""

    def __init__(self, config_path: str, folder_url: str, local_path: str, mode: str):
        """
        Initialize the Box uploader with JWT configuration.
        
        Args:
            config_path: Path to the JSON file containing Box JWT configuration
            folder_url: URL of the Box folder to upload to
            local_path: Local ZIP file or directory containing ZIP files
            mode: Upload mode - 'upload', 'overwrite', or 'update'
            
        Raises:
            ValueError: If config file not found, local path not found, or invalid URL
        """
        self.config_path = os.path.abspath(config_path)
        self.local_path = os.path.abspath(local_path)
        self.folder_url = folder_url
        self.mode = mode

        # Validate configuration file
        if not os.path.isfile(self.config_path):
            raise ValueError(f"JWT config not found: {self.config_path}")

        # Validate local path
        if not os.path.exists(self.local_path):
            raise ValueError(f"Local path not found: {self.local_path}")

        # Determine if uploading a single ZIP file or directory
        self.is_zip_file = os.path.isfile(self.local_path) and self.local_path.endswith(".zip")
        self.is_directory = os.path.isdir(self.local_path)

        # Extract folder ID from URL
        match = re.search(r"/folder/(\d+)", folder_url)
        if not match:
            raise ValueError("Invalid Box folder URL")
        self.folder_id = match.group(1)

        # Load JWT configuration
        with open(self.config_path, "r") as f:
            cfg = json.load(f)

        app = cfg["boxAppSettings"]
        auth = app["appAuth"]

        jwt_cfg = JWTConfig(
            client_id=app["clientID"],
            client_secret=app["clientSecret"],
            enterprise_id=cfg.get("enterpriseID"),
            jwt_key_id=auth["publicKeyID"],
            private_key=auth["privateKey"],
            private_key_passphrase=auth["passphrase"]
        )

        # Initialize Box client
        self.client = BoxClient(BoxJWTAuth(jwt_cfg))

    def find_file(self, fname: str):
        """
        Check if a file exists in the Box folder.
        
        Args:
            fname: Name of the file to search for
            
        Returns:
            tuple: (exists: bool, file_id: str or None)
        """
        try:
            items = self.client.folders.get_folder_items(self.folder_id, limit=1000).entries
            for it in items:
                if it.type == "file" and it.name == fname:
                    return True, it.id
        except Exception as e:
            print(f"Error listing folder: {e}")
        return False, None

    def delete_box_file(self, file_id: str):
        """
        Delete an existing Box file.
        
        Args:
            file_id: ID of the file to delete
            
        Raises:
            Exception: If deletion fails
        """
        try:
            self.client.files.delete_file_by_id(file_id)
            print(f"✓ Deleted existing file ID {file_id}")
        except Exception as e:
            print(f"✗ Failed to delete file ID {file_id}: {e}")
            raise

    def upload_zip(self, zip_path: str):
        """
        Upload a ZIP file to Box based on the selected mode.
        
        Args:
            zip_path: Path to the ZIP file to upload
        """
        fname = os.path.basename(zip_path)
        exists, file_id = self.find_file(fname)

        # OVERWRITE mode: delete existing file then upload
        if self.mode == "overwrite" and exists:
            print(f"↻ Overwriting existing file: {fname}")
            self.client.files.delete_file_by_id(file_id)
            exists = False

        # UPDATE mode: create new version of existing file
        if self.mode == "update" and exists:
            print(f"↻ Updating existing version: {fname}")
            try:
                with open(zip_path, "rb") as f:
                    attrs = UploadFileAttributes(name=fname)
                    result = self.client.files.upload_file_version(
                        file_id=file_id,
                        attributes=attrs,
                        file=f
                    )
                uploaded = result.entries[0]
                print(f"✓ Updated file (ID: {uploaded.id})")
                return
            except Exception as e:
                print(f"✗ Failed to update {fname}: {e}")
                return

        # UPLOAD mode: skip if file exists
        if self.mode == "upload" and exists:
            print(f"⊘ Skipping existing file: {fname}")
            return

        # Upload new file
        print(f"↑ Uploading new file: {fname}")
        try:
            with open(zip_path, "rb") as f:
                attrs = UploadFileAttributes(parent={"id": self.folder_id}, name=fname)
                result = self.client.uploads.upload_file(attrs, f)

            uploaded = result.entries[0]
            print(f"✓ Uploaded file: {fname} (ID: {uploaded.id})")
        except Exception as e:
            print(f"✗ Failed to upload {fname}: {e}")

    def upload_all(self):
        """
        Upload all ZIP files based on the local path (single file or directory).
        """
        print("\n=== Starting ZIP Upload ===")
        print(f"Mode: {self.mode}")
        print("===========================\n")

        if self.is_zip_file:
            # Upload single ZIP file
            self.upload_zip(self.local_path)

        elif self.is_directory:
            # Upload all ZIP files in directory
            zips = list(Path(self.local_path).glob("*.zip"))
            if not zips:
                print("⚠ No ZIP files found in directory")
                return
            
            print(f"Found {len(zips)} ZIP file(s) to upload\n")
            for z in zips:
                self.upload_zip(str(z))

        print("\n=== Upload Complete ===")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Upload ZIP files to Box using JWT authentication",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload with overwrite mode (default)
  python box_uploader_jwt.py -c config.json -u https://box.com/folder/123 -d /path/to/files

  # Upload only new files
  python box_uploader_jwt.py -c config.json -u https://box.com/folder/123 -d file.zip --mode upload

  # Update existing files with new versions
  python box_uploader_jwt.py -c config.json -u https://box.com/folder/123 -d /path/to/files --mode update
        """
    )

    parser.add_argument(
        "-c", "--config",
        required=True,
        help="Path to Box JWT configuration JSON file"
    )
    parser.add_argument(
        "-u", "--url",
        required=True,
        help="Box folder URL to upload to"
    )
    parser.add_argument(
        "-d", "--local-path",
        required=True,
        help="Local ZIP file or directory containing ZIP files"
    )
    parser.add_argument(
        "--mode",
        choices=["upload", "overwrite", "update"],
        default="overwrite",
        help="Upload mode: upload=only new files, overwrite=delete then upload, update=new version (default: overwrite)"
    )

    args = parser.parse_args()

    # Initialize uploader and start upload
    try:
        uploader = BoxUploader(args.config, args.url, args.local_path, args.mode)
        uploader.upload_all()
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob
