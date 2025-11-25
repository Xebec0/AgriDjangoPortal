# Candidate List - Sorting & Filtering Quick Reference

## What Was Added

### ✨ New Search Field
```
[Search by name or email...]
```
Type any candidate's:
- First name
- Last name  
- Email address

### ✨ New Gender Filter
```
[Gender: Male / Female / Other / All]
```

### ✨ New Nationality Filter
```
[Nationality: Filipino / Thai / Vietnamese / etc.]
```

### ✨ New Sort By Dropdown
```
[Sort By: Newest First / Oldest First / Name (A-Z) / etc.]
```
10 sorting options available

---

## All Available Filters

| Filter | Options | Type |
|--------|---------|------|
| Search | Any text | Text input |
| Gender | Male, Female, Other | Dropdown |
| Nationality | Filipino, Thai, Vietnamese, Swedish, Slovenian | Dropdown |
| Country | Philippines, Thailand, Vietnam, Sweden, Slovenia | Dropdown |
| Specialization | Animal science, Agronomy, Horticulture, etc. | Dropdown |
| Status | Draft, New, Approved, Rejected | Dropdown |
| Date Range | From Date → To Date | Date picker |

---

## All Sorting Options

1. **Newest First** (default) - Most recent candidates first
2. **Oldest First** - Oldest candidates first
3. **Name (A-Z)** - Alphabetical by first name
4. **Name (Z-A)** - Reverse alphabetical by first name
5. **Email (A-Z)** - Alphabetical by email
6. **Email (Z-A)** - Reverse alphabetical by email
7. **Gender** - Group by gender
8. **Country** - Group by country of birth
9. **Nationality** - Group by nationality
10. **Status** - Group by approval status

---

## Common Use Cases

### Find a Specific Person
```
Search: [type their name or email]
Click: Search & Filter
```

### Find All Males from Thailand
```
Gender: Male
Country: Thailand
Click: Search & Filter
```

### Find All Approved Horticulture Candidates
```
Specialization: Horticulture
Status: Approved
Sort By: Name (A-Z)
Click: Search & Filter
```

### Find Filipino Applicants Added in October
```
Nationality: Filipino
Date Range: Oct 1 - Oct 31
Sort By: Newest First
Click: Search & Filter
```

### Clear All Filters
```
Click: Reset
```

---

## Layout

```
┌────────────────────────────────────────────────────────┐
│ [Search by name or email..........................]    │
└────────────────────────────────────────────────────────┘

┌──────┬──────────┬────────┬──────────────┬────────┬──────────┐
│Country│Nationality│Gender│Specialization│ Status │ Sort By  │
└──────┴──────────┴────────┴──────────────┴────────┴──────────┘

┌──────────────────────────────────────┬─────────────────┐
│ Date Range [calendar icon]           │[Search & Filter]│
└──────────────────────────────────────┴─────────────────┘
[Reset]
```

---

## Tips

✅ **Combine Filters**
- Use multiple filters at once
- All filters work together
- More specific = fewer results

✅ **Search Tips**
- Search is case-insensitive
- Works with partial names (e.g., "john" finds "Johnny")
- Works with partial emails (e.g., "gmail" finds all Gmail addresses)

✅ **Sorting Tips**
- Sort options apply to filtered results
- Can sort by name even with other filters active
- Default sort is "Newest First"

✅ **Resetting**
- Click "Reset" to clear ALL filters at once
- Or refresh the page

✅ **Exporting**
- Export works with filtered results
- Exported file contains only visible candidates
- Choose CSV, Excel, or PDF format

---

## Keyboard Shortcuts (Optional)

- **Alt + S** - Focus search field
- **Enter** - Submit form (when in any filter field)
- **Escape** - Close any open dropdown

---

## Browser Support

Works on:
- Chrome/Chromium
- Firefox
- Safari
- Edge
- Mobile browsers

---

## Staff Only Feature

⚠️ **Note:** These filtering features are only available to staff members. Regular users can only see their own candidates.

---

## Customization

### Add More Countries
Edit: `core/forms.py` (line ~730)

### Add More Nationalities  
Edit: `core/forms.py` (line ~738)

### Add More Specializations
Edit: `core/forms.py` (line ~748)

### Add More Sort Options
Edit: `core/forms.py` (SORT_CHOICES, line ~697)

---

## Troubleshooting

**Search not working?**
- Make sure you're searching for an actual candidate
- Check spelling
- Try searching by different name/email

**Filters appear but nothing selected?**
- Click on the dropdown to open it
- Select an option

**Results not changing after filtering?**
- Make sure form was submitted (look at URL)
- Click "Search & Filter" button
- Try "Reset" and filter again

**Date picker not opening?**
- Click the calendar icon next to date field
- Check if popup is blocked by browser

---

## What Each Field Does

| Field | Does What | Example |
|-------|-----------|---------|
| Search | Finds candidates by name/email | Type "John" |
| Gender | Shows only candidates of that gender | Select "Male" |
| Nationality | Shows only that nationality | Select "Filipino" |
| Country | Shows only that country of birth | Select "Philippines" |
| Specialization | Shows only that field of study | Select "Agronomy" |
| Status | Shows only that approval status | Select "Approved" |
| Date Range | Shows candidates added between dates | Pick Oct 1-31 |
| Sort By | Orders the results | Select "Name (A-Z)" |

---

## Performance Notes

- All 91 candidates can be searched/filtered instantly
- No lag when selecting filters
- Export works fast even with all 91 candidates
- Pagination shows 15 candidates per page

---

## Version Info

- **Created:** November 25, 2025
- **Status:** Production Ready ✅
- **Tested:** Yes
- **Mobile Responsive:** Yes
- **Security:** Staff only

---

## Support

For detailed information, see:
- `FILTERING_FEATURES_GUIDE.md` - Complete feature guide
- `SORTING_FILTERING_SUMMARY.md` - Before/after comparison

---

**You're ready to use the new filtering and sorting features!** 🎉
