"""
File operations module - handles file deletion and user confirmations
"""

import tkinter as tk
from tkinter import ttk, messagebox
from ..utils.file_utils import safe_delete_file
import logging

logger = logging.getLogger(__name__)


class DeletionProgressDialog:
    """Progress dialog shown during file deletion"""

    def __init__(self, parent, total_files):
        """
        Initialize progress dialog

        Args:
            parent: Parent window
            total_files: Total number of files to delete
        """
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Deleting Files")
        self.dialog.geometry("500x150")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (150 // 2)
        self.dialog.geometry(f"500x150+{x}+{y}")

        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill='both', expand=True)

        # Title
        ttk.Label(main_frame, text="Deleting Files...",
                 font=('Segoe UI', 12, 'bold')).pack(pady=(0, 10))

        # Status label
        self.status_var = tk.StringVar(value="Starting deletion...")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var)
        self.status_label.pack(pady=5)

        # Progress bar
        self.progress_var = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(
            main_frame,
            variable=self.progress_var,
            maximum=total_files,
            mode='determinate',
            length=450
        )
        self.progress_bar.pack(pady=10)

        # Progress text
        self.progress_text_var = tk.StringVar(value=f"0 / {total_files} files")
        ttk.Label(main_frame, textvariable=self.progress_text_var,
                 font=('Segoe UI', 9)).pack()

        self.total_files = total_files
        self.current_file = 0

    def update_progress(self, current, filename):
        """
        Update progress dialog

        Args:
            current: Current file number
            filename: Current file being deleted
        """
        self.current_file = current
        self.progress_var.set(current)
        self.progress_text_var.set(f"{current} / {self.total_files} files")

        # Truncate long filenames
        if len(filename) > 60:
            display_name = "..." + filename[-57:]
        else:
            display_name = filename

        self.status_var.set(f"Deleting: {display_name}")
        self.dialog.update()

    def close(self):
        """Close the progress dialog"""
        self.dialog.destroy()


class FileOperationsHandler:
    """Handles file deletion operations with user confirmation"""

    def __init__(self, recommender, parent_window=None):
        """
        Initialize file operations handler

        Args:
            recommender: RecommendationEngine instance for recording feedback
            parent_window: Parent window for progress dialog
        """
        self.recommender = recommender
        self.parent_window = parent_window

    def delete_selected_files(self, delete_files_list, keep_files_list, selected_indices):
        """
        Delete selected files with user confirmation

        Args:
            delete_files_list: List of files recommended for deletion
            keep_files_list: List of files recommended to keep
            selected_indices: Dict with 'delete' and 'keep' sets of selected indices

        Returns:
            Dict with results: {
                'success_count': int,
                'failed_count': int,
                'failed_files': list,
                'use_recycle_bin': bool,
                'cancelled': bool
            }
        """
        total_selected = len(selected_indices['delete']) + len(selected_indices['keep'])

        # Check if any files selected
        if total_selected == 0:
            messagebox.showinfo(
                "No Files Selected",
                "Please select files to delete first!\n\n"
                "How to select files:\n"
                "1. Click the checkbox (☐) next to each file you want to delete\n"
                "2. Or use 'Select All DELETE' / 'Select All KEEP' buttons\n"
                "3. Then click 'Delete Files' button"
            )
            return {'cancelled': True}

        # Calculate total size and collect files
        total_size_mb = 0
        files_to_delete = []

        for idx in selected_indices['delete']:
            if idx < len(delete_files_list):
                files_to_delete.append(delete_files_list[idx])
                total_size_mb += delete_files_list[idx].get('size_mb', 0)

        for idx in selected_indices['keep']:
            if idx < len(keep_files_list):
                files_to_delete.append(keep_files_list[idx])
                total_size_mb += keep_files_list[idx].get('size_mb', 0)

        # Show confirmation dialog (platform-aware messaging)
        import platform
        trash_name = "Trash" if platform.system() == 'Darwin' else "Recycle Bin"

        response = messagebox.askyesnocancel(
            "⚠️ Confirm File Deletion",
            f"DELETE {total_selected} files ({total_size_mb:.2f} MB)?\n\n"
            "⚠️ WARNING: This will PERMANENTLY delete the selected files!\n\n"
            f"• Click YES to move files to {trash_name} (recommended)\n"
            "• Click NO to permanently delete (cannot be recovered)\n"
            "• Click CANCEL to abort\n\n"
            "Are you sure you want to continue?"
        )

        if response is None:  # Cancel
            return {'cancelled': True}

        use_recycle_bin = response  # True = Recycle Bin, False = Permanent

        # Create progress dialog
        progress_dialog = None
        if self.parent_window:
            progress_dialog = DeletionProgressDialog(self.parent_window, len(files_to_delete))

        # Perform deletion
        success_count = 0
        failed_count = 0
        failed_files = []

        try:
            for i, file_data in enumerate(files_to_delete, 1):
                filepath = file_data.get('path')
                if filepath:
                    # Update progress
                    if progress_dialog:
                        import os
                        filename = os.path.basename(filepath)
                        progress_dialog.update_progress(i, filename)

                    # Delete file
                    if safe_delete_file(filepath, use_recycle_bin=use_recycle_bin):
                        success_count += 1
                        # Record feedback for learning
                        self.recommender.record_choice(file_data, user_kept=False)
                        logger.info(f"Deleted: {filepath}")
                    else:
                        failed_count += 1
                        failed_files.append(filepath)
                        logger.error(f"Failed to delete: {filepath}")
        finally:
            # Close progress dialog
            if progress_dialog:
                progress_dialog.close()

        return {
            'success_count': success_count,
            'failed_count': failed_count,
            'failed_files': failed_files,
            'use_recycle_bin': use_recycle_bin,
            'total_size_mb': total_size_mb,
            'cancelled': False
        }

    @staticmethod
    def show_deletion_results(results):
        """
        Show deletion results to user

        Args:
            results: Dict returned from delete_selected_files
        """
        if results.get('cancelled'):
            return

        if results['failed_count'] > 0:
            messagebox.showwarning(
                "Deletion Complete with Errors",
                f"✅ Successfully deleted: {results['success_count']} files\n"
                f"❌ Failed to delete: {results['failed_count']} files\n\n"
                f"Failed files:\n" + "\n".join(results['failed_files'][:10]) +
                ("\n..." if len(results['failed_files']) > 10 else "")
            )
        else:
            import platform
            trash_name = "Trash" if platform.system() == 'Darwin' else "Recycle Bin"
            deletion_type = f"moved to {trash_name}" if results['use_recycle_bin'] else "permanently deleted"
            messagebox.showinfo(
                "✅ Deletion Successful",
                f"Successfully {deletion_type}:\n"
                f"• {results['success_count']} files\n"
                f"• {results['total_size_mb']:.2f} MB freed\n\n"
                "Feedback recorded for future recommendations."
            )
