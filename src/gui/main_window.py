"""
Main application window and orchestration
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
    """Main application class"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} v{APP_VERSION} - {TEAM_NAME}")
        self.root.geometry(f"{UI_CONFIG['window_width']}x{UI_CONFIG['window_height']}")
        
        # Initialize components
        self.analyzer = FileAnalyzer()
        self.scanner = DirectoryScanner(self.analyzer)
        self.classifier = MLClassifier()
        self.anomaly_detector = AnomalyDetector()
        self.recommender = RecommendationEngine()
        
        # Data storage
        self.scan_results = []
        self.recommendations = []
        self.selected_indices = set()
        
        # Setup UI
        self.setup_ui()
        
        logger.info("Application initialized")
    
    def setup_ui(self):
        """Setup the user interface"""
        
        # === Header ===
        header_frame = ttk.Frame(self.root, padding=10)
        header_frame.pack(fill='x')
        
        title_label = ttk.Label(
            header_frame,
            text=APP_NAME,
            font=(UI_CONFIG['font_family'], UI_CONFIG['title_font_size'], 'bold')
        )
        title_label.pack()
        
        subtitle_label = ttk.Label(
            header_frame,
            text="Intelligent file management using Machine Learning",
            font=(UI_CONFIG['font_family'], 10)
        )
        subtitle_label.pack()
        
        # === Control Panel ===
        control_frame = ttk.LabelFrame(self.root, text="Scan Controls", padding=10)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        # Directory selection
        dir_frame = ttk.Frame(control_frame)
        dir_frame.pack(fill='x', pady=5)
        
        ttk.Label(dir_frame, text="Directory:").pack(side='left', padx=5)
        
        self.path_var = tk.StringVar(value=str(Path.home() / "Downloads"))
        path_entry = ttk.Entry(dir_frame, textvariable=self.path_var, width=60)
        path_entry.pack(side='left', padx=5, fill='x', expand=True)
        
        browse_btn = ttk.Button(dir_frame, text="Browse", command=self.browse_directory)
        browse_btn.pack(side='left', padx=5)
        
        # Scan button
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill='x', pady=5)
        
        self.scan_btn = ttk.Button(button_frame, text="Start Scan", command=self.start_scan)
        self.scan_btn.pack(side='left', padx=5)
        
        self.cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.cancel_scan, state='disabled')
        self.cancel_btn.pack(side='left', padx=5)
        
        # === Progress ===
        progress_frame = ttk.Frame(self.root, padding=5)
        progress_frame.pack(fill='x', padx=10)
        
        self.progress_var = tk.StringVar(value="Ready to scan")
        progress_label = ttk.Label(progress_frame, textvariable=self.progress_var)
        progress_label.pack()
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill='x', pady=5)
        
        # === Results ===
        results_frame = ttk.LabelFrame(self.root, text="Scan Results", padding=10)
        results_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Treeview
        tree_frame = ttk.Frame(results_frame)
        tree_frame.pack(fill='both', expand=True)
        
        columns = ('File', 'Size', 'Access', 'Recommendation', 'Confidence', 'ML', 'Anomaly')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='tree headings', 
                                 height=UI_CONFIG['tree_height'])
        
        # Configure columns
        self.tree.heading('#0', text='☐')
        self.tree.heading('File', text='File Path')
        self.tree.heading('Size', text='Size (MB)')
        self.tree.heading('Access', text='Days Unaccessed')
        self.tree.heading('Recommendation', text='Recommendation')
        self.tree.heading('Confidence', text='Confidence')
        self.tree.heading('ML', text='ML Pred')
        self.tree.heading('Anomaly', text='Anomaly')
        self.tree.column('#0', width=50)
        self.tree.column('File', width=400)
        self.tree.column('Size', width=80)
        self.tree.column('Access', width=100)
        self.tree.column('Recommendation', width=120)
        self.tree.column('Confidence', width=80)
        self.tree.column('ML', width=60)
        self.tree.column('Anomaly', width=60)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Tree click handler
        self.tree.bind('<Button-1>', self.on_tree_click)
        
        # === Action Panel ===
        action_frame = ttk.Frame(self.root, padding=10)
        action_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(action_frame, text="Select All Recommended", 
                  command=self.select_recommended).pack(side='left', padx=5)
        ttk.Button(action_frame, text="Deselect All", 
                  command=self.deselect_all).pack(side='left', padx=5)
        ttk.Button(action_frame, text="Simulate Delete", 
                  command=self.simulate_delete).pack(side='left', padx=5)
        ttk.Button(action_frame, text="Export Report", 
                  command=self.export_report).pack(side='left', padx=5)
        
        # Status
        self.status_var = tk.StringVar(value="")
        status_label = ttk.Label(action_frame, textvariable=self.status_var, 
                                foreground=COLORS['status_info'])
        status_label.pack(side='left', padx=20)
        
        # === Menu Bar ===
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
        help_menu.add_command(label="Statistics", command=self.show_statistics)
    
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
        
        # Disable scan button
        self.scan_btn.config(state='disabled')
        self.cancel_btn.config(state='normal')
        
        # Clear previous results
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.selected_indices.clear()
        
        # Start progress
        self.progress_var.set("Starting scan...")
        self.progress_bar.start()
        
        # Run in background
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
            
            # Scan files
            def update_progress(count, status):
                self.root.after(0, lambda: self.progress_var.set(
                    f"Scanned {count} files... {status[:50]}"
                ))
            
            self.scan_results = self.scanner.scan(
                path,
                max_files=5000,
                progress_callback=update_progress
            )
            
            if not self.scan_results:
                self.root.after(0, lambda: messagebox.showinfo(
                    "Info", "No files found or scan cancelled"
                ))
                self.root.after(0, self.scan_complete)
                return
            
            # ML Classification
            self.root.after(0, lambda: self.progress_var.set("Running ML classification..."))
            predictions, probabilities = self.classifier.predict(self.scan_results)
            
            # Anomaly Detection
            self.root.after(0, lambda: self.progress_var.set("Detecting anomalies..."))
            anomaly_results = self.anomaly_detector.detect_with_reasons(self.scan_results)
            
            # Generate Recommendations
            self.root.after(0, lambda: self.progress_var.set("Generating recommendations..."))
            self.recommendations = self.recommender.get_recommendations(
                self.scan_results,
                predictions.tolist(),
                probabilities.tolist()
            )
            
            # Combine results
            for i, (file_data, rec, anom) in enumerate(zip(
                self.scan_results, self.recommendations, anomaly_results
            )):
                file_data.update(rec)
                file_data.update(anom)
            
            # Display results
            self.root.after(0, self.display_results)
            
        except Exception as e:
            logger.exception(f"Error during scan: {e}")
            self.root.after(0, lambda: messagebox.showerror(
                "Error", f"Scan failed: {str(e)}"
            ))
        finally:
            self.root.after(0, self.scan_complete)
    
    def scan_complete(self):
        """Called when scan is complete"""
        self.progress_bar.stop()
        self.scan_btn.config(state='normal')
        self.cancel_btn.config(state='disabled')
        self.progress_var.set("Scan complete")
    
    def display_results(self):
        """Display scan results"""
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Sort by recommendation confidence
        sorted_results = sorted(
            self.scan_results,
            key=lambda x: (x.get('recommend_delete', False), x.get('confidence', 0)),
            reverse=True
        )
        
        # Add to tree
        for i, file_data in enumerate(sorted_results[:1000]):  # Limit to 1000 for performance
            rec = "DELETE" if file_data.get('recommend_delete') else "KEEP"
            conf = file_data.get('confidence', 0)
            ml_pred = "KEEP" if file_data.get('ml_prediction') == 1 else "DEL"
            anom = "Yes" if file_data.get('is_anomaly') else "No"
            
            values = (
                file_data.get('path', ''),
                f"{file_data.get('size_mb', 0):.2f}",
                f"{file_data.get('accessed_days_ago', 0):.0f}",
                rec,
                f"{conf:.1%}",
                ml_pred,
                anom
            )
            
            tag = 'delete' if file_data.get('recommend_delete') else 'keep'
            item_id = self.tree.insert('', 'end', text='☐', values=values, tags=(tag, str(i)))
        
        # Configure tags
        self.tree.tag_configure('delete', background=COLORS['delete_bg'])
        self.tree.tag_configure('keep', background=COLORS['keep_bg'])
        
        # Update status
        delete_count = sum(1 for f in self.scan_results if f.get('recommend_delete'))
        total_size = sum(f.get('size_mb', 0) for f in self.scan_results if f.get('recommend_delete'))
        
        self.status_var.set(
            f"Found {len(self.scan_results)} files | "
            f"{delete_count} recommended for deletion ({total_size:.1f} MB)"
        )
    
    def on_tree_click(self, event):
        """Handle tree click for selection"""
        region = self.tree.identify('region', event.x, event.y)
        if region == 'tree':
            item = self.tree.identify_row(event.y)
            if item:
                # Toggle selection
                current_text = self.tree.item(item, 'text')
                if current_text == '☐':
                    self.tree.item(item, text='☑')
                    # Extract index from tags
                    tags = self.tree.item(item, 'tags')
                    for tag in tags:
                        if tag.isdigit():
                            self.selected_indices.add(int(tag))
                else:
                    self.tree.item(item, text='☐')
                    tags = self.tree.item(item, 'tags')
                    for tag in tags:
                        if tag.isdigit():
                            self.selected_indices.discard(int(tag))
    
    def select_recommended(self):
        """Select all files recommended for deletion"""
        self.selected_indices.clear()
        for item in self.tree.get_children():
            tags = self.tree.item(item, 'tags')
            if 'delete' in tags:
                self.tree.item(item, text='☑')
                for tag in tags:
                    if tag.isdigit():
                        self.selected_indices.add(int(tag))
    
    def deselect_all(self):
        """Deselect all files"""
        self.selected_indices.clear()
        for item in self.tree.get_children():
            self.tree.item(item, text='☐')
    
    def simulate_delete(self):
        """Simulate file deletion"""
        if not self.selected_indices:
            messagebox.showinfo("Info", "No files selected")
            return
        
        response = messagebox.askyesno(
            "Confirm Simulation",
            f"Simulate deletion of {len(self.selected_indices)} files?\n\n"
            "Note: Files will NOT actually be deleted (simulation mode).\n"
            "Your choices will be recorded to improve recommendations."
        )
        
        if not response:
            return
        
        # Record feedback
        for idx in self.selected_indices:
            if idx < len(self.scan_results):
                self.recommender.record_choice(self.scan_results[idx], user_kept=False)
        
        # Remove from display
        items_to_remove = []
        for item in self.tree.get_children():
            if self.tree.item(item, 'text') == '☑':
                items_to_remove.append(item)
        
        for item in items_to_remove:
            self.tree.delete(item)
        
        self.selected_indices.clear()
        
        messagebox.showinfo(
            "Success",
            f"Simulated deletion of {len(items_to_remove)} files.\n"
            "Feedback recorded for future recommendations."
        )
    
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
        messagebox.showinfo(
            "About",
            f"{APP_NAME} v{APP_VERSION}\n\n"
            f"{TEAM_NAME}\n"
            "CECS 451 - Fall 2025\n\n"
            "Intelligent file management using:\n"
            "• Machine Learning Classification\n"
            "• Anomaly Detection\n"
            "• Personalized Recommendations"
        )
    
    def show_statistics(self):
        """Show application statistics"""
        stats = self.recommender.get_statistics()
        scanner_stats = self.scanner.get_statistics()
        
        msg = (
            "Application Statistics\n\n"
            f"Files Scanned: {scanner_stats.get('files_scanned', 0)}\n"
            f"Directories: {scanner_stats.get('directories_scanned', 0)}\n"
            f"Errors: {scanner_stats.get('errors', 0)}\n\n"
            f"User Feedback:\n"
            f"  Total Decisions: {stats['total_feedback']}\n"
            f"  Files Kept: {stats['files_kept']}\n"
            f"  Files Deleted: {stats['files_deleted']}\n"
            f"  Extensions Learned: {stats['extensions_learned']}\n"
            f"  Categories Learned: {stats['categories_learned']}\n"
        )
        
        messagebox.showinfo("Statistics", msg)
    
    def run(self):
        """Run the application"""
        self.root.mainloop()