---
name: alibaba-cloud-infra
description: Chat-based Alibaba Cloud infrastructure assistance using the aliyun CLI and ossutil. Use for querying, auditing, and monitoring Alibaba Cloud resources (ECS, OSS, RAM, Function Compute, ACK/ACR, RDS, SLS/Log Service, billing, etc.), and for proposing safe changes with explicit confirmation before any write/destructive action.
---

# Alibaba Cloud Infra

## Overview
Use the local `aliyun` CLI (and `ossutil` for OSS) to answer questions about Alibaba Cloud resources. Default to read-only queries. Only propose or run write/destructive actions after explicit user confirmation.

## Quick Start
1. Determine profile/region from environment or `~/.aliyun/config.json`.
2. Verify identity:
   ```
   aliyun sts GetCallerIdentity
   ```
3. Use read-only `List`/`Describe`/`Get` API operations to answer the question.
4. If the user asks for changes, outline the exact command and ask for confirmation before running.

## Setup / Configuration

### Install the CLI
```bash
# macOS (Homebrew)
brew install aliyun-cli

# Linux / macOS (script)
/bin/bash -c "$(curl -fsSL https://aliyuncli.alicdn.com/install.sh)"
```

### Configure credentials (interactive)
```bash
aliyun configure
# Prompts: AccessKey ID, AccessKey Secret, Region ID, output format
```

### Configure a named profile (non-interactive)
```bash
aliyun configure set \
  --profile myprofile \
  --mode AK \
  --access-key-id <YOUR_ACCESS_KEY_ID> \
  --access-key-secret <YOUR_ACCESS_KEY_SECRET> \
  --region cn-hangzhou
```

**Example — Saudi Arabia (Riyadh) profile:**
```bash
aliyun configure set \
  --profile saudi-prod \
  --mode AK \
  --access-key-id LTA******** \
  --access-key-secret ExampleSecretKey******Z \
  --region me-central-1
```

**Example — use that profile for a single command:**
```bash
aliyun ecs DescribeInstances --profile saudi-prod --RegionId me-central-1
```

### List / switch profiles
```bash
aliyun configure list                       # show all configured profiles and modes
aliyun configure switch --profile saudi-prod  # make saudi-prod the default
```

**Example output of `aliyun configure list`:**
```
Profile   | Credential         | Valid | Region        | Language
--------- | ------------------ | ----- | ------------- | --------
default * | AK:***YId          | true  | cn-hangzhou   | en
saudi-prod| AK:***123          | true  | me-central-1  | en
staging   | AK:***789          | true  | ap-southeast-1| en
```

### Environment variable overrides (highest priority)
```bash
ALIBABA_CLOUD_ACCESS_KEY_ID=<id>
ALIBABA_CLOUD_ACCESS_KEY_SECRET=<secret>
ALIBABA_CLOUD_REGION_ID=cn-hangzhou
ALIBABA_CLOUD_SECURITY_TOKEN=<sts-token>   # for STS credentials
ALIBABA_CLOUD_PROFILE=prod                 # select named profile
```

### Authentication modes
| Mode | When to use |
|---|---|
| `AK` | Static AccessKey pair (default) |
| `StsToken` | Temporary STS credentials |
| `RamRoleArn` | Assume a RAM role (auto-refreshes) |
| `EcsRamRole` | Instance-attached RAM role (no keys needed) |
| `CloudSSO` | Browser-based SSO login |

---

## Safety Rules (must follow)
- Treat all actions as **read-only** unless the user explicitly requests a change **and** confirms it.
- **Always ask for confirmation before running any write or destructive action.** This includes:
  - `Delete*` — deleting any resource (instance, bucket, user, database, access key…)
  - `Stop*` / `Reboot*` — stopping or rebooting ECS instances or RDS instances
  - `Terminate*` / `Destroy*` — any termination operation
  - `Modify*` / `Update*` / `Set*` — changing resource configuration or ACL
  - `Scale*` / `Execute*` (scaling rules) — Auto Scaling changes
  - `Attach*` / `Detach*` — attaching/detaching policies, disks, NICs
  - RAM/credential mutations — creating, disabling, or deleting access keys or roles
- Before any write action, show the **exact command** that will run and wait for the user to say yes/confirm.
- Use `--DryRun true` when available (ECS operations) and show the output before proceeding.
- Never reveal or log secrets (AccessKey ID/Secret, STS tokens).

