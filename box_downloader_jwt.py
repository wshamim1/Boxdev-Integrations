"""
Box File Downloader using JWT Authentication

This module provides functionality to download files from Box folders
using JWT (JSON Web Token) authentication with a configuration file.

Usage:
    python box_downloader_jwt.py

Environment Variables:
    BOX_CONFIG_PATH: Path to Box JWT configuration JSON file
    BOX_FOLDER_URL: The Box folder URL to download from
    DOWNLOAD_DIR: Local directory to save downloaded files
"""

import os
import re
import datetime
import json
import sys
from box_sdk_gen import BoxClient, BoxJWTAuth, JWTConfig


class BoxDownloader:
    """Download files from Box using JWT authentication."""
    
    def __init__(self, config_path: str, folder_url: str, download_dir: str):
        """
        Initialize the BoxDownloader with JWT configuration.

        Args:
            config_path: Path to the JSON file containing Box JWT configuration
            folder_url: The URL of the Box folder to download files from
            download_dir: Local directory where files will be saved
            
        Raises:
            ValueError: If config file not found or folder ID cannot be extracted
            FileNotFoundError: If config file doesn't exist
        """
        self.config_path = config_path
        self.folder_url = folder_url
        self.download_dir = download_dir
        
        # Ensure the download directory exists
        os.makedirs(self.download_dir, exist_ok=True)

        # Extract folder ID from the folder URL
        self.folder_id = self._extract_folder_id()
        print(f"Detected folder ID: {self.folder_id}")

        # Load JWT configuration from the JSON file
        if not os.path.isfile(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, "r") as f:
            cfg = json.load(f)

        # Extract application settings from the configuration
        app_settings = cfg["boxAppSettings"]
        app_auth = app_settings["appAuth"]

        # Initialize JWT configuration
        jwt_config = JWTConfig(
            client_id=app_settings["clientID"],
            client_secret=app_settings["clientSecret"],
            enterprise_id=cfg.get("enterpriseID"),
            jwt_key_id=app_auth["publicKeyID"],
            private_key=app_auth["privateKey"],
            private_key_passphrase=app_auth["passphrase"],
        )

        # Create JWT authentication object and Box client
        self.auth = BoxJWTAuth(jwt_config)
        self.client = BoxClient(self.auth)

    def _extract_folder_id(self) -> str:
        """
        Extract the folder ID from the provided folder URL using regex.

        Returns:
            str: Folder ID extracted from URL
            
        Raises:
            ValueError: If the folder ID cannot be extracted from the URL
        """
        match = re.search(r"/folder/(\d+)", self.folder_url)
        if not match:
            raise ValueError(f"Could not extract folder ID from URL: {self.folder_url}")
        return match.group(1)

    def list_folder_items(self):
        """
        Fetch and return a list of items (files and folders) from the specified folder.

        Returns:
            list: List of Box folder items
        """
        print(f"Fetching items from folder ID {self.folder_id}...")
        items = self.client.folders.get_folder_items(self.folder_id, limit=1000).entries
        print(f"Found {len(items)} items.")
        return items

    def download_files(self, extensions=(".zip", ".isx")):
        """
        Download files with specified extensions from the folder.

        Args:
            extensions: Tuple of file extensions to download (default: .zip, .isx)
        """
        items = self.list_folder_items()
        downloaded_count = 0
        
        for item in items:
            if item.type == "file" and item.name.lower().endswith(extensions):
                print(f"Downloading {item.name}...")
                start_time = datetime.datetime.now()
                
                try:
                    download_stream = self.client.downloads.download_file(item.id)
                    download_path = os.path.join(self.download_dir, item.name)
                    
                    with open(download_path, "wb") as out_file:
                        out_file.write(download_stream.read())
                    
                    elapsed = (datetime.datetime.now() - start_time).total_seconds()
                    print(f"✓ Saved to {download_path} (Time: {elapsed:.2f}s)")
                    downloaded_count += 1
                    
                except Exception as e:
                    print(f"✗ Failed to download {item.name}: {e}")
        
        print(f"\nDownload complete: {downloaded_count} file(s) with extensions {', '.join(extensions)}")


def main():
    """Main entry point for the script."""
    # Get configuration from environment variables
    config_path = os.getenv("BOX_CONFIG_PATH")
    folder_url = os.getenv("BOX_FOLDER_URL")
    download_dir = os.getenv("DOWNLOAD_DIR")
    
    # Validate required environment variables
    if not config_path:
        print("Error: BOX_CONFIG_PATH environment variable is required")
        print("Set it with: export BOX_CONFIG_PATH='/path/to/config.json'")
        sys.exit(1)
    
    if not folder_url:
        print("Error: BOX_FOLDER_URL environment variable is required")
        print("Set it with: export BOX_FOLDER_URL='https://yourcompany.box.com/folder/123456'")
        sys.exit(1)
    
    if not download_dir:
        print("Error: DOWNLOAD_DIR environment variable is required")
        print("Set it with: export DOWNLOAD_DIR='/path/to/download/directory'")
        sys.exit(1)
    
    # Initialize the downloader and start the download process
    try:
        downloader = BoxDownloader(config_path, folder_url, download_dir)
        downloader.download_files()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob
