# massunpacker

Mass unpack utility for extracting multiple zip archives into a single directory with intelligent collision handling.

## Features

- **Batch extraction** - Process multiple zip archives with a single command
- **Smart collision detection** - Choose between size-only, fast hash, or SHA256 comparison
- **Automatic renaming** - Conflicting files are renamed (file.jpg -> file-1.jpg)
- **Encoding support** - Handles various filename encodings including Cyrillic
- **Progress tracking** - Visual progress bar with statistics
- **Natural sorting** - Correctly handles numbered files (f1, f2, f10, f11)
- **Disk space check** - Verifies available space before extraction
- **Archive management** - Automatically moves processed archives to OK/ERR folders
- **Rich output** - Colored console output with detailed summaries

## Installation

Using uv (recommended):

```bash
git clone <repository-url>
cd massunpacker
uv sync
```

## Usage

### Basic usage

Extract all zip files from a directory:

```bash
# With quoted pattern (prevents shell expansion)
massunpacker "path/to/archives/*.zip"

# Without quotes (shell expands *.zip to file list)
massunpacker *.zip

# Explicit file list
massunpacker file1.zip file2.zip file3.zip
```

### Advanced options

```bash
massunpacker "data/folder_*/file_*.zip" \
  --extract-to=output \
  --count=10 \
  --collision=hash-fast \
  --mv-ok=processed \
  --mv-er=failed

# Or with expanded glob pattern
massunpacker *.zip --count=5 --extract-to=output
```

### Command-line options

- `PATTERNS` - One or more glob patterns or zip file paths (required)
- `--extract-to, -o` - Output directory (default: current directory)
- `--count, -n` - Limit number of archives to process
- `--mv-ok` - Move successful archives here (default: ./OK)
- `--mv-er` - Move failed archives here (default: ./ERR)
- `--collision, -c` - Collision detection method:
  - `size` - Compare file sizes only (fastest)
  - `hash-fast` - Compare size + fast hash (default, recommended)
  - `hash-sha256` - Compare size + SHA256 hash (most reliable)
- `--no-progress` - Disable progress bar
- `--verbose, -v` - Enable verbose logging

## How it works

1. **Find archives** - Locates all zip files matching the pattern
2. **Natural sort** - Sorts files correctly (f1, f2, f10 not f1, f10, f2)
3. **Check space** - Verifies sufficient disk space is available
4. **Extract files** - Processes each archive:
   - Decodes filenames (handles various encodings)
   - Checks for path traversal attacks
   - Detects collisions with existing files
   - Identical files are skipped
   - Different files with same name are renamed
5. **Move archives** - Moves processed archives to OK or ERR folders
6. **Summary** - Displays detailed statistics

## Collision handling

When files with the same name are found in different archives:

- **Identical files** (same size and hash) are skipped
- **Different files** are renamed with numeric suffixes:
  - `photo.jpg` (from archive1)
  - `photo-1.jpg` (from archive2)
  - `photo-2.jpg` (from archive3)

## Examples

### Extract from multiple sources

```bash
# Extract from all numbered folders
massunpacker "downloads/batch_*/archive_*.zip" --extract-to=merged
```

### Limit processing

```bash
# Process only first 5 archives
massunpacker "*.zip" --count=5
```

### Custom collision detection

```bash
# Use SHA256 for maximum reliability
massunpacker "*.zip" --collision=hash-sha256

# Use size-only for speed (less reliable)
massunpacker "*.zip" --collision=size
```

## Output

The utility provides:

- **stdout** - Extraction summaries and statistics
- **stderr** - Warnings about collisions and errors
- **Progress bar** - Real-time progress (can be disabled)

Example output:

```
Found 3 archive(s) to process
[1/3] Processing archive1.zip...
archive1.zip: 150 extracted, 0 skipped, 0 renamed | 5120 KB -> 8192 KB (37.5% compression)
[2/3] Processing archive2.zip...
archive2.zip: 120 extracted, 30 skipped, 5 renamed | 4096 KB -> 6144 KB (33.3% compression)
Collision in archive2.zip: photo.jpg -> photo-1.jpg
...
Processing complete!
Total: 270 extracted, 30 skipped, 5 renamed, 0 errors
```

## Requirements

- Python 3.10+
- Dependencies (installed automatically with uv):
  - typer - CLI framework
  - rich - Terminal formatting and progress
  - xxhash - Fast hashing
  - natsort - Natural sorting

## License

TBD

## Contributing

Contributions are welcome! This is an open-source project intended for mass extraction of archives from cloud storage services like Google Drive.

## Use cases

- Extracting multiple archive batches from cloud storage downloads
- Merging content from multiple similar archives
- Batch processing of numbered archives
- Consolidating fragmented backups

## Development

Run tests:

```bash
uv run pytest
```

Install in development mode:

```bash
uv sync --dev
```

## Roadmap

- [ ] Add support for other archive formats (tar.gz, rar, 7z)
- [ ] Parallel extraction for improved performance
- [ ] Dry-run mode to preview operations
- [ ] Configuration file support
- [ ] Resume interrupted operations
- [ ] Web UI for remote operations

## Author

Sergey Pankov

## Acknowledgments

Built with modern Python best practices and designed for simplicity and reliability.
