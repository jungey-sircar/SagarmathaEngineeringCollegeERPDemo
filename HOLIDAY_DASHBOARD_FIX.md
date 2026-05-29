# HOD Dashboard - Holiday Display Fix

## Issues Found and Fixed

### 1. **Hardcoded Date Range** ❌ → ✅
**Problem:** The holiday period title was hardcoded as "Holidays from 2026/04/01 to 2026/12/31"

**Solution:** Changed to use dynamic `holiday_period_label` variable:
```html
<!-- Before -->
<div class="panel-title">Holidays from 2026/04/01 to 2026/12/31</div>

<!-- After -->
<div class="panel-title">{{ holiday_period_label|default:'Holidays' }}</div>
```

This now correctly shows the actual year range (e.g., "Holidays from 2082/04/01 to 2083/03/32")

---

### 2. **Non-functional Tab Switching** ❌ → ✅
**Problem:** The "Holidays" and "Optional Holidays" tabs had no functionality

**Solution:** Added Bootstrap tab attributes (`data-bs-toggle` and `data-bs-target`):
```html
<!-- Before -->
<button class="active" type="button">Holidays</button>
<button type="button">Optional Holidays</button>

<!-- After -->
<button class="active" type="button" data-bs-toggle="tab" data-bs-target="#hod-holidays">Holidays</button>
<button type="button" data-bs-toggle="tab" data-bs-target="#hod-optional-holidays">Optional Holidays</button>
```

---

### 3. **Date and Holiday Name Not Side by Side** ❌ → ✅
**Problem:** Columns were ordered as: #, Name, From, To, Remarks

**Solution:** Reorganized to: #, Date, Holiday Name, Remarks
```html
<!-- Before -->
<th>Name</th>
<th>From</th>
<th>To</th>
<th>Remarks</th>

<!-- After -->
<th>Date</th>
<th>Holiday Name</th>
<th>Remarks</th>
```

Now calendar date (2082/04/01) and holiday name display side by side as intended.

---

### 4. **Missing Optional Holidays Tab Content** ❌ → ✅
**Problem:** The Optional Holidays tab was declared but had no content

**Solution:** Added complete Optional Holidays table with:
- Date, Holiday Name, Remarks columns
- **"Apply" button** that links to the staff leave application page
- Proper empty state message

```html
<div class="tab-pane fade" id="hod-optional-holidays">
    <table class="dashboard-table">
        <thead>
            <tr>
                <th>#</th>
                <th>Date</th>
                <th>Holiday Name</th>
                <th>Remarks</th>
                <th>Action</th>
            </tr>
        </thead>
        <tbody>
            {% for row in optional_holiday_rows %}
            <tr>
                <td>{{ forloop.counter }}</td>
                <td>{{ row.from }}</td>
                <td>{{ row.name }}</td>
                <td>{{ row.remarks }}</td>
                <td>
                    <a href="{% url 'staff_apply_leave' %}" class="btn btn-sm btn-outline-primary">Apply</a>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
```

---

## File Modified
- **Path:** `main_app/templates/hod_template/erpnext_home_content.html`
- **Lines Changed:** 392-423

---

## Testing Steps

1. **Visit HOD Dashboard**: Navigate to the admin/HOD dashboard
2. **Verify Holiday Period Label**: Should show current year range (e.g., "BS 2082 to 2083 holiday schedule")
3. **Test Holidays Tab**: Should show all holidays with Date | Holiday Name | Remarks columns
4. **Test Optional Holidays Tab**: Click the "Optional Holidays" tab to see optional holidays
5. **Test Apply Button**: Click "Apply" button to ensure it navigates to leave application page

---

## Expected Display

### Holidays Tab
```
#  | Date       | Holiday Name              | Remarks
1  | 2082/04/25 | Gai Jatra (गाई जात्रा)   | -
2  | 2082/04/31 | Krishna Janma (कृष्ण जन्म)| -
```

### Optional Holidays Tab
```
#  | Date       | Holiday Name              | Remarks | Action
1  | 2082/05/07 | Father's Day             | -       | [Apply]
2  | 2082/05/10 | TEEJ (तीज)              | -       | [Apply]
```

---

## Notes
- The Apply button currently directs to `staff_apply_leave` URL
- Holiday data comes from `get_nepali_holiday_dashboard_data()` function in `holiday_service.py`
- The system supports both live calendar and artifact-based data sources
- Optional holidays are automatically classified based on specific keywords and exact names

