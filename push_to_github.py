"""
Script สำหรับ Push โปรเจกต์ขึ้น GitHub
วิธีใช้:
1. ไปที่ https://github.com/new แล้วสร้าง Repository ใหม่ (เช่น ตั้งชื่อว่า stick-figure-shorts)
2. ก๊อปปี้ URL ของ Repo (เช่น https://github.com/YOUR_USERNAME/stick-figure-shorts.git)
3. ใส่ Personal Access Token (PAT) หรือรันคำสั่ง:
   python push_to_github.py <GITHUB_REPO_URL> <GITHUB_TOKEN>
"""
import sys
import os
from dulwich import porcelain

if len(sys.argv) < 2:
    print("Usage: python push_to_github.py <REPO_URL> [GITHUB_TOKEN]")
    sys.exit(1)

repo_url = sys.argv[1]
repo_path = os.path.dirname(os.path.abspath(__file__))

print(f"Pushing to {repo_url}...")
try:
    porcelain.push(repo_path, repo_url, "refs/heads/main:refs/heads/main")
    print("✅ Push to GitHub successful!")
except Exception as e:
    print(f"Error: {e}")
