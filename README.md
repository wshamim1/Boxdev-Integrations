# Box Integration Scripts

A collection of Python scripts for downloading and uploading files to/from Box using both Developer Token and JWT authentication methods.

## 📁 Files Overview

### Download Scripts
- **`box_downloader_token.py`** - Download files using Developer Token authentication
- **`box_downloader_jwt.py`** - Download files using JWT authentication

### Upload Scripts
- **`box_uploader_token.py`** - Upload files/directories using Developer Token authentication
- **`box_uploader_jwt.py`** - Upload ZIP files using JWT authentication with multiple modes

### Configuration
- **`.env.example`** - Template for environment variables
- **`config/box_config.json`** - JWT configuration file (not included, must be generated)

## 🚀 Setup

### 1. Install Dependencies

**Option 1: Install from requirements.txt (Recommended)**
```bash
pip install -r requirements.txt
```

**Option 2: Install manually**
```bash
pip install box-sdk-gen PyJWT python-dotenv
```

**Required packages:**
- `box-sdk-gen` - Official Box SDK for Python
- `PyJWT` - Required for JWT authentication
- `python-dotenv` - Optional, for better environment variable management

### 2. Configure Environment Variables

Copy the example environment file and fill in your values:

```bash
cp .env.example .env
```

Edit `.env` with your actual credentials:

```bash
# For token-based authentication
export BOX_DEVELOPER_TOKEN="your_token_here"

# For JWT-based authentication
export BOX_CONFIG_PATH="/path/to/box_config.json"

# Common settings
export BOX_FOLDER_URL="https://yourcompany.box.com/folder/123456789"
export DOWNLOAD_DIR="/path/to/download"
export LOCAL_DIR="/path/to/upload"
```

Load the environment variables:

```bash
source .env
```

### 3. Get Box Credentials

#### Developer Token (Quick Start)
1. Go to [Box Developer Console](https://app.box.com/developers/console)
2. Select your app or create a new one
3. Go to Configuration tab
4. Generate Developer Token (expires in 60 minutes)

#### JWT Authentication (Production)
1. Go to [Box Developer Console](https://app.box.com/developers/console)
2. Select your app or create a new one
3. Go to Configuration tab
4. Under "Add and Manage Public Keys", click "Generate a Public/Private Keypair"
5. Download the JSON configuration file
6. Save it securely (e.g., `config/box_config.json`)

## 📖 Usage Examples

### Download Files (Token-based)

**Basic Usage:**
```bash
# Set environment variables
export BOX_DEVELOPER_TOKEN="your_token"
export BOX_FOLDER_URL="https://yourcompany.box.com/folder/123456"
export DOWNLOAD_DIR="/path/to/download"

# Run the script
python box_downloader_token.py
```

**Example Output:**
```
Detected folder ID: 123456
Fetching items from folder ID 123456...
Found 5 items.
Downloading project_data.zip...
✓ Saved to /path/to/download/project_data.zip (Time: 2.34s)
Downloading analysis.isx...
✓ Saved to /path/to/download/analysis.isx (Time: 1.12s)

Download complete: 2 file(s) with extensions .zip, .isx
```

**Custom File Extensions:**
To download different file types, modify the `download_files()` call in the script:
```python
# Download only PDF files
downloader.download_files(extensions=(".pdf",))

# Download multiple types
downloader.download_files(extensions=(".pdf", ".docx", ".xlsx"))
```

### Download Files (JWT-based)

**Method 1: Using Environment Variables**
```bash
# Set environment variables
export BOX_CONFIG_PATH="./config/box_config.json"
export BOX_FOLDER_URL="https://ibm.ent.box.com/folder/347177397554"
export DOWNLOAD_DIR="./downloads"

# Run the script
python box_downloader_jwt.py
```

**Method 2: Direct Command (Recommended)**
```bash
# Download files directly without setting environment variables
python box_downloader_jwt.py

# Then enter values when prompted:
# BOX_CONFIG_PATH: ./config/box_config.json
# BOX_FOLDER_URL: https://ibm.ent.box.com/folder/347177397554
# DOWNLOAD_DIR: ./downloads
```

**Example Output:**
```
Detected folder ID: 347177397554
Fetching items from folder ID 347177397554...
Found 3 items.
Downloading dataset_2024.zip...
✓ Saved to ./downloads/dataset_2024.zip (Time: 5.67s)
Downloading report.isx...
✓ Saved to ./downloads/report.isx (Time: 0.89s)

Download complete: 2 file(s) with extensions .zip, .isx
```

**Advanced: Using Python API**
```python
from box_downloader_jwt import BoxDownloader

# Initialize downloader
downloader = BoxDownloader(
    config_path="./config/box_config.json",
    folder_url="https://yourcompany.box.com/folder/123456",
    download_dir="./downloads"
)

# Download specific file types
downloader.download_files(extensions=(".pdf", ".docx"))
```

### Upload Files (Token-based)

```bash
# Set environment variables
export BOX_DEVELOPER_TOKEN="your_token"
export BOX_FOLDER_URL="https://yourcompany.box.com/folder/123456"
export LOCAL_DIR="/path/to/upload"

# Run the script
python box_uploader_token.py
```

### Upload ZIP Files (JWT-based)

The JWT uploader supports three modes:

```bash
# Upload only new files (skip existing)
python box_uploader_jwt.py \
  -c /path/to/box_config.json \
  -u https://yourcompany.box.com/folder/123456 \
  -d /path/to/files \
  --mode upload

# Overwrite existing files (delete and re-upload)
python box_uploader_jwt.py \
  -c /path/to/box_config.json \
  -u https://yourcompany.box.com/folder/123456 \
  -d /path/to/files \
  --mode overwrite

# Update existing files (create new versions)
python box_uploader_jwt.py \
  -c /path/to/box_config.json \
  -u https://yourcompany.box.com/folder/123456 \
  -d /path/to/files \
  --mode update
```

## 🔒 Security Best Practices

1. **Never commit credentials** to version control
2. Add `.env` and `config/*.json` to `.gitignore`
3. Use JWT authentication for production environments
4. Rotate developer tokens regularly (they expire in 60 minutes)
5. Store JWT configuration files securely with restricted permissions

```bash
# Secure your JWT config file
chmod 600 config/box_config.json
```

## 📝 Features

### Downloaders
- ✅ Extract folder ID from Box URLs automatically
- ✅ Filter files by extension (.zip, .isx by default)
- ✅ Progress tracking with download times
- ✅ Error handling for failed downloads

### Uploaders
- ✅ Upload single files or entire directories
- ✅ Recursive directory upload (token-based)
- ✅ Three upload modes: upload, overwrite, update (JWT-based)
- ✅ Automatic folder creation
- ✅ Progress tracking with upload times
- ✅ Error handling for failed uploads

## 🐛 Troubleshooting

### Import Error: box_sdk_gen not found
```bash
pip install box-sdk-gen
```

### Authentication Failed
- **Developer Token**: Check if token has expired (60-minute lifetime)
- **JWT**: Verify the config file path and ensure the app has proper permissions

### Folder ID Not Found
- Ensure the Box folder URL is in the correct format: `https://yourcompany.box.com/folder/123456789`

### Permission Denied
- Verify your Box app has the necessary scopes enabled
- For JWT: Ensure the service account has access to the folder

## 📄 License

This project is provided as-is for integration with Box services.

## 🤝 Contributing

Feel free to submit issues and enhancement requests!