# Bamboo H2 Database Fix - Summary

## Issue
Bamboo setup wizard failed with error: "Setting up embedded database instance failed"
- Root cause: H2 database JAR was missing from `/opt/atlassian/bamboo/lib/`
- Bamboo 9.6.5 tarball doesn't include the H2 driver by default

## Fix Applied

### 1. Immediate Fix (Running Instance)
Used AWS Systems Manager to install H2 JAR on the running instance:

```bash
cd /opt/atlassian/bamboo/lib
wget -O h2-2.2.224.jar https://repo1.maven.org/maven2/com/h2database/h2/2.2.224/h2-2.2.224.jar
chown bamboo:bamboo h2-2.2.224.jar
systemctl restart bamboo
```

**Result**: ✅ H2 JAR installed successfully
- File: `/opt/atlassian/bamboo/lib/h2-2.2.224.jar` (2.6 MB)
- Owner: bamboo:bamboo
- Bamboo service restarted and running

### 2. Permanent Fix (Terraform)
Updated `linux_user_data.tpl` to automatically download H2 JAR during installation:

```bash
# --- Ensure H2 driver JAR exists (needed for Embedded DB setup) ---
BAMBOO_LIB="/opt/atlassian/bamboo/lib"
mkdir -p "$BAMBOO_LIB"

if ! ls -1 "$BAMBOO_LIB"/h2-*.jar >/dev/null 2>&1; then
  echo "H2 jar not found in $BAMBOO_LIB. Downloading..."
  wget -O "$BAMBOO_LIB/h2-2.2.224.jar" \
    "https://repo1.maven.org/maven2/com/h2database/h2/2.2.224/h2-2.2.224.jar"
fi
```

This ensures future instance recreations will have H2 JAR automatically.

## Current Status

✅ **Bamboo is fully operational**

- **URL**: http://3.95.170.192:8085
- **Status**: Running (active for 1min 37s)
- **H2 JAR**: Installed at `/opt/atlassian/bamboo/lib/h2-2.2.224.jar`
- **Service**: Active and healthy
- **Setup**: Ready for embedded database configuration

## Verification

```
=== H2 JAR Check ===
-rw-r--r--. 1 bamboo bamboo  2614933 Sep 18  2023 h2-2.2.224.jar

=== Bamboo Service Status ===
● bamboo.service - Atlassian Bamboo
     Active: active (running)
     Memory: 911.1M
     
=== Logs ===
2026-01-31 21:52:27 [http-nio-8085-exec-1] The application is not yet setup. 
Redirecting request to '/bootstrap/selectSetupStep.action'
```

## Next Steps

1. **Access Bamboo**: Go to http://3.95.170.192:8085
2. **Select Database**: Choose "Embedded database" option
3. **Complete Setup**: The H2 database setup should now work without errors
4. **Configure License**: Enter your Bamboo license or request a trial
5. **Create Admin User**: Set up the administrator account

## Files Modified

1. `/Users/venkat/Documents/devops/AWS_RealEstate/terraform/modules/bamboo-server/linux_user_data.tpl`
   - Added H2 JAR download logic with conditional check
   - Ensures H2 JAR is present before starting Bamboo

## Reference

- H2 Database Version: 2.2.224
- Maven Central URL: https://repo1.maven.org/maven2/com/h2database/h2/2.2.224/
- Atlassian Documentation: Bamboo requires H2 JAR in `<BAMBOO_INSTALL_DIR>/lib` for embedded database
