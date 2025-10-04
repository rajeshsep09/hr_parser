# 📁 Folder Upload Guide

The HR Parser now supports uploading entire folders of resumes at once!

## 🚀 Quick Start

### Method 1: Using the Upload Script
```bash
python upload_folder.py <folder_path>
```

**Example:**
```bash
python upload_folder.py ./my_resumes
python upload_folder.py C:\Users\YourName\Documents\Resumes
```

### Method 2: Using the API Directly
```bash
curl -X POST "http://localhost:8080/hr/parser/bulk" \
  -F "files=@resume1.pdf" \
  -F "files=@resume2.docx" \
  -F "files=@resume3.txt"
```

## 📋 Supported File Formats

- **PDF**: `.pdf`
- **Word Documents**: `.docx`, `.doc`
- **Text Files**: `.txt`
- **Rich Text**: `.rtf`

## 📊 Features

### ✅ **Automatic Format Detection**
- Detects file types automatically
- Handles different MIME types correctly
- Supports mixed format folders

### ✅ **Robust Parsing**
- Works with various resume structures
- Handles different page counts (1-10+ pages)
- Processes different layouts and formats

### ✅ **Deduplication**
- Automatically deduplicates by phone number
- Updates existing records instead of creating duplicates
- One record per person in MongoDB

### ✅ **Batch Processing**
- Upload entire folders at once
- Process hundreds of resumes efficiently
- Detailed success/failure reporting

## 📈 Example Output

```
📁 Uploading folder: ./resumes
============================================================
📄 Found 25 resume files:
   - john_doe_engineer.pdf
   - sarah_smith_designer.docx
   - mike_wilson_analyst.txt
   - lisa_chen_manager.pdf
   ...

📡 Uploading 25 files...
📊 Response status: 200
✅ Bulk upload successful!
   Total files processed: 25
   ✅ john_doe_engineer.pdf: 0.95 confidence (ID: 68cc1807...)
   ✅ sarah_smith_designer.docx: 0.95 confidence (ID: 68cc1808...)
   ✅ mike_wilson_analyst.txt: 0.90 confidence (ID: 68cc1809...)
   ...

📊 Summary:
   ✅ Successful: 24
   ❌ Failed: 1
   👥 Unique candidates: 22
   📈 Success rate: 96.0%
```

## 🔧 Advanced Usage

### Recursive Folder Search
The upload script automatically searches subdirectories:
```
resumes/
├── engineers/
│   ├── resume1.pdf
│   └── resume2.docx
├── designers/
│   ├── resume3.pdf
│   └── resume4.txt
└── managers/
    └── resume5.docx
```

### Custom API Endpoint
```bash
python upload_folder.py ./resumes --api-url http://your-server:8080/hr/parser/bulk
```

## 🛠️ Troubleshooting

### Common Issues

1. **"No resume files found"**
   - Check file extensions (must be .pdf, .docx, .doc, .txt, .rtf)
   - Ensure files are not corrupted

2. **"Upload timed out"**
   - Try with fewer files (split large folders)
   - Check server status

3. **"Parse failed"**
   - File might be corrupted or password-protected
   - Check if file contains readable text

### Performance Tips

- **Optimal batch size**: 10-50 files per upload
- **Large folders**: Split into smaller batches
- **Network issues**: Use smaller batches for stability

## 📝 API Response Format

```json
{
  "ok": true,
  "count": 25,
  "results": [
    {
      "ok": true,
      "candidate_id": "68cc1807ee2a3d03dd4065b2",
      "parsing_confidence": 0.95
    },
    {
      "ok": false,
      "file": "corrupted.pdf",
      "error": "Parse failed: Invalid PDF format"
    }
  ]
}
```

## 🎯 Best Practices

1. **Organize your folders** by department, role, or date
2. **Use descriptive filenames** for easier tracking
3. **Check file quality** before uploading
4. **Monitor success rates** and retry failed files
5. **Keep backups** of original files

---

**Ready to upload your resume folder?** 🚀
```bash
python upload_folder.py ./your_resumes
```

