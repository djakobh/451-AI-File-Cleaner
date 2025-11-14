"""
Generate synthetic test files for File Purge System
Creates realistic file structure with various ages, sizes, and types
"""

import os
import random
from pathlib import Path
from datetime import datetime, timedelta

def generate_test_files(base_dir="test_files", num_files=1000):
    """
    Generate realistic test files
    
    Args:
        base_dir: Directory to create files in
        num_files: Number of files to generate
    """
    base_path = Path(base_dir)
    base_path.mkdir(exist_ok=True)
    
    # File categories with extensions
    categories = {
        'documents': ['pdf', 'docx', 'txt', 'xlsx', 'pptx', 'doc', 'odt'],
        'images': ['jpg', 'png', 'gif', 'bmp', 'svg', 'webp'],
        'videos': ['mp4', 'avi', 'mkv', 'mov', 'wmv'],
        'audio': ['mp3', 'wav', 'flac', 'aac', 'ogg'],
        'archives': ['zip', 'rar', '7z', 'tar', 'gz'],
        'executables': ['exe', 'msi', 'dll', 'bat'],
        'disposable': ['tmp', 'cache', 'bak', 'log', 'old'],
        'code': ['py', 'js', 'java', 'cpp', 'html', 'css'],
    }
    
    # Age categories (days ago)
    age_profiles = {
        'recent': (0, 30),      # Last month
        'moderate': (31, 180),  # 1-6 months
        'old': (181, 730),      # 6 months - 2 years
        'ancient': (731, 1825), # 2-5 years
    }
    
    # Size profiles (KB)
    size_profiles = {
        'tiny': (1, 100),           # 1-100 KB
        'small': (100, 1024),       # 100KB-1MB
        'medium': (1024, 10240),    # 1-10 MB
        'large': (10240, 102400),   # 10-100 MB
        'huge': (102400, 512000),   # 100-500 MB
    }
    
    print(f"Generating {num_files} test files in {base_dir}/")
    print("=" * 60)
    
    files_created = 0
    
    # Generate files
    for i in range(num_files):
        # Choose category
        category = random.choice(list(categories.keys()))
        extension = random.choice(categories[category])
        
        # Choose age
        age_profile = random.choice(list(age_profiles.keys()))
        days_ago = random.randint(*age_profiles[age_profile])
        
        # Choose size
        size_profile = random.choice(list(size_profiles.keys()))
        size_kb = random.randint(*size_profiles[size_profile])
        
        # Create subdirectory structure (some files nested)
        depth = random.randint(0, 3)
        if depth == 0:
            dir_path = base_path
        else:
            subdirs = [f"folder_{random.randint(1, 10)}" for _ in range(depth)]
            dir_path = base_path / Path(*subdirs)
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        filename = f"{category}_{i}_{age_profile}_{size_profile}.{extension}"
        filepath = dir_path / filename
        
        # Create file with random content
        try:
            with open(filepath, 'wb') as f:
                # Write random bytes
                content_size = size_kb * 1024
                chunk_size = min(content_size, 8192)
                written = 0
                while written < content_size:
                    to_write = min(chunk_size, content_size - written)
                    f.write(os.urandom(to_write))
                    written += to_write
            
            # Set file timestamps (created, modified, accessed)
            now = datetime.now()
            old_time = now - timedelta(days=days_ago)
            timestamp = old_time.timestamp()
            
            # Set access and modification time
            os.utime(filepath, (timestamp, timestamp))
            
            files_created += 1
            
            if files_created % 100 == 0:
                print(f"Created {files_created} files...")
        
        except Exception as e:
            print(f"Error creating {filepath}: {e}")
    
    print("=" * 60)
    print(f"✅ Successfully created {files_created} test files")
    print(f"📁 Location: {base_path.absolute()}")
    
    # Generate summary
    print("\n📊 Test Data Summary:")
    print("-" * 60)
    
    # Count files by category
    for cat in categories.keys():
        count = len(list(base_path.rglob(f"*{cat}*")))
        print(f"  {cat.capitalize():<15} {count} files")
    
    # Calculate total size
    total_size = sum(f.stat().st_size for f in base_path.rglob('*') if f.is_file())
    print(f"\n  Total Size: {total_size / (1024**3):.2f} GB")
    
    print("\n🎯 Test Scenarios Covered:")
    print("-" * 60)
    print("  ✅ Various file ages (0 days to 5 years)")
    print("  ✅ Different file sizes (1 KB to 500 MB)")
    print("  ✅ Multiple file types (8 categories)")
    print("  ✅ Nested directory structures (up to 3 levels)")
    print("  ✅ Mix of disposable and important files")
    
    print("\n💡 Usage:")
    print("-" * 60)
    print(f"  1. Point the File Purge System to: {base_path.absolute()}")
    print(f"  2. Run a scan")
    print(f"  3. Verify deletion rate is 40-60%")
    print(f"  4. Check that old/disposable files are flagged")
    
    print("\n⚠️  To delete this test data:")
    print(f"  import shutil; shutil.rmtree('{base_dir}')")


def generate_specific_test_cases(base_dir="test_files_specific"):
    """Generate specific test cases for edge cases"""
    base_path = Path(base_dir)
    base_path.mkdir(exist_ok=True)
    
    print(f"\n\n🧪 Generating Specific Test Cases in {base_dir}/")
    print("=" * 60)
    
    test_cases = [
        # (filename, size_kb, days_old, description)
        ("recent_important.docx", 500, 1, "Recent document - should KEEP"),
        ("old_disposable.tmp", 100, 400, "Old temp file - should DELETE"),
        ("huge_old_file.zip", 500000, 800, "Huge old archive - should DELETE"),
        ("tiny_recent.txt", 1, 5, "Tiny recent file - should KEEP"),
        ("log_file_ancient.log", 50, 1000, "Ancient log - should DELETE"),
        ("project_file.py", 100, 30, "Recent code - should KEEP"),
        ("backup_old.bak", 1000, 500, "Old backup - should DELETE"),
        ("photo_vacation.jpg", 5000, 60, "Recent photo - should KEEP"),
        ("cache_data.cache", 200, 200, "Old cache - should DELETE"),
        ("important_doc.pdf", 2000, 90, "Important doc - should KEEP"),
    ]
    
    for filename, size_kb, days_old, description in test_cases:
        filepath = base_path / filename
        
        # Create file
        with open(filepath, 'wb') as f:
            f.write(os.urandom(size_kb * 1024))
        
        # Set timestamp
        now = datetime.now()
        old_time = now - timedelta(days=days_old)
        timestamp = old_time.timestamp()
        os.utime(filepath, (timestamp, timestamp))
        
        print(f"  ✅ {filename:<30} ({description})")
    
    print("\n💡 Use this folder to verify:")
    print("  - Recent files are kept")
    print("  - Old disposable files are deleted")
    print("  - Large old files are flagged")
    print(f"\n📁 Location: {base_path.absolute()}")


if __name__ == "__main__":
    import sys
    
    # Parse arguments
    num_files = 1000
    if len(sys.argv) > 1:
        try:
            num_files = int(sys.argv[1])
        except ValueError:
            print("Usage: python generate_test_data.py [num_files]")
            print("Example: python generate_test_data.py 2000")
            sys.exit(1)
    
    # Generate files
    generate_test_files(num_files=num_files)
    
    # Generate specific test cases
    generate_specific_test_cases()
    
    print("\n" + "=" * 60)
    print("✅ Test data generation complete!")
    print("=" * 60)
