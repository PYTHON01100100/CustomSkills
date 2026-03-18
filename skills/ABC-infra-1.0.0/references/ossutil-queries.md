# ossutil Command Reference

ossutil is the dedicated CLI tool for Alibaba Cloud OSS (Object Storage Service).
Use **ossutil 2.x** for new work — binary is always named `ossutil`.

---

## Installation

```bash
# macOS (amd64)
curl -o ossutil.zip https://gosspublic.alicdn.com/ossutil/v2/2.2.0/ossutil-2.2.0-mac-amd64.zip
unzip ossutil.zip && chmod +x ossutil && sudo mv ossutil /usr/local/bin/

# macOS (Apple Silicon / arm64)
curl -o ossutil.zip https://gosspublic.alicdn.com/ossutil/v2/2.2.0/ossutil-2.2.0-mac-arm64.zip
unzip ossutil.zip && chmod +x ossutil && sudo mv ossutil /usr/local/bin/

# Linux (amd64)
curl -o ossutil.zip https://gosspublic.alicdn.com/ossutil/v2/2.2.0/ossutil-2.2.0-linux-amd64.zip
unzip ossutil.zip && chmod +x ossutil && sudo mv ossutil /usr/local/bin/

# Windows: download ossutil-2.2.0-windows-amd64.zip, extract, add to PATH

# Verify
ossutil --version
```

---

## Configuration

```bash
# Interactive setup
ossutil config
# Prompts: AccessKey ID, AccessKey Secret, Region, Endpoint (optional)

# Non-interactive
ossutil config \
  --access-key-id     LTAI5tExampleKeyId123 \
  --access-key-secret ExampleSecretKey456abcXYZ \
  --region            me-central-1 \
  --endpoint          oss-me-central-1.aliyuncs.com

# Use a custom config file at runtime
ossutil -c /path/to/custom.config ls oss://

# Environment variables (override config file)
export OSS_ACCESS_KEY_ID=LTAI5tExampleKeyId123
export OSS_ACCESS_KEY_SECRET=ExampleSecretKey456abcXYZ
export OSS_REGION=me-central-1
```

Config file location: `~/.ossutilconfig` (Linux/macOS) or `%USERPROFILE%\.ossutilconfig` (Windows).

---

## Upload — `cp` and `sync`

### Single file
```bash
# Upload to bucket root (object name = filename)
ossutil cp /local/report.pdf oss://mybucket/

# Upload and set a different object name/path
ossutil cp /local/report.pdf oss://mybucket/reports/2026/march.pdf
```

### Upload entire folder (recursive)
```bash
ossutil cp -r /local/project/ oss://mybucket/project/
# -r = --recursive
```

### Upload only newer files (incremental)
```bash
ossutil cp -r -u /local/project/ oss://mybucket/project/
# -u = --update  — skips files already in OSS that are newer or same age
```

### Upload with include / exclude filters
```bash
# Only .jpg files
ossutil cp -r /local/photos/ oss://mybucket/photos/ --include "*.jpg"

# Everything except .tmp and .log files
ossutil cp -r /local/app/ oss://mybucket/app/ --exclude "*.tmp" --exclude "*.log"
```

### Resumable / multipart upload for large files
```bash
# ossutil auto-uses multipart for files > 100 MB; add --checkpoint-dir to resume
ossutil cp /local/bigfile.tar.gz oss://mybucket/ \
  --checkpoint-dir /tmp/oss_checkpoint

# Re-run the same command to resume after interruption
ossutil cp /local/bigfile.tar.gz oss://mybucket/ \
  --checkpoint-dir /tmp/oss_checkpoint

# Tune concurrency and part size
ossutil cp /local/bigfile.tar.gz oss://mybucket/ \
  --jobs 10 \
  --parallel 5 \
  --part-size 10485760 \
  --checkpoint-dir /tmp/oss_checkpoint
```

### Upload with storage class
```bash
ossutil cp /local/file.csv oss://mybucket/ --storage-class Standard      # default
ossutil cp /local/file.csv oss://mybucket/ --storage-class IA            # Infrequent Access
ossutil cp /local/file.csv oss://mybucket/ --storage-class Archive
ossutil cp /local/file.csv oss://mybucket/ --storage-class ColdArchive

# Recursive upload with storage class
ossutil cp -r /local/archive/ oss://mybucket/archive/ --storage-class Archive
```

