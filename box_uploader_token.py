"""
Box File Uploader using Developer Token Authentication

This module provides functionality to upload files and directories to Box folders
using developer token authentication.

Usage:
    python box_uploader_token.py

Environment Variables:
    BOX_DEVELOPER_TOKEN: Your Box developer token
    BOX_FOLDER_URL: The Box folder URL to upload to
    LOCAL_DIR: Local directory or file to upload
"""

import os
import re
import time
import sys
from box_sdk_gen import BoxClient, BoxDeveloperTokenAuth, UploadFileAttributes


class BoxUploader:
    """Upload files and directories to Box using developer token authentication."""
    
    def __init__(self, developer_token: str, folder_url: str, local_dir: str):
        """
        Initialize the Box uploader.
        
        Args:
            developer_token: Box developer token for authentication
            folder_url: URL of the Box folder to upload to
            local_dir: Local directory or file path to upload
            
        Raises:
            ValueError: If local directory not found or folder ID cannot be extracted
        """
        self.developer_token = developer_token
        self.folder_url = folder_url
        self.local_dir = local_dir
        
        if not os.path.exists(self.local_dir):
            raise ValueError(f"Local path not found: {self.local_dir}")
        
        # Extract and validate folder ID
        self.folder_id = self._extract_folder_id()
        print(f"Detected Box folder ID: {self.folder_id}")
        
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

    def _create_folder(self, name: str, parent_id: str) -> str:
        """
        Create a folder in Box or return existing folder ID.
        
        Args:
            name: Name of the folder to create
            parent_id: Parent folder ID where the folder will be created
            
        Returns:
            str: ID of the created or existing folder
        """
        # Check if folder already exists
        items = self.client.folders.get_folder_items(parent_id, limit=1000).entries
        for item in items:
            if item.type == "folder" and item.name == name:
                print(f"Folder '{name}' already exists (ID: {item.id})")
                return item.id
        
        # Create new folder
        print(f"Creating folder '{name}' in Box...")
        new_folder = self.client.folders.create_folder(name, parent_id)
        return new_folder.id

    def upload_directory(self, local_path: str, parent_id: str):
        """
        Recursively upload a directory and its contents to Box.
        
        Args:
            local_path: Local directory path to upload
            parent_id: Box folder ID where contents will be uploaded
        """
        for entry in os.scandir(local_path):
            if entry.is_file():
                file_name = entry.name
                file_path = entry.path
                print(f"Uploading file: {file_path}...")
                start_time = time.time()
                
                try:
                    with open(file_path, "rb") as file_stream:
                        attributes = UploadFileAttributes(
                            parent={"id": parent_id},
                            name=file_name
                        )
                        self.client.uploads.upload_file(attributes, file_stream)
                    
                    elapsed = time.time() - start_time
                    print(f"✓ Uploaded '{file_name}' (Time: {elapsed:.2f}s)")
                    
                except Exception as e:
                    print(f"✗ Upload failed for {file_name}: {e}")
                    
            elif entry.is_dir():
                # Create subfolder and recursively upload its contents
                subfolder_id = self._create_folder(entry.name, parent_id)
                self.upload_directory(entry.path, subfolder_id)

    def upload_all(self):
        """
        Upload all files from the local directory to Box.
        """
        print(f"Starting upload from {self.local_dir} to Box folder ID {self.folder_id}...")
        
        if os.path.isfile(self.local_dir):
            # Upload single file
            file_name = os.path.basename(self.local_dir)
            print(f"Uploading single file: {file_name}...")
            start_time = time.time()
            
            try:
                with open(self.local_dir, "rb") as file_stream:
                    attributes = UploadFileAttributes(
                        parent={"id": self.folder_id},
                        name=file_name
                    )
                    self.client.uploads.upload_file(attributes, file_stream)
                
                elapsed = time.time() - start_time
                print(f"✓ Uploaded '{file_name}' (Time: {elapsed:.2f}s)")
                
            except Exception as e:
                print(f"✗ Upload failed for {file_name}: {e}")
        else:
            # Upload directory
            self.upload_directory(self.local_dir, self.folder_id)
        
        print("\nUpload complete.")


def main():
    """Main entry point for the script."""
    # Get configuration from environment variables
    developer_token = os.getenv("BOX_DEVELOPER_TOKEN")
    folder_url = os.getenv("BOX_FOLDER_URL")
    local_dir = os.getenv("LOCAL_DIR")
    
    # Validate required environment variables
    if not developer_token:
        print("Error: BOX_DEVELOPER_TOKEN environment variable is required")
        print("Set it with: export BOX_DEVELOPER_TOKEN='your_token_here'")
        sys.exit(1)
    
    if not folder_url:
        print("Error: BOX_FOLDER_URL environment variable is required")
        print("Set it with: export BOX_FOLDER_URL='https://yourcompany.box.com/folder/123456'")
        sys.exit(1)
    
    if not local_dir:
        print("Error: LOCAL_DIR environment variable is required")
        print("Set it with: export LOCAL_DIR='/path/to/local/directory'")
        sys.exit(1)
    
    # Initialize uploader and start upload
    try:
        uploader = BoxUploader(developer_token, folder_url, local_dir)
        uploader.upload_all()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob
