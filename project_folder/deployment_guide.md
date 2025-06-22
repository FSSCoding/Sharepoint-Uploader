# Deployment Guide - Report

**Original Report Date:** 6/18/2025
**Project Phase:** Deployment

## 1. Executive Summary

This guide covers deploying the SharePoint Uploader CLI in production environments.

## 📋 Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **Operating System**: Windows, Linux, or macOS
- **Memory**: Minimum 512MB RAM
- **Storage**: 100MB for application + space for temporary files during upload
- **Network**: Internet access for Microsoft Graph API

### Microsoft Graph Prerequisites
- **Azure AD Application** with appropriate permissions
- **SharePoint Site** with upload permissions
- **Client Credentials** (Client ID, Client Secret, Tenant ID)

## 🔐 Security Configuration

### 1. Environment Variables (Recommended)
Instead of storing credentials in `config.json`, use environment variables:

```bash
# Create .env file (copy from env_template.txt)
cp env_template.txt .env

# Edit .env with your actual values
TENANT_ID=your-actual-tenant-id
CLIENT_ID=your-actual-client-id
CLIENT_SECRET=your-actual-client-secret
SITE_ID=your-actual-site-id
DRIVE_ID=your-actual-drive-id
```

### 2. File Permissions
```bash
# Secure the configuration files
chmod 600 config.json
chmod 600 .env
```

### 3. Credential Management
- **Never commit credentials to version control**
- **Use Azure Key Vault for business deployments**
- **Rotate client secrets regularly**
- **Use managed identities when possible**

## 🏗️ Installation Methods

### Method 1: Direct Installation
```bash
# Clone the repository
git clone <repository-url>
cd sharepoint-uploader

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Configure credentials
cp config.json.example config.json
# Edit config.json with your values
```

### Method 2: Docker Deployment
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

ENTRYPOINT ["python", "main.py"]
```

```bash
# Build and run
docker build -t sharepoint-uploader .
docker run -v /local/files:/app/uploads sharepoint-uploader --upload-only /app/uploads/file.txt
```

### Method 3: Systemd Service (Linux)
```ini
# /etc/systemd/system/sharepoint-uploader.service
[Unit]
Description=SharePoint Uploader CLI
After=network.target

[Service]
Type=oneshot
User=sharepoint
WorkingDirectory=/opt/sharepoint-uploader
ExecStart=/opt/sharepoint-uploader/venv/bin/python main.py
EnvironmentFile=/opt/sharepoint-uploader/.env

[Install]
WantedBy=multi-user.target
```

## 🔧 Configuration Management

### Production Config Structure
```json
{
  "TENANT_ID": "${TENANT_ID}",
  "CLIENT_ID": "${CLIENT_ID}",
  "CLIENT_SECRET": "${CLIENT_SECRET}",
  "SITE_ID": "${SITE_ID}",
  "DRIVE_ID": "${DRIVE_ID}",
  "SHAREPOINT_HOST": "graph.microsoft.com",
  "SCOPES": "https://graph.microsoft.com/.default",
  "UPLOAD_CHUNK_SIZE": 4194304,
  "MAX_RETRIES": 3,
  "RETRY_DELAY": 1
}
```

### Environment-Specific Configs
```bash
# Development
config.dev.json

# Staging
config.staging.json

# Production
config.prod.json
```

## 📊 Monitoring and Logging

### 1. Application Logging
```python
# Add to main.py for production logging
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/sharepoint-uploader.log'),
        logging.StreamHandler()
    ]
)
```

### 2. Health Checks
```bash
# Create health check script
#!/bin/bash
python test_live_auth.py > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "SharePoint Uploader: HEALTHY"
    exit 0
else
    echo "SharePoint Uploader: UNHEALTHY"
    exit 1
fi
```

### 3. Metrics Collection
- **Upload Success Rate**: Track successful vs failed uploads
- **Upload Duration**: Monitor upload performance
- **Error Rates**: Track authentication and network errors
- **File Sizes**: Monitor typical file sizes being uploaded

## 🔄 Backup and Recovery

### 1. State File Management
```bash
# Backup upload state files
find /app/data -name "*.state.json" -exec cp {} /backup/states/ \;

# Clean up old state files
find /app/data -name "*.state.json" -mtime +7 -delete
```

### 2. Configuration Backup
```bash
# Backup configurations (without secrets)
cp config.json /backup/config.json.backup
```

## 🚨 Troubleshooting

### Common Issues

#### Authentication Failures
```bash
# Test authentication
python test_live_auth.py

# Check token expiration
# Tokens expire after 1 hour, application handles refresh automatically
```

#### Upload Failures
```bash
# Check network connectivity
curl -I https://graph.microsoft.com

# Test with small file first
python main.py --upload-only small-test.txt

# Check SharePoint permissions
# Ensure application has Files.ReadWrite.All permission
```

#### Performance Issues
```bash
# Monitor system resources
top -p $(pgrep -f "python main.py")

# Check disk space for temporary files
df -h /tmp

# Monitor network bandwidth
iftop -i eth0
```

## 📈 Performance Optimization

### 1. Chunk Size Tuning
```json
{
  "UPLOAD_CHUNK_SIZE": 8388608  // 8MB for faster networks
}
```

### 2. Parallel Uploads
For multiple files, consider running parallel instances:
```bash
# Upload multiple files in parallel
python main.py --upload-only file1.txt &
python main.py --upload-only file2.txt &
python main.py --upload-only file3.txt &
wait
```

### 3. Compression Optimization
```bash
# Use maximum compression for large files
python main.py --compress --compression-level 9 --upload-to-sharepoint
```

## 🔒 Security Best Practices

### 1. Access Control
- **Principle of Least Privilege**: Grant minimum required permissions
- **Regular Access Reviews**: Audit who has access to credentials
- **Multi-Factor Authentication**: Enable MFA for admin accounts

### 2. Network Security
- **TLS Encryption**: All communication uses HTTPS
- **Firewall Rules**: Restrict outbound connections to Microsoft Graph endpoints
- **VPN Access**: Consider VPN for sensitive uploads

### 3. Audit Logging
```python
# Enhanced logging for security events
import logging
import json

security_logger = logging.getLogger('security')
security_logger.info(json.dumps({
    'event': 'upload_started',
    'user': os.getenv('USER'),
    'file': file_path,
    'timestamp': datetime.utcnow().isoformat()
}))
```

## 📋 Maintenance Tasks

### Daily
- [ ] Check upload logs for errors
- [ ] Monitor disk space for temporary files
- [ ] Verify service health

### Weekly
- [ ] Review upload statistics
- [ ] Clean up old state files
- [ ] Update dependencies if needed

### Monthly
- [ ] Rotate client secrets
- [ ] Review access permissions
- [ ] Performance analysis
- [ ] Backup configuration

## 🆘 Emergency Procedures

### Service Down
1. Check authentication: `python test_live_auth.py`
2. Check network connectivity to Microsoft Graph
3. Verify SharePoint service status
4. Check application logs
5. Restart service if needed

### Data Recovery
1. Check for interrupted uploads: `find . -name "*.state.json"`
2. Resume interrupted uploads: `python main.py --upload-only <file>`
3. Verify file integrity after upload

## 📞 Support Contacts

- **Microsoft Graph API Status**: https://status.graph.microsoft.com/
- **SharePoint Service Health**: Microsoft 365 Admin Center
- **Application Logs**: `/var/log/sharepoint-uploader.log`

---

**Your SharePoint Uploader CLI is production-ready!** Follow this guide for secure, reliable deployment in any environment. 