### Upload with server-side encryption
```bash
# AES-256
ossutil cp /local/file.txt oss://mybucket/ \
  --meta "x-oss-server-side-encryption:AES256"

# KMS (default CMK)
ossutil cp /local/file.txt oss://mybucket/ \
  --meta "x-oss-server-side-encryption:KMS"

# KMS with specific key ID
ossutil cp /local/file.txt oss://mybucket/ \
  --meta "x-oss-server-side-encryption:KMS#x-oss-server-side-encryption-key-id:<key-id>"
```

### Upload with custom metadata and Content-Type
```bash
# Multiple headers separated by #
ossutil cp /local/page.html oss://mybucket/ \
  --meta "Content-Type:text/html; charset=utf-8#Cache-Control:no-cache#X-Oss-Meta-Env:prod"
```

### Sync local folder → OSS (recommended for ongoing deployments)
```bash
# Sync (only upload new/changed files)
ossutil sync /local/website/ oss://mybucket/website/

# Sync and delete OSS objects that no longer exist locally
ossutil sync /local/website/ oss://mybucket/website/ --delete

# Sync with filters
ossutil sync /local/src/ oss://mybucket/src/ \
  --include "*.go" --include "*.mod" --exclude "vendor/"

# Sync with concurrency
ossutil sync /local/data/ oss://mybucket/data/ --jobs 10 --parallel 5

# Limit upload speed (KB/s)
ossutil sync /local/data/ oss://mybucket/data/ --maxupspeed 2048
```

---

## Download — `cp` and `sync`

### Single object
```bash
# Download to local directory (keep original name)
ossutil cp oss://mybucket/reports/march.pdf /local/downloads/

# Download and rename
ossutil cp oss://mybucket/reports/march.pdf /local/downloads/march-report.pdf
```

### Download entire prefix (folder)
```bash
ossutil cp -r oss://mybucket/project/ /local/project/
```

### Download only newer files
```bash
ossutil cp -r -u oss://mybucket/project/ /local/project/
```

### Sync OSS → local
```bash
ossutil sync oss://mybucket/data/ /local/data/

# Delete local files that no longer exist in OSS
ossutil sync oss://mybucket/data/ /local/data/ --delete

# Limit download speed (KB/s)
ossutil sync oss://mybucket/data/ /local/data/ --maxdownspeed 1024
```

---

## List — `ls`

```bash
# List all buckets
ossutil ls oss://

# List objects in a bucket
ossutil ls oss://mybucket

# List objects under a prefix
ossutil ls oss://mybucket/logs/2026/03/

# Long listing: shows size, date, storage class, ETag
ossutil ls oss://mybucket -l

# List all versions (versioned bucket)
ossutil ls oss://mybucket --all-versions

# List in-progress multipart uploads
ossutil ls oss://mybucket -m
```

---

## Copy / Move within OSS

```bash
# Copy object within same bucket
ossutil cp oss://mybucket/src/file.txt oss://mybucket/dest/file.txt

# Copy between buckets (same region)
ossutil cp oss://sourcebucket/file.txt oss://destbucket/file.txt

# Copy entire prefix between buckets
ossutil cp -r oss://sourcebucket/src/ oss://destbucket/dest/

# Move = copy then delete (no native mv command)
ossutil cp oss://mybucket/old/file.txt oss://mybucket/new/file.txt
ossutil rm oss://mybucket/old/file.txt
```

---

## Delete — `rm`  ⚠ Confirm before running

```bash
# Delete single object
ossutil rm oss://mybucket/path/to/file.txt

# Delete with force flag (no confirmation prompt)
ossutil rm oss://mybucket/path/to/file.txt -f

# Delete all objects under a prefix (recursive)
ossutil rm oss://mybucket/logs/ -r
ossutil rm oss://mybucket/logs/ -r -f          # skip confirmation

# Delete matching a pattern
ossutil rm oss://mybucket --include "*.tmp" -r -f

# Delete all objects in a bucket (empty it)
ossutil rm oss://mybucket -r -f

# Delete all object versions (versioned bucket)
ossutil rm oss://mybucket -r --all-versions -f

# Delete a bucket itself (must be empty first, then use -b)
ossutil rm oss://mybucket -b -f

# Abort all incomplete multipart uploads (cleanup)
ossutil rm oss://mybucket -m -r -f
```

---

## Bucket Management

