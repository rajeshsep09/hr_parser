# 🌐 Web Interface Guide

## 🚀 Quick Start

1. **Start the server** (if not already running):
   ```bash
   python -m uvicorn app.main:app --reload --port 8080
   ```

2. **Open your browser** and go to:
   ```
   http://localhost:8080/
   ```

3. **Upload resumes** using one of these methods:
   - **Drag & Drop**: Drag your resume folder directly onto the upload area
   - **Click to Browse**: Click "Choose Folder" to select a folder
   - **Individual Files**: Select multiple files at once

## ✨ Features

### 🎯 **Drag & Drop Interface**
- **Drag entire folders** directly onto the upload area
- **Visual feedback** when dragging files over the area
- **Automatic file filtering** for supported formats

### 📁 **Folder Upload**
- **Recursive folder scanning** (includes subfolders)
- **Multiple file format support** (PDF, DOCX, DOC, TXT, RTF)
- **File size display** for each selected file

### 📊 **Real-time Progress**
- **Upload progress bar** with percentage
- **Live status updates** during processing
- **Detailed results** for each file

### 📈 **Results Dashboard**
- **Success/failure indicators** for each file
- **Confidence scores** for successful parses
- **Summary statistics** (success rate, average confidence)
- **Error messages** for failed uploads

## 🎨 Interface Overview

```
┌─────────────────────────────────────────┐
│  🚀 HR Parser                          │
│  Upload resumes in bulk                │
├─────────────────────────────────────────┤
│  📁 Drag & Drop your resume folder     │
│     here                               │
│  or click to browse files              │
│  [Choose Folder]                       │
├─────────────────────────────────────────┤
│  📋 Supported Formats                  │
│  [PDF] [DOCX] [DOC] [TXT] [RTF]        │
└─────────────────────────────────────────┘
```

## 📱 How to Use

### Method 1: Drag & Drop
1. Open your file explorer
2. Navigate to your resume folder
3. **Drag the entire folder** onto the upload area
4. Wait for processing to complete
5. Review the results

### Method 2: Browse Folder
1. Click **"Choose Folder"**
2. Select your resume folder in the file dialog
3. Click **"Upload X Files"**
4. Wait for processing to complete
5. Review the results

### Method 3: Select Multiple Files
1. Click **"Choose Folder"**
2. Hold **Ctrl** (Windows) or **Cmd** (Mac) and select multiple files
3. Click **"Upload X Files"**
4. Wait for processing to complete
5. Review the results

## 📊 Understanding Results

### ✅ **Successful Uploads**
- **Green background** with checkmark
- **Confidence score** (0-100%)
- **Candidate ID** for tracking

### ❌ **Failed Uploads**
- **Red background** with error icon
- **Error message** explaining the issue
- **File name** for identification

### 📈 **Summary Statistics**
- **Total files processed**
- **Success rate percentage**
- **Average confidence score**
- **Number of unique candidates**

## 🔧 Troubleshooting

### Common Issues

1. **"No supported files found"**
   - Check file extensions (must be .pdf, .docx, .doc, .txt, .rtf)
   - Ensure files are not corrupted

2. **"Upload failed"**
   - Check server status (should be running on port 8080)
   - Try with fewer files
   - Check file permissions

3. **"Parse failed"**
   - File might be corrupted or password-protected
   - Check if file contains readable text
   - Try with a different file format

### Browser Compatibility
- ✅ **Chrome** (recommended)
- ✅ **Firefox**
- ✅ **Safari**
- ✅ **Edge**

## 🎯 Best Practices

1. **Organize your folders** by department, role, or date
2. **Use descriptive filenames** for easier tracking
3. **Check file quality** before uploading
4. **Upload in batches** of 10-50 files for best performance
5. **Keep backups** of original files

## 🚀 Advanced Features

### Batch Processing
- Upload **hundreds of resumes** at once
- **Automatic deduplication** by phone number
- **Parallel processing** for faster uploads

### Real-time Feedback
- **Live progress updates** during upload
- **Immediate error detection**
- **Detailed success/failure reporting**

### Data Management
- **One record per person** in MongoDB
- **Automatic updates** for duplicate candidates
- **Structured data storage** for easy querying

---

**Ready to upload your resumes?** 🌐
```
Open http://localhost:8080/ in your browser
```

