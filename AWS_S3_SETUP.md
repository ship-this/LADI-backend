# AWS S3 Setup Guide for LADI Backend

This guide explains how to configure AWS S3 for file storage in the LADI backend application.

## Overview

The LADI backend now supports AWS S3 for file storage, with automatic fallback to local storage if AWS credentials are not configured. This provides:

- **Persistent file storage** (files survive server restarts)
- **Scalable storage** (no local disk space limitations)
- **Secure file access** (presigned URLs with expiration)
- **Automatic fallback** (works without AWS for development)

## Quick Setup

### 1. Run the Setup Script

```bash
cd backend
python setup_aws.py
```

This interactive script will guide you through the setup process.

### 2. Manual Setup

If you prefer to set up manually, follow these steps:

#### Step 1: Create AWS Account
1. Go to [AWS Console](https://aws.amazon.com/)
2. Create a new account or sign in to existing account
3. Note: AWS offers free tier with 5GB S3 storage for 12 months

#### Step 2: Create S3 Bucket
1. Go to [S3 Console](https://console.aws.amazon.com/s3/)
2. Click "Create bucket"
3. Choose a unique bucket name (e.g., `ladi-files-2024`)
4. Select your preferred region (e.g., `us-east-1`)
5. Keep default settings for now
6. Click "Create bucket"

#### Step 3: Create IAM User
1. Go to [IAM Console](https://console.aws.amazon.com/iam/)
2. Click "Users" → "Add user"
3. Enter username (e.g., `ladi-s3-user`)
4. Select "Programmatic access"
5. Click "Next: Permissions"

#### Step 4: Attach S3 Policy
1. Click "Attach existing policies directly"
2. Search for "AmazonS3FullAccess"
3. Check the box and click "Next"
4. Click "Create user"

#### Step 5: Get Credentials
1. Click on your new user
2. Go to "Security credentials" tab
3. Click "Create access key"
4. **Important**: Copy and save the Access Key ID and Secret Access Key

#### Step 6: Configure Environment Variables

Add these to your `.env` file:

```env
# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_S3_BUCKET=your_bucket_name_here
AWS_S3_REGION=us-east-1
```

## Testing the Setup

### Test S3 Connection

```bash
cd backend
python setup_aws.py test
```

This will test if your AWS credentials are working correctly.

### Test File Upload

1. Start your Flask application
2. Upload a file through the frontend
3. Check the logs for S3 messages:
   - ✅ "Successfully uploaded to S3" = S3 is working
   - ⚠️ "falling back to local storage" = Using local storage

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `AWS_ACCESS_KEY_ID` | Your AWS access key | Yes (for S3) |
| `AWS_SECRET_ACCESS_KEY` | Your AWS secret key | Yes (for S3) |
| `AWS_S3_BUCKET` | Your S3 bucket name | Yes (for S3) |
| `AWS_S3_REGION` | Your S3 bucket region | No (default: us-east-1) |

## How It Works

### Automatic Fallback
- If AWS credentials are missing or invalid, the app automatically uses local storage
- No code changes needed - it's transparent to the application
- Perfect for development without AWS setup

### File Operations
- **Upload**: Files are uploaded to S3 with proper content types
- **Download**: Presigned URLs are generated for secure file access
- **Delete**: Files are properly deleted from S3
- **Metadata**: File sizes and existence checks work with S3

### Security
- Presigned URLs expire after 24 hours (configurable)
- Files are stored with proper content types
- No direct S3 access from frontend - all through backend

## Troubleshooting

### Common Issues

#### 1. "AWS credentials not found"
- Check that your `.env` file has the correct AWS variables
- Ensure no extra spaces or quotes around values
- Restart your Flask application after changing `.env`

#### 2. "S3 bucket not found"
- Verify your bucket name is correct
- Check that the bucket exists in the specified region
- Ensure your IAM user has access to the bucket

#### 3. "Access denied to S3 bucket"
- Verify your IAM user has the `AmazonS3FullAccess` policy
- Check that your access keys are correct
- Ensure the bucket is not blocking public access (if needed)

#### 4. Files not uploading to S3
- Check the application logs for error messages
- Verify your AWS credentials are working with the test script
- Ensure your S3 bucket has proper permissions

### Debug Mode

To see detailed S3 logs, set:

```env
FLASK_DEBUG=true
```

This will show S3 connection attempts and file operations in the logs.

## Cost Considerations

### AWS S3 Pricing (as of 2024)
- **Storage**: $0.023 per GB per month
- **Requests**: $0.0004 per 1,000 GET requests
- **Data Transfer**: Free for uploads, $0.09 per GB for downloads

### Free Tier
- 5GB storage for 12 months
- 20,000 GET requests per month
- 2,000 PUT requests per month

### Cost Optimization
- Set up lifecycle policies to delete old files
- Use appropriate storage classes (Standard, IA, Glacier)
- Monitor usage with AWS Cost Explorer

## Migration from Local Storage

If you have existing files in local storage:

1. **Files will continue to work** - the app reads from local storage if S3 is not available
2. **New uploads go to S3** - once configured, new files use S3
3. **Gradual migration** - you can manually move files to S3 if needed

## Security Best Practices

1. **Never commit AWS credentials** to version control
2. **Use IAM roles** instead of access keys in production
3. **Limit S3 permissions** to only what's needed
4. **Enable S3 bucket logging** for audit trails
5. **Use bucket policies** to restrict access if needed

## Production Deployment

For production on Render:

1. Set environment variables in Render dashboard
2. Use IAM roles if possible (more secure)
3. Consider using AWS Secrets Manager for credentials
4. Set up S3 bucket logging and monitoring

## Support

If you encounter issues:

1. Check the application logs for error messages
2. Run the test script: `python setup_aws.py test`
3. Verify your AWS credentials and bucket permissions
4. Check AWS S3 console for any error messages
