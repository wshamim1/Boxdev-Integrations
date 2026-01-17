"""
Box File Downloader using Developer Token Authentication

This module provides functionality to download files from Box folders
using developer token authentication.

Usage:
    python box_downloader_token.py

Environment Variables:
    BOX_DEVELOPER_TOKEN: Your Box developer token
    BOX_FOLDER_URL: The Box folder URL to download from
    DOWNLOAD_DIR: Local directory to save downloaded files
"""

from box_sdk_gen import BoxClient, BoxDeveloperTokenAuth
import os
import re
import time
import sys


class BoxDownloader:
    """Download files from Box using developer token authentication."""
    
    def __init__(self, developer_token: str, folder_url: str, download_dir: str):
        """
        Initialize the Box downloader.
        
        Args:
            developer_token: Box developer token for authentication
            folder_url: URL of the Box folder to download from
            download_dir: Local directory path to save downloaded files
            
        Raises:
            ValueError: If folder ID cannot be extracted from URL
        """
        self.developer_token = developer_token
        self.folder_url = folder_url
        self.download_dir = download_dir
        
        # Create download directory if it doesn't exist
        os.makedirs(self.download_dir, exist_ok=True)
        
        # Extract and validate folder ID
        self.folder_id = self._extract_folder_id()
        print(f"Detected folder ID: {self.folder_id}")
        
        # Initialize Box client with authentication
        self.auth = BoxDeveloperTokenAuth(self.developer_token)
        self.client = BoxClient(self.auth)

    def _extract_folder_id(self) -> str:
        """
        Extract numeric folder ID from Box folder URL.
        
        Returns:
            str: The extracted folder ID
            
        Raises:
            ValueError: If folder ID cannot be extracted from URL
        """
        match = re.search(r"/folder/(\d+)", self.folder_url)
        if not match:
            raise ValueError(f"Could not extract folder ID from URL: {self.folder_url}")
        return match.group(1)

    def list_folder_items(self):
        """
        List all items in the Box folder.
        
        Returns:
            list: List of Box folder items
        """
        print(f"Fetching items from folder ID {self.folder_id}...")
        items = self.client.folders.get_folder_items(self.folder_id, limit=1000).entries
        print(f"Found {len(items)} items.")
        return items

    def download_files(self, extensions=(".zip", ".isx")):
        """
        Download files matching the specified extensions.
        
        Args:
            extensions: Tuple of file extensions to download (default: .zip, .isx)
        """
        items = self.list_folder_items()
        downloaded_count = 0
        
        for item in items:
            if item.type == "file" and item.name.lower().endswith(extensions):
                print(f"Downloading {item.name}...")
                start_time = time.time()
                
                try:
                    download_stream = self.client.downloads.download_file(item.id)
                    download_path = os.path.join(self.download_dir, item.name)
                    
                    with open(download_path, "wb") as out_file:
                        out_file.write(download_stream.read())
                    
                    elapsed = time.time() - start_time
                    print(f"✓ Saved to {download_path} (Time: {elapsed:.2f}s)")
                    downloaded_count += 1
                    
                except Exception as e:
                    print(f"✗ Failed to download {item.name}: {e}")
        
        print(f"\nDownload complete: {downloaded_count} file(s) with extensions {', '.join(extensions)}")


def main():
    """Main entry point for the script."""
    # Get configuration from environment variables
    developer_token = os.getenv("BOX_DEVELOPER_TOKEN")
    folder_url = os.getenv("BOX_FOLDER_URL")
    download_dir = os.getenv("DOWNLOAD_DIR")
    
    # Validate required environment variables
    if not developer_token:
        print("Error: BOX_DEVELOPER_TOKEN environment variable is required")
        print("Set it with: export BOX_DEVELOPER_TOKEN='your_token_here'")
        sys.exit(1)
    
    if not folder_url:
        print("Error: BOX_FOLDER_URL environment variable is required")
        print("Set it with: export BOX_FOLDER_URL='https://yourcompany.box.com/folder/123456'")
        sys.exit(1)
    
    if not download_dir:
        print("Error: DOWNLOAD_DIR environment variable is required")
        print("Set it with: export DOWNLOAD_DIR='/path/to/download/directory'")
        sys.exit(1)
    
    # Initialize downloader and start download
    try:
        downloader = BoxDownloader(developer_token, folder_url, download_dir)
        downloader.download_files()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob
