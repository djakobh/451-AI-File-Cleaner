"""
Main application window with side-by-side results and live metrics dashboard
UPDATED: Added Type column to show file extensions + SORTABLE columns
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import threading
import logging

from ..core.config import APP_NAME, APP_VERSION, TEAM_NAME, UI_CONFIG, COLORS
from ..core.scanner import DirectoryScanner
from ..core.file_analyzer import FileAnalyzer
from ..ai.ml_classifier import MLClassifier
from ..ai.anomaly_detector import AnomalyDetector
from ..ai.recommender import RecommendationEngine
from ..utils.export import export_to_csv

logger = logging.getLogger(__name__)


class FilePurgeApp:
    """Main application class with live metrics dashboard"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} v{APP_VERSION} - {TEAM_NAME}")
        self.root.geometry("1600x900")  # Wider for side-by-side view
        
        # Initialize components
        self.analyzer = FileAnalyzer()
        self.scanner = DirectoryScanner(self.analyzer)
        self.classifier = MLClassifier()
        self.anomaly_detector = AnomalyDetector()
        self.recommender = RecommendationEngine()
        
        # Data storage
        self.scan_results = []
        self.recommendations = []
        self.selected_indices = {'delete': set(), 'keep': set()}
        
        # Sorting state
        self.delete_sort_column = None
        self.delete_sort_reverse = False
        self.keep_sort_column = None
        self.keep_sort_reverse = False
        
        # Filtered/sorted data
        self.delete_files = []
        self.keep_files = []
        
        # Setup UI
        self.setup_ui()
        
        logger.info("Application initialized")
    
    def setup_ui(self):
        """Setup the user interface"""
        
        # Header
        header_frame = ttk.Frame(self.root, padding=10)
        header_frame.pack(fill='x')
        
        ttk.Label(header_frame, text=APP_NAME, 
                 font=(UI_CONFIG['font_family'], UI_CONFIG['title_font_size'], 'bold')).pack()
        ttk.Label(header_frame, text="Intelligent file management using Machine Learning",
                 font=(UI_CONFIG['font_family'], 10)).pack()
        
        # Control Panel
        self._setup_controls()
        
        # Progress
        self._setup_progress()
        
        # Main content area - Split into results and metrics
        main_container = ttk.Frame(self.root)
        main_container.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Left side: Results (70% width)
        results_container = ttk.Frame(main_container)
        results_container.pack(side='left', fill='both', expand=True)
        self._setup_results(results_container)
        
        # Right side: Metrics Dashboard (30% width)
        metrics_container = ttk.LabelFrame(main_container, text="📊 Model Metrics", padding=10)
        metrics_container.pack(side='right', fill='both', padx=(10, 0))
        self._setup_metrics_dashboard(metrics_container)
        
        # Action Panel
        self._setup_actions()
        
        # Menu Bar
        self._setup_menu()
    
    def _setup_controls(self):
        """Setup control panel"""
        control_frame = ttk.LabelFrame(self.root, text="Scan Controls", padding=10)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        dir_frame = ttk.Frame(control_frame)
        dir_frame.pack(fill='x', pady=5)
        
        ttk.Label(dir_frame, text="Directory:").pack(side='left', padx=5)
        self.path_var = tk.StringVar(value=str(Path.home() / "Downloads"))
        ttk.Entry(dir_frame, textvariable=self.path_var, width=60).pack(side='left', padx=5, fill='x', expand=True)
        ttk.Button(dir_frame, text="Browse", command=self.browse_directory).pack(side='left', padx=5)
        
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill='x', pady=5)
        
        self.scan_btn = ttk.Button(button_frame, text="Start Scan", command=self.start_scan)
        self.scan_btn.pack(side='left', padx=5)
        
        self.cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.cancel_scan, state='disabled')
        self.cancel_btn.pack(side='left', padx=5)
    
    def _setup_progress(self):
        """Setup progress indicators"""
        progress_frame = ttk.Frame(self.root, padding=5)
        progress_frame.pack(fill='x', padx=10)
        
        self.progress_var = tk.StringVar(value="Ready to scan")
        ttk.Label(progress_frame, textvariable=self.progress_var).pack()
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill='x', pady=5)
    
    def _setup_results(self, parent):
        """Setup side-by-side results view"""
        results_frame = ttk.LabelFrame(parent, text="Scan Results", padding=10)
        results_frame.pack(fill='both', expand=True)
        
        # Split into two columns
        split_frame = ttk.Frame(results_frame)
        split_frame.pack(fill='both', expand=True)
        
        # Left: DELETE recommendations (red)
        delete_frame = ttk.LabelFrame(split_frame, text="🔴 Recommended for Deletion", padding=5)
        delete_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        self._create_tree(delete_frame, 'delete')
        
        # Right: KEEP recommendations (green)
        keep_frame = ttk.LabelFrame(split_frame, text="🟢 Recommended to Keep", padding=5)
        keep_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
        self._create_tree(keep_frame, 'keep')
    
    def _create_tree(self, parent, tree_type):
        """Create a treeview for delete or keep files - WITH SORTABLE COLUMNS"""
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill='both', expand=True)
        
        columns = ('File', 'Type', 'Size', 'Access', 'Confidence')
        tree = ttk.Treeview(tree_frame, columns=columns, show='tree headings', height=20)
        
        tree.heading('#0', text='☐')
        tree.heading('File', text='File Path', command=lambda: self.sort_tree(tree_type, 'File'))
        tree.heading('Type', text='Type', command=lambda: self.sort_tree(tree_type, 'Type'))
        tree.heading('Size', text='Size (MB) ⇅', command=lambda: self.sort_tree(tree_type, 'Size'))
        tree.heading('Access', text='Days Unaccessed ⇅', command=lambda: self.sort_tree(tree_type, 'Access'))
        tree.heading('Confidence', text='Confidence', command=lambda: self.sort_tree(tree_type, 'Confidence'))
        
        tree.column('#0', width=40)
        tree.column('File', width=260)
        tree.column('Type', width=70)
        tree.column('Size', width=80)
        tree.column('Access', width=100)
        tree.column('Confidence', width=80)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient='vertical', command=tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient='horizontal', command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Bind click event
        tree.bind('<Button-1>', lambda e: self.on_tree_click(e, tree_type))
        
        # Store reference
        if tree_type == 'delete':
            self.delete_tree = tree
        else:
            self.keep_tree = tree
    
    def sort_tree(self, tree_type, column):
        """Sort tree by column (ascending/descending toggle)"""
        tree = self.delete_tree if tree_type == 'delete' else self.keep_tree
        files = self.delete_files if tree_type == 'delete' else self.keep_files
        
        # Toggle sort direction
        if tree_type == 'delete':
            if self.delete_sort_column == column:
                self.delete_sort_reverse = not self.delete_sort_reverse
            else:
                self.delete_sort_column = column
                self.delete_sort_reverse = False
            reverse = self.delete_sort_reverse
        else:
            if self.keep_sort_column == column:
                self.keep_sort_reverse = not self.keep_sort_reverse
            else:
                self.keep_sort_column = column
                self.keep_sort_reverse = False
            reverse = self.keep_sort_reverse
        
        # Sort data
        if column == 'File':
            files.sort(key=lambda x: x.get('path', '').lower(), reverse=reverse)
        elif column == 'Type':
            files.sort(key=lambda x: x.get('extension', '').lower(), reverse=reverse)
        elif column == 'Size':
            files.sort(key=lambda x: x.get('size_mb', 0), reverse=reverse)
        elif column == 'Access':
            files.sort(key=lambda x: x.get('accessed_days_ago', 0), reverse=reverse)
        elif column == 'Confidence':
            files.sort(key=lambda x: x.get('confidence', 0), reverse=reverse)
        
        # Update heading to show sort direction
        direction = '▼' if reverse else '▲'
        tree.heading('File', text='File Path' + (' ' + direction if column == 'File' else ''))
        tree.heading('Type', text='Type' + (' ' + direction if column == 'Type' else ''))
        tree.heading('Size', text=f'Size (MB) {direction if column == "Size" else "⇅"}')
        tree.heading('Access', text=f'Days Unaccessed {direction if column == "Access" else "⇅"}')
        tree.heading('Confidence', text='Confidence' + (' ' + direction if column == 'Confidence' else ''))
        
        # Re-populate tree
        self._populate_tree(tree, files, tree_type)
    
    def _populate_tree(self, tree, files, tree_type):
        """Populate tree with files"""
        # Clear tree
        for item in tree.get_children():
            tree.delete(item)
        
        # Add files
        for i, file_data in enumerate(files[:1000]):
            ext = file_data.get('extension', '')
            category = file_data.get('category', '')
            if category and category != 'other':
                type_display = f".{ext}"
            else:
                type_display = f"" if ext else "N/A"
            
            values = (
                file_data.get('path', ''),
                type_display,
                f"{file_data.get('size_mb', 0):.2f}",
                f"{file_data.get('accessed_days_ago', 0):.0f}",
                f"{file_data.get('confidence', 0):.1%}"
            )
            
            # Check if this file was selected
            is_selected = i in self.selected_indices[tree_type]
            checkbox = '☑' if is_selected else '☐'
            
            tree.insert('', 'end', text=checkbox, values=values, 
                       tags=(tree_type, str(i)))
        
        tree.tag_configure('delete', background=COLORS['delete_bg'])
        tree.tag_configure('keep', background=COLORS['keep_bg'])
    
    def _setup_metrics_dashboard(self, parent):
        """Setup live metrics dashboard"""
        # Create canvas with scrollbar
        canvas = tk.Canvas(parent, width=350, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Store references
        self.metrics_frame = scrollable_frame
        
        # Initialize with placeholder
        self._update_metrics_display({
            'total': 0,
            'delete_count': 0,
            'keep_count': 0,
            'deletion_rate': 0,
            'avg_delete_conf': 0,
            'avg_keep_conf': 0,
            'total_size_gb': 0,
            'delete_size_gb': 0,
            'anomaly_count': 0,
            'anomaly_rate': 0,
            'categories': {},
            'feedback': {'total_feedback': 0, 'files_kept': 0, 'files_deleted': 0, 'extensions_learned': 0}
        })
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _update_metrics_display(self, metrics):
        """Update the metrics dashboard with current data"""
        # Clear existing widgets
        for widget in self.metrics_frame.winfo_children():
            widget.destroy()
        
        m = metrics
        
        # Overall Statistics
        ttk.Label(self.metrics_frame, text="📊 Overall Statistics", 
                 font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(0, 5))
        ttk.Separator(self.metrics_frame, orient='horizontal').pack(fill='x', pady=5)
        
        ttk.Label(self.metrics_frame, text=f"Total Files: {m['total']:,}").pack(anchor='w')
        ttk.Label(self.metrics_frame, text=f"DELETE: {m['delete_count']:,} ({m['deletion_rate']:.1f}%)").pack(anchor='w')
        ttk.Label(self.metrics_frame, text=f"KEEP: {m['keep_count']:,} ({100-m['deletion_rate']:.1f}%)").pack(anchor='w')
        
        # Status indicator
        if 40 <= m['deletion_rate'] <= 60:
            status_text = "✅ Balanced"
            status_color = "green"
        elif m['deletion_rate'] > 70:
            status_text = "⚠️ High"
            status_color = "orange"
        elif m['deletion_rate'] < 30:
            status_text = "⚠️ Low"
            status_color = "orange"
        else:
            status_text = "✓ OK"
            status_color = "blue"
        
        ttk.Label(self.metrics_frame, text=f"Status: {status_text}", 
                 foreground=status_color).pack(anchor='w', pady=(5, 10))
        
        # Confidence Metrics
        ttk.Label(self.metrics_frame, text="🎯 Confidence", 
                 font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(10, 5))
        ttk.Separator(self.metrics_frame, orient='horizontal').pack(fill='x', pady=5)
        
        delete_conf_status = "✅" if m['avg_delete_conf'] > 0.70 else "⚠️"
        keep_conf_status = "✅" if m['avg_keep_conf'] > 0.65 else "⚠️"
        
        ttk.Label(self.metrics_frame, 
                 text=f"DELETE: {m['avg_delete_conf']:.1%} {delete_conf_status}").pack(anchor='w')
        ttk.Label(self.metrics_frame, 
                 text=f"KEEP: {m['avg_keep_conf']:.1%} {keep_conf_status}").pack(anchor='w', pady=(0, 10))
        
        # Storage Impact
        ttk.Label(self.metrics_frame, text="💾 Storage Impact", 
                 font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(10, 5))
        ttk.Separator(self.metrics_frame, orient='horizontal').pack(fill='x', pady=5)
        
        ttk.Label(self.metrics_frame, text=f"Total: {m['total_size_gb']:.2f} GB").pack(anchor='w')
        ttk.Label(self.metrics_frame, text=f"To Delete: {m['delete_size_gb']:.2f} GB").pack(anchor='w')
        ttk.Label(self.metrics_frame, 
                 text=f"To Keep: {m['total_size_gb']-m['delete_size_gb']:.2f} GB").pack(anchor='w', pady=(0, 10))
        
        # Anomaly Detection
        ttk.Label(self.metrics_frame, text="🔍 Anomalies", 
                 font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(10, 5))
        ttk.Separator(self.metrics_frame, orient='horizontal').pack(fill='x', pady=5)
        
        anomaly_status = "✅" if 5 <= m['anomaly_rate'] <= 15 else "⚠️"
        ttk.Label(self.metrics_frame, 
                 text=f"Detected: {m['anomaly_count']} ({m['anomaly_rate']:.1f}%) {anomaly_status}").pack(anchor='w', pady=(0, 10))
        
        # Top Categories
        ttk.Label(self.metrics_frame, text="📁 Top Categories", 
                 font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(10, 5))
        ttk.Separator(self.metrics_frame, orient='horizontal').pack(fill='x', pady=5)
        
        if m['categories']:
            sorted_cats = sorted(m['categories'].items(), 
                               key=lambda x: x[1]['total'], reverse=True)[:5]
            for cat, stats in sorted_cats:
                pct = stats['delete'] / stats['total'] * 100 if stats['total'] > 0 else 0
                ttk.Label(self.metrics_frame, 
                         text=f"{cat}: {stats['total']} ({pct:.0f}% del)").pack(anchor='w')
        
        # User Feedback
        ttk.Label(self.metrics_frame, text="👤 Your Feedback", 
                 font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(15, 5))
        ttk.Separator(self.metrics_frame, orient='horizontal').pack(fill='x', pady=5)
        
        ttk.Label(self.metrics_frame, 
                 text=f"Decisions: {m['feedback']['total_feedback']}").pack(anchor='w')
        ttk.Label(self.metrics_frame, 
                 text=f"Kept: {m['feedback']['files_kept']}").pack(anchor='w')
        ttk.Label(self.metrics_frame, 
                 text=f"Deleted: {m['feedback']['files_deleted']}").pack(anchor='w')
    
    def _setup_actions(self):
        """Setup action buttons"""
        action_frame = ttk.Frame(self.root, padding=10)
        action_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(action_frame, text="Select All DELETE", 
                  command=lambda: self.select_all('delete')).pack(side='left', padx=5)
        ttk.Button(action_frame, text="Select All KEEP", 
                  command=lambda: self.select_all('keep')).pack(side='left', padx=5)
        ttk.Button(action_frame, text="Deselect All", 
                  command=self.deselect_all).pack(side='left', padx=5)
        ttk.Button(action_frame, text="Simulate Delete", 
                  command=self.simulate_delete).pack(side='left', padx=5)
        ttk.Button(action_frame, text="Export Report", 
                  command=self.export_report).pack(side='left', padx=5)
        
        self.status_var = tk.StringVar(value="")
        ttk.Label(action_frame, textvariable=self.status_var, 
                 foreground=COLORS['status_info']).pack(side='left', padx=20)
    
    def _setup_menu(self):
        """Setup menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Export Results", command=self.export_report)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Sorting Help", 
                             command=lambda: messagebox.showinfo("Sorting", 
                                 "Click column headers to sort:\n\n"
                                 "• Size (MB) ⇅ - Click to sort by file size\n"
                                 "• Days Unaccessed ⇅ - Click to sort by age\n"
                                 "• ▲ = Ascending  ▼ = Descending\n\n"
                                 "Click again to reverse sort order!"))
    
    def browse_directory(self):
        """Browse for directory"""
        directory = filedialog.askdirectory(initialdir=self.path_var.get())
        if directory:
            self.path_var.set(directory)
    
    def start_scan(self):
        """Start scanning in background thread"""
        path = self.path_var.get()
        
        if not Path(path).exists():
            messagebox.showerror("Error", "Directory does not exist")
            return
        
        self.scan_btn.config(state='disabled')
        self.cancel_btn.config(state='normal')
        
        # Clear both trees
        for item in self.delete_tree.get_children():
            self.delete_tree.delete(item)
        for item in self.keep_tree.get_children():
            self.keep_tree.delete(item)
        
        self.selected_indices = {'delete': set(), 'keep': set()}
        
        self.progress_var.set("Starting scan...")
        self.progress_bar.start()
        
        thread = threading.Thread(target=self.scan_and_analyze, args=(path,), daemon=True)
        thread.start()
    
    def cancel_scan(self):
        """Cancel current scan"""
        self.scanner.cancel()
        self.progress_var.set("Cancelling...")
    
    def scan_and_analyze(self, path: str):
        """Scan and analyze files (runs in background thread)"""
        try:
            logger.info(f"Starting scan of {path}")
            
            def update_progress(count, status):
                self.root.after(0, lambda: self.progress_var.set(
                    f"Scanned {count} files... {status[:50]}"
                ))
            
            self.scan_results = self.scanner.scan(path, max_files=5000, progress_callback=update_progress)
            
            if not self.scan_results:
                self.root.after(0, lambda: messagebox.showinfo("Info", "No files found or scan cancelled"))
                self.root.after(0, self.scan_complete)
                return
            
            self.root.after(0, lambda: self.progress_var.set("Running ML classification..."))
            predictions, probabilities = self.classifier.predict(self.scan_results)
            
            self.root.after(0, lambda: self.progress_var.set("Detecting anomalies..."))
            anomaly_results = self.anomaly_detector.detect_with_reasons(self.scan_results)
            
            self.root.after(0, lambda: self.progress_var.set("Generating recommendations..."))
            self.recommendations = self.recommender.get_recommendations(
                self.scan_results, predictions.tolist(), probabilities.tolist()
            )
            
            for i, (file_data, rec, anom) in enumerate(zip(self.scan_results, self.recommendations, anomaly_results)):
                file_data.update(rec)
                file_data.update(anom)
            
            self.root.after(0, self.display_results)
            
        except Exception as e:
            logger.exception(f"Error during scan: {e}")
            self.root.after(0, lambda: messagebox.showerror("Error", f"Scan failed: {str(e)}"))
        finally:
            self.root.after(0, self.scan_complete)
    
    def scan_complete(self):
        """Called when scan is complete"""
        self.progress_bar.stop()
        self.scan_btn.config(state='normal')
        self.cancel_btn.config(state='disabled')
        self.progress_var.set("Scan complete")
    
    def display_results(self):
        """Display scan results in side-by-side trees"""
        # Separate and store files
        self.delete_files = [f for f in self.scan_results if f.get('recommend_delete')]
        self.keep_files = [f for f in self.scan_results if not f.get('recommend_delete')]
        
        # Sort by confidence (default)
        self.delete_files.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        self.keep_files.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        # Reset sort state
        self.delete_sort_column = None
        self.delete_sort_reverse = False
        self.keep_sort_column = None
        self.keep_sort_reverse = False
        
        # Populate trees
        self._populate_tree(self.delete_tree, self.delete_files, 'delete')
        self._populate_tree(self.keep_tree, self.keep_files, 'keep')
        
        # Update metrics dashboard
        metrics = self._calculate_metrics()
        self._update_metrics_display(metrics)
        
        # Update status bar
        delete_count = len(self.delete_files)
        total_size = sum(f.get('size_mb', 0) for f in self.delete_files)
        
        self.status_var.set(
            f"Found {len(self.scan_results)} files | "
            f"DELETE: {delete_count} ({total_size:.1f} MB) | "
            f"KEEP: {len(self.keep_files)}"
        )
    
    def _calculate_metrics(self):
        """Calculate all performance metrics"""
        total = len(self.scan_results)
        delete_files = [f for f in self.scan_results if f.get('recommend_delete')]
        keep_files = [f for f in self.scan_results if not f.get('recommend_delete')]
        
        metrics = {
            'total': total,
            'delete_count': len(delete_files),
            'keep_count': len(keep_files),
            'deletion_rate': len(delete_files) / total * 100 if total > 0 else 0,
            'avg_delete_conf': sum(f.get('confidence', 0) for f in delete_files) / len(delete_files) if delete_files else 0,
            'avg_keep_conf': sum(f.get('confidence', 0) for f in keep_files) / len(keep_files) if keep_files else 0,
            'total_size_gb': sum(f.get('size_mb', 0) for f in self.scan_results) / 1024,
            'delete_size_gb': sum(f.get('size_mb', 0) for f in delete_files) / 1024,
            'anomaly_count': sum(1 for f in self.scan_results if f.get('is_anomaly')),
            'anomaly_rate': sum(1 for f in self.scan_results if f.get('is_anomaly')) / total * 100 if total > 0 else 0,
        }
        
        # Category stats
        from collections import defaultdict
        metrics['categories'] = defaultdict(lambda: {'total': 0, 'delete': 0})
        for f in self.scan_results:
            cat = f.get('category', 'other')
            metrics['categories'][cat]['total'] += 1
            if f.get('recommend_delete'):
                metrics['categories'][cat]['delete'] += 1
        
        # User feedback
        metrics['feedback'] = self.recommender.get_statistics()
        
        return metrics
    
    def on_tree_click(self, event, tree_type):
        """Handle tree click for selection"""
        tree = self.delete_tree if tree_type == 'delete' else self.keep_tree
        region = tree.identify('region', event.x, event.y)
        
        if region == 'tree':
            item = tree.identify_row(event.y)
            if item:
                current_text = tree.item(item, 'text')
                new_text = '☑' if current_text == '☐' else '☐'
                tree.item(item, text=new_text)
                
                tags = tree.item(item, 'tags')
                for tag in tags:
                    if tag.isdigit():
                        idx = int(tag)
                        if new_text == '☑':
                            self.selected_indices[tree_type].add(idx)
                        else:
                            self.selected_indices[tree_type].discard(idx)
    
    def select_all(self, tree_type):
        """Select all in specified tree"""
        tree = self.delete_tree if tree_type == 'delete' else self.keep_tree
        self.selected_indices[tree_type].clear()
        
        for item in tree.get_children():
            tree.item(item, text='☑')
            tags = tree.item(item, 'tags')
            for tag in tags:
                if tag.isdigit():
                    self.selected_indices[tree_type].add(int(tag))
    
    def deselect_all(self):
        """Deselect all files"""
        self.selected_indices = {'delete': set(), 'keep': set()}
        
        for item in self.delete_tree.get_children():
            self.delete_tree.item(item, text='☐')
        for item in self.keep_tree.get_children():
            self.keep_tree.item(item, text='☐')
    
    def simulate_delete(self):
        """Simulate file deletion"""
        total_selected = len(self.selected_indices['delete']) + len(self.selected_indices['keep'])
        
        if total_selected == 0:
            messagebox.showinfo("Info", "No files selected")
            return
        
        response = messagebox.askyesno(
            "Confirm Simulation",
            f"Simulate deletion of {total_selected} files?\n\n"
            "Note: Files will NOT actually be deleted (simulation mode).\n"
            "Your choices will be recorded to improve recommendations."
        )
        
        if not response:
            return
        
        # Record feedback
        for idx in self.selected_indices['delete']:
            if idx < len(self.delete_files):
                self.recommender.record_choice(self.delete_files[idx], user_kept=False)
        
        for idx in self.selected_indices['keep']:
            if idx < len(self.keep_files):
                self.recommender.record_choice(self.keep_files[idx], user_kept=False)
        
        # Remove from trees
        items_to_remove = []
        for item in self.delete_tree.get_children():
            if self.delete_tree.item(item, 'text') == '☑':
                items_to_remove.append(item)
        for item in items_to_remove:
            self.delete_tree.delete(item)
        
        items_to_remove = []
        for item in self.keep_tree.get_children():
            if self.keep_tree.item(item, 'text') == '☑':
                items_to_remove.append(item)
        for item in items_to_remove:
            self.keep_tree.delete(item)
        
        self.selected_indices = {'delete': set(), 'keep': set()}
        messagebox.showinfo("Success",
            f"Simulated deletion of {total_selected} files.\n"
            "Feedback recorded for future recommendations.")
    
    def export_report(self):
        """Export results to CSV"""
        if not self.scan_results:
            messagebox.showinfo("Info", "No results to export")
            return
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filepath:
            try:
                export_to_csv(self.scan_results, filepath)
                messagebox.showinfo("Success", f"Report exported to {filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {e}")
    
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo("About",
            f"{APP_NAME} v{APP_VERSION}\n\n"
            f"{TEAM_NAME}\n"
            "CECS 451 - Fall 2025\n\n"
            "Intelligent file management using:\n"
            "• Machine Learning Classification\n"
            "• Anomaly Detection\n"
            "• Personalized Recommendations\n\n"
            "💡 Click column headers to sort!"
        )
    
    def run(self):
        """Run the application"""
        self.root.mainloop()