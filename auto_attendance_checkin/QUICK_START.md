# Quick Start Guide - Auto Attendance Check-in/Check-out

## Installation Steps (5 minutes)

### 1. Copy Module to Odoo
```bash
cp -r auto_attendance_checkin /path/to/your/odoo/addons/
```

### 2. Restart Odoo
```bash
sudo systemctl restart odoo
# OR restart your Odoo service
```

### 3. Install in Odoo
1. Login to Odoo as Administrator
2. Go to **Apps** menu
3. Enable **Developer Mode** (Settings > Activate Developer Mode)
4. Click **Update Apps List**
5. Search for **"Auto Attendance Check-in/Check-out"**
6. Click **Install**

### 4. Link Users to Employees
1. Go to **Employees** > **Employees**
2. Open an employee
3. Set **Related User** field
4. Save

## Done! ✅

Now every time a user logs in, they'll automatically check in.
When they log out, they'll automatically check out.

## Verify It Works

1. **Test Check-in:**
   - Log out
   - Log back in
   - Go to **Employees** > **Attendance**
   - You should see a new check-in record

2. **Test Check-out:**
   - Log out
   - Go to **Employees** > **Attendance**
   - Last record should have check-out time

## Troubleshooting

**No attendance created?**
- User must have linked employee record
- Check Odoo logs: `sudo journalctl -u odoo -f`

**Module not appearing?**
- Check addons path includes module directory
- Click "Update Apps List" in Apps menu

See `IMPLEMENTATION_GUIDE.md` for detailed troubleshooting.

