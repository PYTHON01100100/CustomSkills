# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

This is a **Claude AI Skill** (`alibaba-cloud-infra` v1.0.0) — a packaged prompt/behavior definition that enables chat-based Alibaba Cloud infrastructure assistance via the local `aliyun` CLI and `ossutil`. It is not a software application; there are no build, test, or lint steps.

## Project Structure

```
SKILL.md                              # Skill definition: behavior rules, setup guide, task guide
_meta.json                            # Package metadata (slug, version, ownerId, publishedAt)
assets/icon.svg                       # Custom icon for the skill
references/aliyun-cli-queries.md      # aliyun CLI command patterns by service
```

## Core Behavior (from SKILL.md)

**Safety rules — always enforce:**
- Default to read-only queries. Never run write/destructive actions without explicit user request **and** confirmation.
- For any delete/stop/terminate/modify/scale/billing/RAM-credentials action, require a confirmation step.
- Use `--DryRun true` (ECS operations) when available; show the plan before execution.
- Never reveal or log secrets (AccessKey ID/Secret, STS tokens).

**Workflow:**
1. Resolve profile/region: check `ALIBABA_CLOUD_PROFILE`/`ALIBABA_CLOUD_REGION_ID` env vars, then `~/.aliyun/config.json`.
2. Verify identity: `aliyun sts GetCallerIdentity`.
3. Answer with read-only `List`/`Describe`/`Get` operations.
4. For changes: show the exact command and wait for confirmation before running.

**CLI syntax pattern:**
```
aliyun <product> <APIOperation> --Param Value [--RegionId <region>] [--profile <profile>]
```
Operations and parameters use PascalCase. Container Service (ACK) and Function Compute 3.0 use REST paths (`aliyun cs GET /api/v1/clusters`). OSS uses `ossutil`.

## Key aliyun CLI Patterns (from references/aliyun-cli-queries.md)

**Read-only:**
| Service | Command |
|---|---|
| Identity | `aliyun sts GetCallerIdentity` |
| ECS instances | `aliyun ecs DescribeInstances --RegionId cn-hangzhou` |
| ECS security groups | `aliyun ecs DescribeSecurityGroups --RegionId cn-hangzhou` |
| OSS buckets | `ossutil ls oss://` |
| OSS bucket ACL | `ossutil stat oss://<bucket>` |
| RAM users/roles | `aliyun ram ListUsers` / `aliyun ram ListRoles` |
| RAM access keys | `aliyun ram ListAccessKeys --UserName <user>` |
| Function Compute | `aliyun fc ListFunctions --ServiceName <svc>` |
| ACK clusters | `aliyun cs GET /api/v1/clusters` |
| RDS instances | `aliyun rds DescribeDBInstances --RegionId cn-hangzhou` |
| Log Service | `aliyun sls GET /logstores/<store>?type=log&from=<t>&to=<t>&query=...` |
| Billing | `aliyun bssopenapi QueryAccountBill --BillingCycle 2026-02 --Granularity MONTHLY` |

**Write actions requiring confirmation:**
- ECS: `aliyun ecs StopInstance/DeleteInstance --InstanceId i-xxxx` (support `--DryRun true`)
- ESS scaling: `aliyun ess ModifyScalingGroup --ScalingGroupId asg-xxxx --MinSize N --MaxSize N`
- OSS: `ossutil set-bucket-acl oss://<bucket> private` / `ossutil rm oss://<bucket>/key`
- RAM: `aliyun ram UpdateAccessKey --Status Inactive` / `aliyun ram DeleteAccessKey`
- RDS: `aliyun rds RestartDBInstance` / `aliyun rds DeleteDBInstance`

## Editing This Skill

Changes to `SKILL.md` define the skill's behavior for all users. When modifying it:
- Keep safety rules intact — the read-only default and confirmation requirement are non-negotiable.
- `references/aliyun-cli-queries.md` is the command reference library; add new service patterns there.
- `_meta.json` version should be bumped when publishing updates.
