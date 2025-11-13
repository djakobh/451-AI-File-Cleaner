"""
Build script to create Windows executable using PyInstaller
"""

import PyInstaller.__main__
import sys
from pathlib import Path

def build_executable():
    """Build standalone executable"""
    
    print("Building Windows executable...")
    print("This may take several minutes...")
    
    # Get the project directory
    project_dir = Path(__file__).parent
    
    # PyInstaller arguments
    args = [
        'main.py',
        '--name=FilePurgeSystem',
        '--windowed',  # No console window
        '--onefile',   # Single executable file
        '--clean',     # Clean cache before building
        f'--distpath={project_dir}/dist',
        f'--workpath={project_dir}/build',
        f'--specpath={project_dir}',
        
        # Add data files
        '--add-data=config;config',
        
        # Hidden imports for scikit-learn
        '--hidden-import=sklearn.utils._cython_blas',
        '--hidden-import=sklearn.neighbors.typedefs',
        '--hidden-import=sklearn.neighbors.quad_tree',
        '--hidden-import=sklearn.tree',
        '--hidden-import=sklearn.tree._utils',
        '--hidden-import=sklearn.ensemble',
        '--hidden-import=sklearn.ensemble._forest',
        '--hidden-import=sklearn.ensemble._iforest',
        
        # Other hidden imports
        '--hidden-import=pandas',
        '--hidden-import=numpy',
        '--hidden-import=tkinter',
        '--hidden-import=tkinter.ttk',
        
        # Optimize
        '--strip',
        '--noupx',
    ]
    
    try:
        PyInstaller.__main__.run(args)
        print("\n" + "="*50)
        print("Build complete!")
        print(f"Executable location: {project_dir}/dist/FilePurgeSystem.exe")
        print("="*50)
        
    except Exception as e:
        print(f"Build failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        import subprocess
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
        import PyInstaller
    
    build_executable()