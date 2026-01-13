# Auto Attendance Check-in/Check-out Module - Implementation Guide

## Overview
This module automatically creates attendance check-in records when users log into Odoo 19 and check-out records when they log out. It integrates with the standard Odoo HR Attendance module.

---

## Prerequisites

### 1. Required Odoo Modules
Make sure the following modules are installed in your Odoo 19 instance:
- **base** (core module - always installed)
- **hr** (Human Resources)
- **hr_attendance** (HR Attendance)

### 2. User Setup
- Each user must have an **employee record** linked to their user account
- To link an employee to a user:
  1. Go to **Employees** app
  2. Open an employee record
  3. In the "Contact Information" section, set the "Related User" field to the desired user

---

## Step-by-Step Installation Guide

### Step 1: Copy Module to Odoo Addons Directory

```bash
# Option 1: If using a custom addons directory
cp -r /home/am99/Documents/auto_attendance_checkin /path/to/your/odoo/addons/

# Option 2: Copy to Odoo's standard addons path (if you have access)
# Adjust the path according to your Odoo installation
cp -r /home/am99/Documents/auto_attendance_checkin /usr/lib/python3/dist-packages/odoo/addons/

# Option 3: If using Odoo.sh or custom server setup
# Upload the module folder to your custom addons directory
```

**Note:** Make sure the directory is readable by the Odoo process user (usually `odoo` or `www-data`).

### Step 2: Update Addons Path in Odoo Configuration

1. Locate your Odoo configuration file (usually `/etc/odoo/odoo.conf` or `~/.odoorc`)

2. Ensure your addons path includes the directory containing this module:
   ```ini
   [options]
   addons_path = /usr/lib/python3/dist-packages/odoo/addons,/path/to/your/custom/addons
   ```

3. If you modified the config file, restart Odoo:
   ```bash
   sudo systemctl restart odoo
   # OR
   sudo service odoo restart
   ```

### Step 3: Enable Developer Mode

1. Log into Odoo as an Administrator
2. Go to **Settings**
3. Activate **Developer Mode**:
   - Scroll to the bottom of the Settings page
   - Click **Activate Developer Mode**
   - Or use URL parameter: `/web?debug=1`

### Step 4: Update Apps List

1. Go to **Apps** menu
2. Click **Update Apps List** button (top right)
3. Remove filters (if any) to see all apps

### Step 5: Install the Module

1. In the **Apps** menu, remove the "Apps" filter
2. Search for **"Auto Attendance Check-in/Check-out"**
3. Click on the module
4. Click **Install** button

### Step 6: Verify Installation

1. Go to **Employees** > **Attendance**
2. Log out and log back in
3. Check if a new attendance record was created with check-in time

---

## Configuration

### Linking Users to Employees

Before the module can work, each user must be linked to an employee:

1. Navigate to **Employees** > **Employees**
2. Open an employee record
3. In the **Contact Information** section:
   - Find the **Related User** field
   - Select the user that should be linked to this employee
4. Save the record

**Important:** If a user logs in but has no linked employee record, the module will skip creating attendance and log an info message (no error will be shown to the user).

### Testing the Module

1. **Test Check-in:**
   - Log out from Odoo
   - Log back in
   - Go to **Employees** > **Attendance**
   - Verify a new attendance record exists with check-in time matching your login time

2. **Test Check-out:**
   - Log out from Odoo
   - Go to **Employees** > **Attendance**
   - Verify the last attendance record now has a check-out time matching your logout time

---

## How It Works

### Check-in (Login)
- When a user logs in, the module:
  1. Checks if the user has a linked employee record
  2. Verifies there's no active check-in (without check-out) for today
  3. Creates a new attendance record with check-in time = current datetime

### Check-out (Logout)
- When a user logs out, the module:
  1. Checks if the user has a linked employee record
  2. Finds the latest attendance record without check-out
  3. Updates that record with check-out time = current datetime

---

## Troubleshooting

### Issue: Module not appearing in Apps list

**Solution:**
- Verify the module is in a directory included in `addons_path`
- Check file permissions (should be readable by Odoo user)
- Click **Update Apps List** in Apps menu
- Check Odoo logs for any import errors

### Issue: Attendance not being created on login

**Possible Causes:**
1. User has no linked employee record
   - **Solution:** Link employee to user (see Configuration section)
   
2. Employee already has an active check-in
   - **Solution:** This is expected behavior - the module prevents duplicate check-ins
   - Manually check out the existing attendance first

3. Module not installed correctly
   - **Solution:** Uninstall and reinstall the module

### Issue: Check-out not working on logout

**Possible Causes:**
1. No active check-in exists for the employee
   - **Solution:** This is expected if there's no check-in to check out
   
2. User has no linked employee record
   - **Solution:** Link employee to user

### Issue: Permission errors

**Solution:**
- Ensure the Odoo user has read/write permissions on the module directory
- Check security access rules are properly installed (should be automatic)

### Viewing Logs

To debug issues, check Odoo logs:

```bash
# For systemd-based installations
sudo journalctl -u odoo -f

# For service-based installations
sudo tail -f /var/log/odoo/odoo-server.log

# For development mode
# Logs appear in the terminal where Odoo is running
```

Look for log messages containing:
- "Automatic check-in created for employee"
- "Automatic check-out created for employee"
- "Error creating automatic check-in"
- "User has no linked employee record"

---

## Technical Details

### Files Structure
```
auto_attendance_checkin/
├── __init__.py
├── __manifest__.py
├── controllers/
│   ├── __init__.py
│   └── main.py          # Handles logout check-out
├── models/
│   ├── __init__.py
│   └── res_users.py     # Handles login check-in
├── security/
│   └── ir.model.access.csv
└── IMPLEMENTATION_GUIDE.md
```

### Key Methods

1. **`res.users._check_credentials()`**
   - Overridden to intercept login
   - Calls `_auto_checkin_attendance()` after successful authentication

2. **`res.users._auto_checkin_attendance()`**
   - Finds employee linked to user
   - Creates attendance check-in record
   - Prevents duplicate check-ins

3. **`/web/session/logout` route**
   - Overridden HTTP controller route
   - Creates check-out before logout
   - Redirects to login page

---

## Customization Options

### Skip Check-in for Specific Users

Edit `models/res_users.py` and add a condition:

```python
def _auto_checkin_attendance(self):
    # Skip check-in for specific users
    if self.login == 'specific_user@example.com':
        return
    # ... rest of the code
```

### Add Custom Logic

You can extend the module by:
- Adding notifications on check-in/check-out
- Integrating with other modules
- Adding location tracking
- Adding IP address logging

---

## Support

For issues or questions:
1. Check Odoo logs for error messages
2. Verify all prerequisites are met
3. Ensure users are properly linked to employees
4. Review this guide's troubleshooting section

---

## License

AGPL-3 License - Free to use and modify.

