# Jobs Reviews Dashboard - AWS Deployment Script (PowerShell)
# Deploys static frontend to S3 + CloudFront
# Idempotent: safe to run multiple times

$ErrorActionPreference = "Stop"

# Configuration
$BUCKET_NAME = "jobs-reviews-phildev"
$REGION = "us-east-1"
$FRONTEND_DIR = Join-Path $PSScriptRoot "..\src\frontend"
$DISTRIBUTION_ID_FILE = Join-Path $PSScriptRoot ".cloudfront-id"

Write-Host "=== Jobs Reviews Dashboard - Deploy ===" -ForegroundColor Cyan
Write-Host "Bucket: $BUCKET_NAME"
Write-Host "Region: $REGION"
Write-Host "Source: $FRONTEND_DIR"
Write-Host ""

# Step 1: Create S3 bucket if not exists
Write-Host "[1/5] Checking S3 bucket..." -ForegroundColor Yellow
try {
    aws s3api head-bucket --bucket $BUCKET_NAME --region $REGION 2>$null
    Write-Host "  Bucket already exists." -ForegroundColor Green
} catch {
    Write-Host "  Creating bucket..."
    aws s3api create-bucket --bucket $BUCKET_NAME --region $REGION | Out-Null
    Write-Host "  Bucket created." -ForegroundColor Green
}

# Step 2: Configure bucket for static website hosting
Write-Host "[2/5] Configuring static website hosting..." -ForegroundColor Yellow
aws s3 website "s3://$BUCKET_NAME" --index-document index.html --error-document index.html
Write-Host "  Website hosting configured." -ForegroundColor Green

# Step 3: Set bucket policy for public read access
Write-Host "[3/5] Setting bucket policy..." -ForegroundColor Yellow

# Disable block public access first
aws s3api put-public-access-block --bucket $BUCKET_NAME --public-access-block-configuration "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false" 2>$null

# Write policy file without BOM
$policyJson = '{"Version":"2012-10-17","Statement":[{"Sid":"PublicReadGetObject","Effect":"Allow","Principal":"*","Action":"s3:GetObject","Resource":"arn:aws:s3:::' + $BUCKET_NAME + '/*"}]}'
$policyFile = Join-Path $env:TEMP "bucket-policy.json"
[System.IO.File]::WriteAllText($policyFile, $policyJson, [System.Text.UTF8Encoding]::new($false))

aws s3api put-bucket-policy --bucket $BUCKET_NAME --policy "file://$policyFile"
Remove-Item $policyFile -Force
Write-Host "  Bucket policy set for public read." -ForegroundColor Green

# Step 4: Upload frontend files
Write-Host "[4/5] Uploading frontend files..." -ForegroundColor Yellow

aws s3 sync $FRONTEND_DIR "s3://$BUCKET_NAME" --delete --exclude "*" --include "*.html" --content-type "text/html" --cache-control "max-age=300"
aws s3 sync $FRONTEND_DIR "s3://$BUCKET_NAME" --exclude "*" --include "*.css" --content-type "text/css" --cache-control "max-age=300"
aws s3 sync $FRONTEND_DIR "s3://$BUCKET_NAME" --exclude "*" --include "*.js" --content-type "application/javascript" --cache-control "max-age=300"
aws s3 sync $FRONTEND_DIR "s3://$BUCKET_NAME" --exclude "*" --include "*.json" --content-type "application/json" --cache-control "max-age=60"
aws s3 sync $FRONTEND_DIR "s3://$BUCKET_NAME" --exclude "*" --include "*.png" --content-type "image/png" --cache-control "max-age=86400"

Write-Host "  Files uploaded." -ForegroundColor Green

# Step 5: CloudFront distribution
Write-Host "[5/5] Configuring CloudFront..." -ForegroundColor Yellow

$distributionId = $null

