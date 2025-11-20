# Quick Start Guide

## Installation

### Option 1: Install as a tool (recommended)

```bash
cd massunpacker
uv tool install .
```

After installation, `massunpacker` command will be available globally.

### Option 2: Run with uv

```bash
cd massunpacker
uv run massunpacker --help
```

## Basic Usage

1. **Extract all zips from a folder:**
   ```bash
   # With quoted pattern
   massunpacker "/path/to/archives/*.zip"

   # Or without quotes (shell expands to file list)
   massunpacker *.zip
   ```

2. **Extract to specific directory:**
   ```bash
   massunpacker "*.zip" --extract-to=output
   ```

3. **Process first 5 archives only:**
   ```bash
   # Works with or without quotes
   massunpacker *.zip --count=5
   ```

4. **Explicit file list:**
   ```bash
   massunpacker file1.zip file2.zip file3.zip
   ```

5. **Use SHA256 for collision detection:**
   ```bash
   massunpacker "*.zip" --collision=hash-sha256
   ```

6. **Custom OK/ERR folders:**
   ```bash
   massunpacker "*.zip" --mv-ok=processed --mv-er=failed
   ```

## Quick Test

Create test archives:

```bash
# Create test data
mkdir test_data && cd test_data
echo "content 1" > file1.txt
echo "content 2" > file2.txt
echo "content 3" > file3.txt

# Create archives
zip archive1.zip file1.txt file2.txt
zip archive2.zip file2.txt file3.txt
cd ..

# Extract
massunpacker "test_data/*.zip" --extract-to=output

# Check results
ls -la output/
```

## Output Folders

After processing, archives are automatically moved to:

- `OK/` - Successfully processed archives (no errors)
- `ERR/` - Archives with errors or corruption

These folders are created automatically in the current directory, or you can specify custom paths with `--mv-ok` and `--mv-er`.

## Collision Handling

When the same filename appears in multiple archives:

- If files are **identical** (same hash): second file is skipped
- If files are **different**: second file is renamed to `filename-1.ext`

Example:
```
archive1.zip contains: photo.jpg
archive2.zip contains: photo.jpg (different content)
Result: photo.jpg and photo-1.jpg
```

## Getting Help

```bash
massunpacker --help
```

For full documentation, see [README.md](README.md).
