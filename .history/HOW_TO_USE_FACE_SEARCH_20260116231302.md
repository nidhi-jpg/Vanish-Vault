# How to Use AI Face Search - User Guide

## Quick Start

The AI Face Search feature allows you to upload any image (photo, sketch, or pixelated image) and find matching faces in the VanishVault database.

## Step-by-Step Instructions

### 1. Access Face Search Page

- Navigate to the **Face Search** page in your VanishVault application
- URL: `/face-search/` (or click "Search by Photo" in the navigation)

### 2. Upload an Image

**Option A: Click to Upload**
1. Click the **"Choose Image"** button
2. Select an image file from your computer
3. Supported formats: JPG, PNG (Max 5MB)

**Option B: Drag and Drop**
1. Drag an image file from your computer
2. Drop it into the upload area
3. The image will be automatically loaded

**What Images Work Best:**
- ✅ Clear photos with visible faces
- ✅ Sketches or drawings of faces
- ✅ Pixelated or low-quality images (AI will try to enhance them)
- ✅ Front-facing photos work best
- ⚠️ Side profiles may have lower accuracy

### 3. Review Uploaded Image

- The uploaded image will appear in the preview area
- Check that a face is clearly visible
- You can click **"Remove"** to try a different image

### 4. Configure Search Settings

**Search In:**
- **Both Missing & Found Persons** (default) - Searches all databases
- **Missing Persons Only** - Only searches missing person reports
- **Found Persons Only** - Only searches unidentified found persons

**Match Sensitivity:**
- **Medium - Recommended** (default: 60% confidence)
  - Good balance between results and accuracy
  - Best for most searches
  
- **High - More Strict** (80% confidence)
  - Fewer results, but higher accuracy
  - Use when you want only very strong matches
  
- **Low - More Results** (40% confidence)
  - More potential matches, but may include false positives
  - Use when you want to see all possible matches

### 5. Start the Search

1. Click the **"Search Database"** button
2. Wait while the AI processes your image:
   - **Step 1**: Uploading image (20%)
   - **Step 2**: Detecting faces (40%)
   - **Step 3**: Searching database (80%)
   - **Step 4**: Analyzing results (100%)

### 6. Review Results

**Results Display:**
- Number of matches found (shown in badge)
- AI model used (DeepFace/Face Recognition)
- List of potential matches sorted by confidence

**Each Match Shows:**
- **Thumbnail Photo** - Database photo
- **Name** - Person's name or case identifier
- **Confidence Score** - Match percentage (higher = more similar)
- **Case ID** - Unique case identifier
- **Age** - Person's age
- **Gender** - Person's gender
- **Location** - Last seen or found location
- **Date** - Relevant date

**Confidence Badge Colors:**
- 🟢 **Green (80%+)**: Very strong match
- 🟡 **Yellow (60-79%)**: Good match
- 🔴 **Red (40-59%)**: Possible match

### 7. Take Action

**View Details:**
- Click **"View Details"** to see full case information
- Compare uploaded photo with database photo side-by-side

**Report Sighting** (for missing persons):
- Click **"Report Sighting"** if you believe you've found a match
- Fill out the sighting report form

## Tips for Best Results

### ✅ Do's

1. **Use Clear Images**
   - Well-lit photos work best
   - Front-facing is ideal
   - Face should be clearly visible

2. **Try Different Angles**
   - If no matches, try a different photo of the same person
   - Different angles may yield better results

3. **Adjust Sensitivity**
   - Start with Medium sensitivity
   - If too many results, try High
   - If no results, try Low

4. **Use Recent Photos**
   - Photos closer to the time of disappearance work better
   - Age differences can affect matching

### ❌ Don'ts

1. **Don't Use Extremely Blurry Images**
   - Very blurry images may not detect faces
   - AI needs some facial features to work with

2. **Don't Use Images Without Faces**
   - The system requires a detectable face
   - Full body shots may not work if face is too small

3. **Don't Expect 100% Accuracy**
   - AI matching is probabilistic
   - Always verify matches manually
   - Use results as leads, not definitive matches

## Understanding Results

### Confidence Scores

- **85-100%**: Very strong match, high likelihood
- **70-84%**: Strong match, worth investigating
- **60-69%**: Good match, possible connection
- **40-59%**: Weak match, may be coincidental
- **Below 40%**: Usually filtered out (unless using Low sensitivity)

### What to Do with Results

1. **High Confidence (80%+)**
   - Review case details carefully
   - Compare photos side-by-side
   - Report if confident it's a match

2. **Medium Confidence (60-79%)**
   - Review additional case information
   - Check age, location, and other details
   - Consider reporting if other details match

3. **Low Confidence (40-59%)**
   - Use as a starting point for investigation
   - Verify with other identifying information
   - Don't rely solely on face match

## Troubleshooting

### "No face detected" Error

**Possible Causes:**
- Image doesn't contain a clear face
- Face is too small or obscured
- Image quality is too low

**Solutions:**
- Try a different photo with clearer face
- Ensure face is front-facing and well-lit
- Crop image to focus on face area
- Try enhancing image quality

### No Matches Found

**Possible Causes:**
- Person not in database
- Sensitivity threshold too high
- Image quality issues
- Significant age difference

**Solutions:**
- Lower sensitivity to "Low - More Results"
- Try different photos of the same person
- Check if person might be in different category (missing vs found)
- Verify person is actually in the database

### Slow Processing

**Normal:**
- First search may be slower (loading AI models)
- Large databases take longer to search
- Complex images take more processing time

**If Too Slow:**
- Reduce image size before uploading
- Check internet connection
- Try during off-peak hours

## Privacy & Security

- ✅ Your uploaded image is **NOT stored** on the server
- ✅ Image is processed temporarily and then deleted
- ✅ Face encodings are computed on-the-fly
- ✅ No personal information is exposed
- ✅ All processing happens securely server-side

## Example Use Cases

### Case 1: Finding a Missing Person
1. Upload a recent photo of the missing person
2. Select "Missing Persons Only"
3. Use Medium sensitivity
4. Review high-confidence matches
5. Report any potential matches

### Case 2: Identifying Found Person
1. Upload photo of unidentified person
2. Select "Found Persons Only"
3. Use Low sensitivity to see all possibilities
4. Compare with missing person reports
5. Contact authorities if match found

### Case 3: Cross-Reference Search
1. Upload sketch or pixelated image
2. Select "Both Missing & Found Persons"
3. Use Medium sensitivity
4. Review all matches across both databases
5. Investigate promising leads

## Need Help?

If you encounter issues:
1. Check the troubleshooting section above
2. Try different images or settings
3. Contact support if problems persist
4. Review the AI Face Matching Guide for technical details

## Quick Reference

| Action | Location |
|--------|----------|
| Upload Image | Click "Choose Image" or drag & drop |
| Change Settings | Use dropdowns in "Search Settings" |
| Start Search | Click "Search Database" button |
| View Details | Click "View Details" on any match |
| Report Match | Click "Report Sighting" button |
| Try Again | Click "Remove" then upload new image |

---

**Remember**: AI face matching is a tool to help identify potential matches. Always verify results manually and use additional information (age, location, date) to confirm matches before taking action.

