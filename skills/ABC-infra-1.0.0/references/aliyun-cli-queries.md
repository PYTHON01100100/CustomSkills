# Alibaba Cloud CLI Query Patterns

## Identity / Account
```bash
aliyun sts GetCallerIdentity          # returns AccountId, UserId, Arn
aliyun ram GetAccountAlias            # returns human-readable account alias
```

## Saudi Arabia Region (me-central-1)
All standard commands work with `--RegionId me-central-1`. Examples:
```bash
# Set up a Saudi profile
aliyun configure set \
  --profile saudi-prod \
  --mode AK \
  --access-key-id LTAI5tExampleKeyId123 \
  --access-key-secret ExampleSecretKey456abcXYZ \
  --region me-central-1

# List ECS instances in Saudi Arabia
aliyun ecs DescribeInstances --profile saudi-prod --RegionId me-central-1

# List RDS instances in Saudi Arabia
aliyun rds DescribeDBInstances --profile saudi-prod --RegionId me-central-1

# List OSS buckets (region set via profile or env var)
ALIBABA_CLOUD_REGION_ID=me-central-1 ossutil ls oss://

# Get billing for Saudi-region resources
aliyun bssopenapi QueryAccountBill \
  --profile saudi-prod \
  --BillingCycle 2026-03 \
  --Granularity MONTHLY
```

## ECS – Elastic Compute Service
```bash
# List all instances
aliyun ecs DescribeInstances --RegionId cn-hangzhou

# Table view: InstanceId + Status + Public IP
aliyun ecs DescribeInstances --RegionId cn-hangzhou \
  --output cols=InstanceId,InstanceName,Status,PublicIpAddress.IpAddress rows=Instances.Instance[]

# Filter by status or name
aliyun ecs DescribeInstances --RegionId cn-hangzhou --Status Running
aliyun ecs DescribeInstances --RegionId cn-hangzhou --InstanceName "web-*"

# Get specific instances
aliyun ecs DescribeInstances --RegionId cn-hangzhou --InstanceIds '["i-bp1xxxx","i-bp2xxxx"]'

# Security groups
aliyun ecs DescribeSecurityGroups --RegionId cn-hangzhou

# Security group inbound/outbound rules
aliyun ecs DescribeSecurityGroupAttribute \
  --RegionId cn-hangzhou \
  --SecurityGroupId sg-bp1xxxxxxx \
  --Direction all

# List available regions
aliyun ecs DescribeRegions
```

## OSS – Object Storage Service
```bash
# List all buckets
ossutil ls oss://

# Bucket ACL (private / public-read / public-read-write)
ossutil stat oss://<bucket-name>

# Public access block status
ossutil get-bucket-public-access-block --bucket <bucket-name>

# Bucket policy
ossutil get-bucket-policy --bucket <bucket-name>

# List objects in a bucket
ossutil ls oss://<bucket-name>/

# Bucket storage statistics
ossutil get-bucket-stat --bucket <bucket-name>
```

## RAM – Resource Access Management (equivalent of AWS IAM)
```bash
# List users and roles
aliyun ram ListUsers
aliyun ram ListRoles

# Get a specific user or role
aliyun ram GetUser --UserName alice
aliyun ram GetRole --RoleName MyRole

# List access keys (metadata only — secret is not returned)
aliyun ram ListAccessKeys --UserName alice

# List policies
aliyun ram ListPolicies --PolicyType Custom
aliyun ram ListPolicies --PolicyType System

# List policies attached to a user
aliyun ram ListPoliciesForUser --UserName alice

# List groups
aliyun ram ListGroups
```

## Function Compute (FC) – equivalent of AWS Lambda
```bash
# FC 2.0 (service/function model)
aliyun fc ListServices
aliyun fc ListFunctions --ServiceName my-service

# FC 3.0 (function-based, REST API)
aliyun fc GET /2023-03-30/functions
aliyun fc GET /2023-03-30/functions?limit=100&prefix=my-func

# List triggers (FC 2.0)
aliyun fc ListTriggers --ServiceName my-service --FunctionName my-function
```

## Container Service – ACK (Kubernetes) / ACR (Registry)
```bash
# List all Kubernetes clusters
aliyun cs GET /api/v1/clusters

# Filter by type
aliyun cs GET /api/v1/clusters?cluster_type=ManagedKubernetes

# Get cluster details
aliyun cs GET /api/v1/clusters/<cluster-id>

# List ACR repositories
aliyun cr ListRepository --InstanceId <acr-instance-id>
aliyun cr ListNamespace  --InstanceId <acr-instance-id>
```

## ApsaraDB RDS
```bash
# List all RDS instances
aliyun rds DescribeDBInstances --RegionId cn-hangzhou

# Filter by engine
aliyun rds DescribeDBInstances --RegionId cn-hangzhou --Engine MySQL
aliyun rds DescribeDBInstances --RegionId cn-hangzhou --Engine PostgreSQL

# Get instance details
aliyun rds DescribeDBInstanceAttribute --DBInstanceId rm-uf6wjk5xxxxxxx

# List databases in an instance
aliyun rds DescribeDatabases --DBInstanceId rm-uf6wjk5xxxxxxx
```