# Check if we have a saved distribution ID
if (Test-Path $DISTRIBUTION_ID_FILE) {
    $content = Get-Content $DISTRIBUTION_ID_FILE -Raw -ErrorAction SilentlyContinue
    if ($content) {
        $distributionId = $content.Trim()
        if ($distributionId -and $distributionId.Length -gt 0) {
            Write-Host "  Found existing distribution: $distributionId"
        } else {
            $distributionId = $null
        }
    }
}

if (-not $distributionId) {
    # Check if a distribution already exists for this bucket
    $existingDists = aws cloudfront list-distributions --query "DistributionList.Items[?Origins.Items[?contains(DomainName,'$BUCKET_NAME')]].Id" --output text 2>$null
    if ($existingDists -and $existingDists -ne "None" -and $existingDists.Trim() -ne "") {
        $distributionId = $existingDists.Split("`t")[0].Trim()
        Write-Host "  Found existing distribution: $distributionId"
    }
}

if (-not $distributionId) {
    # Create new CloudFront distribution
    Write-Host "  Creating CloudFront distribution..."

    $callerRef = "jobs-reviews-" + (Get-Date -Format "yyyyMMddHHmmss")
    $originDomain = "$BUCKET_NAME.s3-website-$REGION.amazonaws.com"

    $cfConfig = @{
        CallerReference = $callerRef
        Origins = @{
            Quantity = 1
            Items = @(
                @{
                    Id = "S3-$BUCKET_NAME"
                    DomainName = $originDomain
                    CustomOriginConfig = @{
                        HTTPPort = 80
                        HTTPSPort = 443
                        OriginProtocolPolicy = "http-only"
                    }
                }
            )
        }
        DefaultCacheBehavior = @{
            TargetOriginId = "S3-$BUCKET_NAME"
            ViewerProtocolPolicy = "redirect-to-https"
            AllowedMethods = @{
                Quantity = 2
                Items = @("GET", "HEAD")
                CachedMethods = @{
                    Quantity = 2
                    Items = @("GET", "HEAD")
                }
            }
            ForwardedValues = @{
                QueryString = $false
                Cookies = @{ Forward = "none" }
            }
            MinTTL = 0
            DefaultTTL = 300
            MaxTTL = 86400
            Compress = $true
        }
        Comment = "Jobs Reviews Dashboard - Phil Dev"
        Enabled = $true
        DefaultRootObject = "index.html"
        PriceClass = "PriceClass_100"
    } | ConvertTo-Json -Depth 10

    $cfConfigFile = Join-Path $env:TEMP "cf-config.json"
    [System.IO.File]::WriteAllText($cfConfigFile, $cfConfig, [System.Text.UTF8Encoding]::new($false))

    $resultJson = aws cloudfront create-distribution --distribution-config "file://$cfConfigFile" --output json
    $result = $resultJson | ConvertFrom-Json
    $distributionId = $result.Distribution.Id
    $domainName = $result.Distribution.DomainName

    Remove-Item $cfConfigFile -Force

    # Save distribution ID for future runs
    [System.IO.File]::WriteAllText($DISTRIBUTION_ID_FILE, $distributionId, [System.Text.UTF8Encoding]::new($false))

    Write-Host "  Distribution created: $distributionId" -ForegroundColor Green
    Write-Host "  Domain: $domainName" -ForegroundColor Green
    Write-Host "  NOTE: Distribution may take 5-15 minutes to deploy globally." -ForegroundColor Yellow
} else {
    # Invalidate cache on existing distribution
    Write-Host "  Invalidating cache..."
    aws cloudfront create-invalidation --distribution-id $distributionId --paths "/*" --output text | Out-Null
    Write-Host "  Cache invalidated." -ForegroundColor Green

    # Get domain name
    $domainName = aws cloudfront get-distribution --id $distributionId --query "Distribution.DomainName" --output text
}

Write-Host ""
Write-Host "=== Deploy Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "S3 Website URL:   http://$BUCKET_NAME.s3-website-$REGION.amazonaws.com" -ForegroundColor Cyan
Write-Host "CloudFront URL:   https://$domainName" -ForegroundColor Cyan
Write-Host ""
Write-Host "Use the CloudFront URL for HTTPS access from your phone." -ForegroundColor White
