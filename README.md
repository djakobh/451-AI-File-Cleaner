# AI-Powered File Purge System
**Team 13 - CECS 451 | Dylan Hartley, Michael Racioppi, Nyrin Thai**

An intelligent file management system using machine learning to identify unnecessary files and help you reclaim storage space safely.

## Features
-  **ML Classification** - Random Forest algorithm (87% accuracy)
-  **Anomaly Detection** - Identifies unusual/forgotten files
-  **Learning System** - Adapts to your preferences over time
-  **Safety First** - System folder protection + simulation mode
-  **Privacy** - Never accesses file content, only metadata

## Quick Start

### Install Dependencies
```bash
# Install Python packages
pip install -r requirements.txt

# Install tkinter (GUI library)
# Windows/Mac: Already included with Python
# Ubuntu/Debian: sudo apt-get install python3-tk
# Fedora/RHEL: sudo dnf install python3-tkinter
```

### Run the Application
```bash
python main.py
```

## How to Use
1. Click **Browse** and select a directory to scan
2. Click **Start Scan** to analyze files
3. Review results (🔴 red = delete, 🟢 green = keep)
4. Select files or click **Select All DELETE** / **Select All KEEP**
5. Click **Delete Files** (choose Recycle Bin or permanent deletion)
6. Use **Export Report** to save results

## Understanding Results
| Column | Meaning |
|--------|---------|
| **Recommendation** | DELETE or KEEP prediction |
| **Confidence** | AI confidence (0-100%) |
| **Days Unaccessed** | How long since file was opened |
| **Anomaly** | Unusual file detected |

## How It Works
```
File Scan → Feature Extraction → ML Prediction → User Review → Learning
```

**AI Techniques:**
- **Random Forest Classifier** - 100 decision trees analyze file patterns
- **Isolation Forest** - Detects unusual files (size, age, location)
- **Reinforcement Learning** - Learns from your keep/delete decisions

## Privacy & Safety
✅ Only analyzes metadata (size, dates, extension)
✅ Never reads file contents
✅ No data sent to external servers
✅ Automatic system folder protection
✅ Recycle Bin support (files can be recovered)
⚠️ Permanent deletion option available (use with caution)

## Project Structure
```
file-purge-system/
├── main.py              # Run this to start
├── requirements.txt     # Dependencies
├── src/
│   ├── core/           # File scanning & analysis
│   ├── ai/             # ML models
│   ├── gui/            # User interface
│   └── utils/          # Logging & export
├── data/               # Models, logs, feedback
└── config/             # Settings & protected folders
```

## Troubleshooting

**"No module named 'tkinter'"**  
→ Install tkinter using OS commands above

**Import errors for numpy/pandas/sklearn**  
→ Run `pip install -r requirements.txt`

**Permission denied**  
→ Don't scan system folders (C:\Windows, etc.)

**Application won't start**  
→ Requires Python 3.8+. Check: `python --version`

## Building Standalone Executable
```bash
pip install pyinstaller
python build_exe.py
# Executable will be in dist/ folder
```

## Configuration
Edit `config/settings.json` to customize scan limits, confidence thresholds, and UI settings.

## Running Tests
```bash
python -m pytest tests/
```

## Technical Details
- **ML Accuracy:** 87%
- **Max Files/Scan:** 5,000
- **Memory Usage:** <500 MB
- **Scan Speed:** 100-200 files/second

## Future Plans
- Duplicate file detection
- Scheduled automatic scans
- Cloud storage integration
- Undo functionality for recent deletions

---
**CECS 451 Fall 2025 - Phase 3 Project**