## SLS / Log Service – equivalent of AWS CloudWatch Logs
```bash
# List projects
aliyun sls GET /projects --endpoint sls.cn-hangzhou.aliyuncs.com

# Query logs (replace project endpoint accordingly)
# Endpoint format: https://<project-name>.<region>.log.aliyuncs.com
aliyun sls GET /logstores/my-logstore \
  --endpoint https://my-project.cn-hangzhou.log.aliyuncs.com \
  --query "type=log&from=<epoch-start>&to=<epoch-end>&query=level:ERROR&line=100"
```

## Billing / Cost Management (BSS)
```bash
# Monthly bill summary
aliyun bssopenapi QueryAccountBill \
  --BillingCycle 2026-02 \
  --Granularity MONTHLY

# Daily breakdown by product
aliyun bssopenapi QueryAccountBill \
  --BillingCycle 2026-02 \
  --Granularity DAILY \
  --ProductCode ecs

# Account balance
aliyun bssopenapi QueryAccountBalance

# Bill overview
aliyun bssopenapi QueryBillOverview --BillingCycle 2026-02
```

---

## Common Write Actions (confirm before running)

### ECS – Instance lifecycle
```bash
# Dry-run first (supported on most ECS mutations)
aliyun ecs StopInstance   --InstanceId i-bp1xxxx --DryRun true
aliyun ecs StartInstance  --InstanceId i-bp1xxxx --DryRun true
aliyun ecs RebootInstance --InstanceId i-bp1xxxx --DryRun true
aliyun ecs DeleteInstance --InstanceId i-bp1xxxx --DryRun true

# Execute (remove --DryRun true after confirmation)
aliyun ecs StopInstance   --InstanceId i-bp1xxxx
aliyun ecs StartInstance  --InstanceId i-bp1xxxx
aliyun ecs RebootInstance --InstanceId i-bp1xxxx
aliyun ecs DeleteInstance --InstanceId i-bp1xxxx   # IRREVERSIBLE
```

### Auto Scaling (ESS)
```bash
# Describe scaling groups (read-only)
aliyun ess DescribeScalingGroups --RegionId cn-hangzhou

# Modify scaling group capacity (write)
aliyun ess ModifyScalingGroup \
  --ScalingGroupId asg-bp1xxxx \
  --MinSize 2 \
  --MaxSize 10

# Execute a scaling rule (write)
aliyun ess ExecuteScalingRule --ScalingRuleAri ari:acs:ess:cn-hangzhou:123456:scalingrule/asr-xxxx
```

### OSS – Write operations
```bash
# Change bucket ACL
ossutil set-bucket-acl oss://<bucket-name> private
ossutil set-bucket-acl oss://<bucket-name> public-read

# Delete an object
ossutil rm oss://<bucket-name>/path/to/object

# Delete a bucket (IRREVERSIBLE — must be empty first)
aliyun oss DeleteBucket --BucketName my-bucket
```

### RAM – Credential/permission changes
```bash
# Disable an access key (non-destructive)
aliyun ram UpdateAccessKey \
  --UserName alice \
  --UserAccessKeyId LTAI5xxxx \
  --Status Inactive

# Delete an access key (IRREVERSIBLE)
aliyun ram DeleteAccessKey --UserName alice --UserAccessKeyId LTAI5xxxx

# Attach a policy to a user
aliyun ram AttachPolicyToUser \
  --PolicyType System \
  --PolicyName AliyunECSReadOnlyAccess \
  --UserName alice

# Delete a RAM user (IRREVERSIBLE — detach all policies/groups first)
aliyun ram DeleteUser --UserName alice
```

### RDS – Write operations
```bash
# Restart an RDS instance
aliyun rds RestartDBInstance --DBInstanceId rm-uf6wjk5xxxxxxx

# Delete an RDS instance (IRREVERSIBLE)
aliyun rds DeleteDBInstance --DBInstanceId rm-uf6wjk5xxxxxxx
```

---

## AWS CLI → aliyun CLI Quick Reference

| AWS CLI | aliyun CLI |
|---|---|
| `aws sts get-caller-identity` | `aliyun sts GetCallerIdentity` |
| `aws configure --profile foo` | `aliyun configure --profile foo` |
| `aws ec2 describe-instances` | `aliyun ecs DescribeInstances` |
| `aws iam list-users` | `aliyun ram ListUsers` |
| `aws iam list-roles` | `aliyun ram ListRoles` |
| `aws s3 ls` | `ossutil ls oss://` |
| `aws lambda list-functions` | `aliyun fc ListFunctions --ServiceName svc` |
| `aws eks list-clusters` | `aliyun cs GET /api/v1/clusters` |
| `aws rds describe-db-instances` | `aliyun rds DescribeDBInstances` |
| `aws logs filter-log-events` | `aliyun sls GET /logstores/<store>?type=log&...` |
| `aws ce get-cost-and-usage` | `aliyun bssopenapi QueryAccountBill` |
| `--dry-run` (global flag) | `--DryRun true` (ECS per-operation parameter) |
| `--profile` | `--profile` (same) |
| `--region` | `--RegionId` (in API params) or `ALIBABA_CLOUD_REGION_ID` env var |
