# Auto Attendance Check-in/Check-out for Odoo 19

## Quick Overview
This module automatically creates HR attendance check-in records when users log into Odoo and check-out records when they log out.

## Features
- ✅ Automatic check-in on user login
- ✅ Automatic check-out on user logout  
- ✅ Prevents duplicate check-ins
- ✅ Only works for users with linked employee records
- ✅ Full logging for debugging

## Requirements
- Odoo 19
- Module `hr_attendance` must be installed
- Users must have an employee record linked to their user account

## Quick Installation

1. **Copy the module** to your Odoo addons directory:
   ```bash
   cp -r auto_attendance_checkin /path/to/odoo/addons/
   ```

2. **Restart Odoo** (if needed after updating addons path)

3. **Enable Developer Mode** in Odoo Settings

4. **Update Apps List** (Apps > Update Apps List)

5. **Install the module** (Apps > search "Auto Attendance Check-in/Check-out" > Install)

## Configuration

Link each user to an employee:
1. Go to **Employees** > **Employees**
2. Open an employee record
3. Set **Related User** field to the user
4. Save

## Testing

1. **Test Check-in:**
   - Log out from Odoo
   - Log back in
   - Check **Employees** > **Attendance** - should see new check-in record

2. **Test Check-out:**
   - Log out from Odoo
   - Check **Employees** > **Attendance** - last record should have check-out time

## File Structure
```
auto_attendance_checkin/
├── __manifest__.py          # Module manifest
├── __init__.py
├── README.md                # This file
├── IMPLEMENTATION_GUIDE.md  # Detailed guide
├── controllers/
│   ├── __init__.py
│   └── main.py             # Logout handler
├── models/
│   ├── __init__.py
│   ├── res_users.py        # Login handler
│   └── ir_http.py          # Alternative session handler
└── security/
    └── ir.model.access.csv  # Access rules
```

## Key Files

- **`models/res_users.py`**: Handles check-in on login by overriding `_check_credentials()`
- **`controllers/main.py`**: Handles check-out on logout by overriding logout routes
- **`__manifest__.py`**: Module metadata and dependencies

## Troubleshooting

**Attendance not created?**
- Verify user has linked employee record
- Check Odoo logs for errors
- Ensure `hr_attendance` module is installed

**Module not appearing?**
- Check addons path includes module directory
- Click "Update Apps List" in Apps menu
- Check file permissions

See **IMPLEMENTATION_GUIDE.md** for detailed troubleshooting.

## License
AGPL-3