```bash
# Create bucket (private, Standard, LRS)
ossutil mb oss://mybucket

# Create with specific region, ACL, storage class, and redundancy
ossutil mb oss://mybucket \
  --acl private \
  --storage-class Standard \
  --redundancy-type ZRS

# Get bucket info (ACL, region, versioning, sizes)
ossutil stat oss://mybucket

# Set bucket ACL  ⚠ Confirm before running
ossutil api put-bucket-acl --bucket mybucket --acl private

# Enable versioning  ⚠ Confirm before running
ossutil api put-bucket-versioning \
  --bucket mybucket \
  --versioning-configuration '{"Status":"Enabled"}'

# Suspend versioning  ⚠ Confirm before running
ossutil api put-bucket-versioning \
  --bucket mybucket \
  --versioning-configuration '{"Status":"Suspended"}'

# Set default server-side encryption  ⚠ Confirm before running
ossutil api put-bucket-encryption \
  --bucket mybucket \
  --server-side-encryption-rule '{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}'
```

---

## Object Metadata and ACL

```bash
# Get object metadata (size, ETag, Content-Type, custom headers, ACL)
ossutil stat oss://mybucket/path/to/file.txt

# Set object ACL  ⚠ Confirm before running
ossutil api put-object-acl --bucket mybucket --key path/to/file.txt --acl private
# Recursive:
ossutil set-acl oss://mybucket/prefix/ public-read -r

# Update metadata (add/change without replacing all)
ossutil set-meta oss://mybucket/file.txt "Cache-Control:max-age=3600" --update

# Replace all metadata
ossutil set-meta oss://mybucket/file.txt \
  "Content-Type:image/jpeg#Cache-Control:no-cache#X-Oss-Meta-Author:Ali"

# Recursively update metadata on all objects under a prefix
ossutil set-meta oss://mybucket/prefix/ "Content-Type:application/octet-stream" -r
```

---

## Multipart Upload Management

```bash
# List all in-progress multipart uploads
ossutil ls oss://mybucket -m

# List parts for a specific upload
ossutil listpart oss://mybucket/largefile.bin <UploadId>

# Abort a specific multipart upload  ⚠ Confirm before running
ossutil api abort-multipart-upload \
  --bucket mybucket \
  --key largefile.bin \
  --upload-id D9F4****************************

# Abort ALL incomplete multipart uploads in a bucket  ⚠ Confirm before running
ossutil rm oss://mybucket -m -r -f
```

---

## Useful Flags Quick Reference

| Flag | Short | Description |
|---|---|---|
| `--recursive` | `-r` | Operate on all objects under a path |
| `--force` | `-f` | Skip confirmation prompts |
| `--update` | `-u` | Only transfer if source is newer than destination |
| `--jobs` | `-j` | Concurrent file operations (default 3) |
| `--parallel` | | Concurrent parts within a single large file |
| `--part-size` | | Multipart part size in bytes |
| `--bigfile-threshold` | | File size (bytes) above which multipart is used (default 100 MB) |
| `--checkpoint-dir` | | Directory for resumable transfer state |
| `--include` | | Glob pattern to include (e.g. `"*.jpg"`) |
| `--exclude` | | Glob pattern to exclude (e.g. `"*.tmp"`) |
| `--storage-class` | | `Standard` / `IA` / `Archive` / `ColdArchive` |
| `--meta` | | Object metadata `key:value#key:value` |
| `--acl` | | `private` / `public-read` / `public-read-write` |
| `--delete` | | (sync) Delete dest objects missing from source |
| `--maxupspeed` | | Max upload speed in KB/s |
| `--maxdownspeed` | | Max download speed in KB/s |
| `--all-versions` | | Target all object versions |
| `--multipart` | `-m` | Target in-progress multipart uploads |
| `--bucket` | `-b` | Target the bucket itself (not objects) |
| `--sign-version` | | `v1` or `v4` (v4 required for some regions) |
| `--region` | | Override region for a single command |
| `--endpoint` | `-e` | Override OSS endpoint for a single command |
| `--config-file` | `-c` | Path to ossutil config file |
| `--retry-times` | | Retries on failure (default 10) |
| `--loglevel` | | `info` or `debug` |

---

## ossutil 1.x vs 2.x Notes

| | ossutil 1.x | ossutil 2.x |
|---|---|---|
| Binary name | `ossutil64` / `ossutilmac64` | `ossutil` |
| High-level commands | `cp`, `ls`, `rm`, `mb`, `sync`, `stat`, `set-acl`, `set-meta` | Same, plus `ossutil api <operation>` |
| API commands | Not available | `ossutil api put-bucket-acl`, `abort-multipart-upload`, etc. |
| Signature v4 | Not supported | `--sign-version v4` |
| Recommendation | Legacy | **Use this for new work** |
