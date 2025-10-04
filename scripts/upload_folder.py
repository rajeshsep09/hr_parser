#!/usr/bin/env python3
"""
Upload entire folder of resumes to HR Parser API.
Usage: python upload_folder.py <folder_path>
"""

import requests
import os
import sys
from pathlib import Path

def upload_folder(folder_path, api_url="http://localhost:8080/hr/parser/bulk"):
    """Upload entire folder of resumes."""
    
    print(f"📁 Uploading folder: {folder_path}")
    print("=" * 60)
    
    # Check if folder exists
    folder = Path(folder_path)
    if not folder.exists():
        print(f"❌ Folder not found: {folder_path}")
        return False
    
    if not folder.is_dir():
        print(f"❌ Path is not a directory: {folder_path}")
        return False
    
    # Find all resume files
    resume_extensions = ['.pdf', '.docx', '.doc', '.txt', '.rtf']
    files = []
    
    for file_path in folder.rglob("*"):  # Recursively search subdirectories
        if file_path.is_file() and file_path.suffix.lower() in resume_extensions:
            files.append(file_path)
    
    if not files:
        print(f"❌ No resume files found in {folder_path}")
        print(f"   Supported formats: {', '.join(resume_extensions)}")
        return False
    
    print(f"📄 Found {len(files)} resume files:")
    for file_path in files:
        relative_path = file_path.relative_to(folder)
        print(f"   - {relative_path}")
    
    # Prepare files for upload
    upload_files = []
    failed_files = []
    
    for file_path in files:
        try:
            with open(file_path, "rb") as f:
                # Determine MIME type based on extension
                mime_type = "application/octet-stream"
                ext = file_path.suffix.lower()
                
                if ext == '.pdf':
                    mime_type = "application/pdf"
                elif ext == '.docx':
                    mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                elif ext == '.doc':
                    mime_type = "application/msword"
                elif ext == '.txt':
                    mime_type = "text/plain"
                elif ext == '.rtf':
                    mime_type = "application/rtf"
                
                upload_files.append(("files", (file_path.name, f.read(), mime_type)))
                
        except Exception as e:
            print(f"❌ Error reading {file_path.name}: {e}")
            failed_files.append(file_path.name)
    
    if not upload_files:
        print("❌ No files could be read for upload")
        return False
    
    # Upload files
    print(f"\n📡 Uploading {len(upload_files)} files...")
    try:
        response = requests.post(api_url, files=upload_files, timeout=300)  # 5 minute timeout
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Bulk upload successful!")
            print(f"   Total files processed: {result['count']}")
            
            # Show results
            successful = 0
            failed = 0
            candidates = set()
            
            for i, file_result in enumerate(result['results']):
                filename = files[i].name
                if file_result.get('ok'):
                    successful += 1
                    confidence = file_result.get('parsing_confidence', 0)
                    candidate_id = file_result.get('candidate_id', 'N/A')
                    candidates.add(candidate_id)
                    print(f"   ✅ {filename}: {confidence:.2f} confidence (ID: {candidate_id[:8]}...)")
                else:
                    failed += 1
                    error = file_result.get('error', 'Unknown error')
                    print(f"   ❌ {filename}: {error}")
            
            print(f"\n📊 Summary:")
            print(f"   ✅ Successful: {successful}")
            print(f"   ❌ Failed: {failed}")
            print(f"   👥 Unique candidates: {len(candidates)}")
            print(f"   📈 Success rate: {successful/len(files)*100:.1f}%")
            
            if failed_files:
                print(f"   📁 Files with read errors: {len(failed_files)}")
            
            return True
            
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Upload timed out. Try with fewer files or check server status.")
        return False
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False

def main():
    """Main function."""
    
    if len(sys.argv) != 2:
        print("Usage: python upload_folder.py <folder_path>")
        print("Example: python upload_folder.py ./resumes")
        sys.exit(1)
    
    folder_path = sys.argv[1]
    
    print("🚀 HR Parser - Folder Upload Tool")
    print("=" * 60)
    
    success = upload_folder(folder_path)
    
    if success:
        print(f"\n🎉 Folder upload completed successfully!")
    else:
        print(f"\n❌ Folder upload failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()

