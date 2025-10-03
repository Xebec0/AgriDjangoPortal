# Farm Images & Featured Programs - Admin Guide

## Overview

Admins can now upload farm photos for agriculture programs and mark them as "featured" to display prominently on the landing page.

## ✨ New Features

### 1. **Farm Image Upload**
- Upload custom images for each agriculture program
- Images appear on the landing page and program details
- Supported formats: JPG, PNG, GIF
- Recommended size: 800x400 pixels (2:1 aspect ratio)

### 2. **Featured Programs**
- Mark programs as "featured" to prioritize them on the landing page
- Featured programs show a ⭐ Featured badge
- Up to 6 featured programs displayed on homepage
- Featured programs appear first in program lists

## 📋 How to Upload Farm Images

### Step 1: Access Admin Panel
1. Go to `/admin/`
2. Log in with admin credentials
3. Click on **"Agriculture programs"**

### Step 2: Edit/Create Program
1. Click on an existing program or **"ADD AGRICULTURE PROGRAM"**
2. Scroll to the **"Display Settings"** section
3. You'll see two fields:
   - **Image**: Upload farm photo
   - **Is featured**: Checkbox to mark as featured

### Step 3: Upload Image
1. Click **"Choose File"** next to Image field
2. Select a high-quality farm photo from your computer
3. Image will be uploaded to `media/program_images/`
4. Preview will show after upload

### Step 4: Mark as Featured (Optional)
1. Check the **"Is featured"** box
2. Program will appear on landing page with featured badge
3. Can also be toggled from the program list view

### Step 5: Save
1. Click **"Save"** or **"Save and continue editing"**
2. Image and featured status are now active

## 🎯 Best Practices

### Image Selection
- **Quality**: Use high-resolution photos (minimum 800x400px)
- **Relevance**: Show actual farm/agricultural activities
- **Branding**: Consistent style across all program images
- **Lighting**: Well-lit, clear images work best
- **Composition**: Focus on farming activities, crops, or landscapes

### Featured Programs
- **Limit**: Keep 3-6 programs featured at a time
- **Rotation**: Update featured programs regularly  
- **Priority**: Feature programs with:
  - Upcoming start dates
  - High capacity
  - Special opportunities
  - Urgent recruitment needs

### File Management
- **File Size**: Keep images under 2MB for fast loading
- **Naming**: Use descriptive names (e.g., `israel-dairy-farm.jpg`)
- **Format**: JPG for photos, PNG for graphics with transparency
- **Backup**: Keep original high-res images as backup

## 🖼️ Placeholder Images

If no image is uploaded, the system uses placeholders:

### Location-Specific Placeholders
- **Israel**: `israel-farm.jpg`
- **Japan**: `japan-farm.jpg`
- **Australia**: `australia-farm.jpg`
- **New Zealand**: `newzealand-farm.jpg`
- **Other**: `default-farm.jpg`

### Adding Custom Placeholders
1. Navigate to `static/images/placeholders/`
2. Add images with exact names above
3. System will automatically use them
4. See `/static/images/placeholders/README.md` for details

### Temporary Fallback
Until placeholder images are added, system shows:
- Dynamic placeholder with location name
- Example: "Israel Farm" on green background
- Powered by placehold.co

## 📊 Admin List View Features

### New Columns
- **Is featured**: ✓/✗ indicator (editable inline)
- **Has Image**: ✓/✗ shows if image uploaded

### Quick Actions
1. **Inline Edit Featured Status**:
   - Check/uncheck "Is featured" directly in list
   - Click "Save" at bottom of page
   - No need to open individual programs

2. **Bulk Actions**:
   - Select multiple programs
   - Available actions will show in dropdown

### Filters
- Filter by **"Is featured"** status
- Filter by **location**
- Filter by **start date**
- Combine filters for precise selection

## 🎨 How Images Appear

### Landing Page (/)
- Shows up to 6 programs (featured first)
- Images displayed at 200px height
- Maintains aspect ratio (cropped to fit)
- Featured badge appears on top-right
- "Learn More" button below image

### Program Detail Page
- Full program information
- Larger image display
- All program details visible

### Program List Page
- Thumbnail images (if implemented)
- Filterable and searchable

## 🔧 Troubleshooting

### Image Not Showing
**Problem**: Image uploaded but not displaying

**Solutions**:
1. Check file format (must be JPG, PNG, or GIF)
2. Verify file size (under 10MB)
3. Run `python manage.py collectstatic`
4. Check `MEDIA_URL` and `MEDIA_ROOT` in settings
5. Ensure media files are served correctly

### Featured Not Working
**Problem**: Program marked as featured but not on landing page

**Solutions**:
1. Verify "Is featured" checkbox is checked
2. Save the program after checking
3. Check if more than 6 programs are featured (only 6 show)
4. Clear browser cache
5. Check program has future start date

### Upload Errors
**Problem**: Cannot upload images

**Solutions**:
1. Check `media/program_images/` directory exists
2. Verify directory has write permissions
3. Check Django `MEDIA_ROOT` setting
4. Ensure `Pillow` library is installed: `pip install Pillow`

## 🚀 Quick Start Checklist

- [ ] Access admin panel at `/admin/`
- [ ] Navigate to Agriculture Programs
- [ ] Select a program to edit
- [ ] Upload a farm image (800x400px recommended)
- [ ] Check "Is featured" box
- [ ] Save the program
- [ ] Visit landing page to verify
- [ ] Repeat for 3-6 key programs

## 📝 Example Workflow

### Promoting a New Program

1. **Prepare Image**:
   - Take/download high-quality farm photo
   - Resize to 800x400px (optional but recommended)
   - Save with descriptive name

2. **Upload to Admin**:
   - Go to admin → Agriculture Programs
   - Create or edit program
   - Fill in all program details
   - Upload image in Display Settings
   - Check "Is featured"
   - Save

3. **Verify**:
   - Visit homepage (/)
   - Confirm program appears with image
   - Check featured badge is visible
   - Test "Learn More" link

4. **Rotate Featured Programs**:
   - After program starts or fills up
   - Uncheck "Is featured" 
   - Feature next upcoming program

## 🔒 Permissions

Only users with **staff status** can:
- Access admin panel
- Upload program images
- Mark programs as featured
- Edit program details

Regular users will see:
- Featured programs on landing page
- Program images throughout site
- Cannot modify content

## 📞 Support

If you encounter issues:
1. Check this guide first
2. Review error messages in admin
3. Check server logs for details
4. Contact system administrator

---

**Last Updated**: 2025-10-03  
**Feature Version**: 1.0  
**Status**: ✅ Active
