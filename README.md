# AI-Powered File Purge System
**Team 13 - CECS 451 Phase 3 Project**

## Team Members
- Dylan Hartley
- Michael Racioppi  
- Nyrin Thai

## Overview
An intelligent file management system that uses machine learning to identify and recommend files for deletion, helping users reclaim storage space without compromising system integrity.

## Key Features

### 1. Machine Learning Classification
- Random Forest algorithm analyzes file metadata
- 87%+ accuracy on synthetic training data
- Privacy-first: Never accesses file content

### 2. Anomaly Detection
- Isolation Forest identifies unusual files
- Detects large, unused, or outdated files
- Provides reasons for anomaly classification

### 3. Recommendation Engine
- Learns from user feedback over time
- Adapts to individual preferences
- Reinforcement learning approach

### 4. Safety Features
- Automatic system folder protection
- Simulation mode for safe testing
- User approval required for all actions

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup Instructions

1. **Clone or download the project**
```bash
cd file-purge-system
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the application**
```bash
python main.py
```

## Usage Guide

### Quick Start
1. Launch the application: `python main.py`
2. Click "Browse" to select a directory (default: Downloads)
3. Click "Start Scan" to begin analysis
4. Review color-coded recommendations:
   - **Red background** = Recommended for deletion
   - **Green background** = Recommended to keep
5. Select files manually or click "Select All Recommended"
6. Click "Simulate Delete" to test (files are NOT actually deleted)
7. Export results with "Export Report"

### Understanding Results
- **Size (MB)**: File size in megabytes
- **Days Unaccessed**: Days since last file access
- **Recommendation**: DELETE or KEEP
- **Confidence**: AI confidence level (0-100%)
- **ML Pred**: Raw machine learning prediction
- **Anomaly**: Whether file is flagged as unusual

## Technical Architecture
```
┌─────────────────────────────────────┐
│      User Interface (Tkinter)       │
└──────────────┬──────────────────────┘
               │
       ┌───────┴───────┐
       │               │
┌──────▼──────┐ ┌─────▼──────┐
│File Analyzer│ │Recommender │
└──────┬──────┘ └─────┬──────┘
       │               │
       └───────┬───────┘
               │
    ┌──────────▼──────────┐
    │   ML Classification  │
    │ • Random Forest      │
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │ Anomaly Detection    │
    │ • Isolation Forest   │
    └─────────────────────┘
```

## AI Techniques

### Random Forest Classifier
- **Algorithm**: Ensemble of 100 decision trees
- **Features**: Size, access patterns, file age, extension
- **Training**: Synthetic data with heuristic labeling
- **Output**: Keep/Delete prediction with confidence

### Isolation Forest
- **Purpose**: Detect anomalous files
- **Features**: Size, access age, directory depth
- **Contamination**: 10% expected anomalies
- **Output**: Binary anomaly flag + reasons

### Recommendation Engine
- **Approach**: Reinforcement learning from user feedback
- **Storage**: Local JSON file
- **Learning**: Extension and category preferences
- **Adjustment**: ±15% score modification

## Data Privacy

✅ **No file content is ever accessed**  
✅ **Only metadata is analyzed**  
✅ **No data sent to external servers**  
✅ **User feedback stored locally only**

### Metadata Analyzed
- File size, creation/modification/access dates
- File extension and directory path
- File attributes (hidden, system)
- **NOT analyzed**: File contents, file names (except extension)

## Project Structure
```
file-purge-system/
├── main.py                    # Application entry point
├── requirements.txt           # Dependencies
├── README.md                 # This file
├── src/
│   ├── core/                 # Core functionality
│   │   ├── config.py         # Configuration
│   │   ├── file_analyzer.py  # Metadata extraction
│   │   └── scanner.py        # Directory scanning
│   ├── ai/                   # AI models
│   │   ├── ml_classifier.py  # Random Forest
│   │   ├── anomaly_detector.py # Isolation Forest
│   │   ├── recommender.py    # Learning engine
│   │   └── feature_engineer.py # Feature prep
│   ├── gui/                  # User interface
│   │   └── main_window.py    # Main window
│   └── utils/                # Utilities
│       ├── logger.py         # Logging
│       └── export.py         # CSV export
└── data/                     # Generated data
    ├── models/               # Saved ML models
    ├── feedback/             # User preferences
    └── logs/                 # Application logs
```

## Performance

| Metric | Value |
|--------|-------|
| Files scanned/second | 100-200 |
| ML accuracy | 87% |
| Memory usage | <500 MB |
| Max files per scan | 5,000 |

## Troubleshooting

**Problem**: Import errors  
**Solution**: Ensure all `__init__.py` files exist in folders

**Problem**: No GUI appears  
**Solution**: Install tkinter: `pip install tk` (or `apt-get install python3-tk` on Linux)

**Problem**: Permission denied  
**Solution**: Don't scan system folders; run without admin privileges

**Problem**: Slow scanning  
**Solution**: Reduce max_files in config.py or scan smaller directories

## Future Enhancements

- Actual file deletion (with recycle bin)
- Duplicate file detection
- Content-aware image analysis
- Scheduled automatic scans
- Cloud synchronization

## License
Academic project for CECS 451 - Fall 2025

## Support
For issues or questions, contact team members via Canvas.

---
**Phase 3 Deliverable - CECS 451 - Team 13**