**Confirmation prompt template:**
```
I am about to run:

  aliyun <product> <Operation> --Param Value ...

This will [describe what it does and what will be affected].
Do you want to proceed? (yes / no)
```

---

## Task Guide (common requests)
- **Inventory / list**: use `List`/`Describe` operations with `--RegionId`.
- **Health / errors**: query SLS Log Service (start-query → get-results).
- **Security checks**: RAM policies, OSS public access, ECS security group rules, RAM access key metadata.
- **Costs**: BSS OpenAPI billing queries (read-only).
- **Changes**: show exact `aliyun` command and require confirmation.

---

## CLI Syntax Pattern
```
aliyun <product> <APIOperation> --Param Value [--RegionId <region>] [--profile <profile>]
```
- Products and operations use **PascalCase** (e.g. `ecs DescribeInstances`).
- Parameters also use **PascalCase** (e.g. `--RegionId`, `--InstanceId`).
- Container Service (ACK) and Function Compute 3.0 use REST paths: `aliyun cs GET /api/v1/clusters`.
- OSS bucket/object operations use `ossutil` (separate binary).

---

## Region & Profile Handling
- If the user specifies a region/profile, honor it with `--RegionId` / `--profile`.
- Otherwise use `ALIBABA_CLOUD_PROFILE` / `ALIBABA_CLOUD_REGION_ID` if set, then fall back to `~/.aliyun/config.json`.
- When results are region-scoped, state the region used.

### Common Region IDs
| Region | ID |
|---|---|
| **Saudi Arabia (Riyadh)** | **`me-central-1`** |
| China (Hangzhou) | `cn-hangzhou` |
| China (Beijing) | `cn-beijing` |
| China (Shanghai) | `cn-shanghai` |
| China (Shenzhen) | `cn-shenzhen` |
| Singapore | `ap-southeast-1` |
| US East (Virginia) | `us-east-1` |
| US West (Silicon Valley) | `us-west-1` |
| Germany (Frankfurt) | `eu-central-1` |
| Japan (Tokyo) | `ap-northeast-1` |

---

## Output and Debugging
```bash
# Table output
aliyun ecs DescribeInstances --RegionId cn-hangzhou \
  --output cols=InstanceId,InstanceName,Status rows=Instances.Instance[]

# Poll until state changes
aliyun ecs DescribeInstances \
  --InstanceIds '["i-bp1xxxx"]' \
  --waiter expr='Instances.Instance[0].Status' to=Running

# Debug HTTP traffic
DEBUG=sdk aliyun ecs DescribeInstances --RegionId cn-hangzhou

# Built-in help
aliyun help ecs                    # list all ECS operations
aliyun help ecs DescribeInstances  # full parameter reference
```

---

---

## ossutil — OSS File and Folder Operations

ossutil is a dedicated binary for Alibaba Cloud OSS. It handles uploads, downloads, sync, and bucket management. Use **ossutil 2.x** (binary named `ossutil`).

### Install
```bash
# macOS (amd64)
curl -o ossutil.zip https://gosspublic.alicdn.com/ossutil/v2/2.2.0/ossutil-2.2.0-mac-amd64.zip
unzip ossutil.zip && chmod +x ossutil && sudo mv ossutil /usr/local/bin/

# macOS (Apple Silicon)
curl -o ossutil.zip https://gosspublic.alicdn.com/ossutil/v2/2.2.0/ossutil-2.2.0-mac-arm64.zip
unzip ossutil.zip && chmod +x ossutil && sudo mv ossutil /usr/local/bin/

# Linux (amd64)
curl -o ossutil.zip https://gosspublic.alicdn.com/ossutil/v2/2.2.0/ossutil-2.2.0-linux-amd64.zip
unzip ossutil.zip && chmod +x ossutil && sudo mv ossutil /usr/local/bin/

# Windows: download ossutil-2.2.0-windows-amd64.zip, extract, add to PATH
```

### Configure ossutil
```bash
# Interactive
ossutil config

# Non-interactive (example: Saudi Arabia region)
ossutil config \
  --access-key-id     LTAI5tExampleKeyId123 \
  --access-key-secret ExampleSecretKey456abcXYZ \
  --region            me-central-1 \
  --endpoint          oss-me-central-1.aliyuncs.com
```

### Upload Files and Folders

```bash
# Single file
ossutil cp /local/report.pdf oss://mybucket/

# Single file with custom path and name in OSS
ossutil cp /local/report.pdf oss://mybucket/reports/2026/march.pdf

# Entire folder (recursive)
ossutil cp -r /local/project/ oss://mybucket/project/

# Only newer files (incremental)
ossutil cp -r -u /local/project/ oss://mybucket/project/

# Filter by file type
ossutil cp -r /local/photos/ oss://mybucket/photos/ --include "*.jpg"
ossutil cp -r /local/app/   oss://mybucket/app/   --exclude "*.tmp" --exclude "*.log"

# Large file — resumable/multipart (auto for files > 100 MB; --checkpoint-dir to resume)
ossutil cp /local/bigfile.tar.gz oss://mybucket/ \
  --checkpoint-dir /tmp/oss_checkpoint \
  --jobs 10 --parallel 5 --part-size 10485760

# Upload with storage class
ossutil cp /local/file.csv oss://mybucket/ --storage-class IA       # Infrequent Access
ossutil cp /local/file.csv oss://mybucket/ --storage-class Archive

# Upload with server-side encryption
ossutil cp /local/file.txt oss://mybucket/ \
  --meta "x-oss-server-side-encryption:AES256"

# Upload with custom Content-Type and metadata
ossutil cp /local/page.html oss://mybucket/ \
  --meta "Content-Type:text/html; charset=utf-8#Cache-Control:no-cache"
```

### Sync (best for recurring deployments)
```bash
# Sync local → OSS (upload new/changed files only)
ossutil sync /local/website/ oss://mybucket/website/

# Sync and delete OSS objects removed locally  ⚠ Confirm before running
ossutil sync /local/website/ oss://mybucket/website/ --delete

# Sync OSS → local
ossutil sync oss://mybucket/data/ /local/data/

# Sync OSS → local and delete local files removed from OSS  ⚠ Confirm before running
ossutil sync oss://mybucket/data/ /local/data/ --delete

# With concurrency and speed limit
ossutil sync /local/data/ oss://mybucket/data/ --jobs 10 --maxupspeed 2048
```

### Download Files
```bash
# Single object
ossutil cp oss://mybucket/reports/march.pdf /local/downloads/

# Entire prefix
ossutil cp -r oss://mybucket/project/ /local/project/
```

### List and Inspect
```bash
ossutil ls oss://                          # all buckets
ossutil ls oss://mybucket                 # objects in bucket
ossutil ls oss://mybucket/prefix/ -l      # long listing (size, date, class)
ossutil ls oss://mybucket -m              # in-progress multipart uploads
ossutil stat oss://mybucket               # bucket info (ACL, region, versioning)
ossutil stat oss://mybucket/file.txt      # object metadata
```

### Delete  ⚠ Always confirm before running any rm command

```bash
# Single object
ossutil rm oss://mybucket/path/file.txt

# All objects under a prefix
ossutil rm oss://mybucket/logs/ -r

# All objects in bucket (empty it)
ossutil rm oss://mybucket -r -f

# Delete bucket itself (must be empty first)
ossutil rm oss://mybucket -b -f

# Abort all incomplete multipart uploads
ossutil rm oss://mybucket -m -r -f
```

### Bucket and Object Settings  ⚠ Confirm before running
```bash
# Create bucket
ossutil mb oss://mybucket --acl private --storage-class Standard

# Set bucket ACL
ossutil api put-bucket-acl --bucket mybucket --acl private

# Set object ACL
ossutil api put-object-acl --bucket mybucket --key path/file.txt --acl private

# Update object metadata
ossutil set-meta oss://mybucket/file.txt "Cache-Control:max-age=3600" --update

# Enable versioning
ossutil api put-bucket-versioning \
  --bucket mybucket \
  --versioning-configuration '{"Status":"Enabled"}'
```

---

## References
- `references/aliyun-cli-queries.md` — aliyun CLI patterns by service (ECS, RAM, RDS, SLS, billing…)
- `references/ossutil-queries.md` — full ossutil reference (all commands, flags, upload/download/sync)

## Assets
- `assets/icon.svg` — custom icon (dark cloud + terminal prompt)
