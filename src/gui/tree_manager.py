"""
Tree manager module - handles tree view operations and file selection
"""

from tkinter import ttk
from ..core.config import COLORS
import logging

logger = logging.getLogger(__name__)


class TreeManager:
    """Manages tree view operations for file display and selection"""

    def __init__(self):
        """Initialize tree manager"""
        self.delete_tree = None
        self.keep_tree = None
        self.selected_indices = {'delete': set(), 'keep': set()}

        # Sorting state
        self.delete_sort_column = None
        self.delete_sort_reverse = False
        self.keep_sort_column = None
        self.keep_sort_reverse = False

    def create_tree(self, parent, tree_type, on_click_callback):
        """
        Create a treeview for delete or keep files with sortable columns

        Args:
            parent: Parent widget
            tree_type: 'delete' or 'keep'
            on_click_callback: Function to call when tree item is clicked

        Returns:
            ttk.Treeview widget
        """
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill='both', expand=True)

        columns = ('File', 'Type', 'Size', 'Access', 'Confidence')
        tree = ttk.Treeview(tree_frame, columns=columns, show='tree headings', height=20)

        tree.heading('#0', text='☐')
        tree.heading('File', text='File Path')
        tree.heading('Type', text='Type')
        tree.heading('Size', text='Size (MB) ⇅')
        tree.heading('Access', text='Days Unaccessed ⇅')
        tree.heading('Confidence', text='Confidence')

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
        tree.bind('<Button-1>', lambda e: on_click_callback(e, tree_type))

        # Store reference
        if tree_type == 'delete':
            self.delete_tree = tree
        else:
            self.keep_tree = tree

        return tree

    def populate_tree(self, tree, files, tree_type):
        """
        Populate tree with files

        Args:
            tree: ttk.Treeview widget
            files: List of file data dictionaries
            tree_type: 'delete' or 'keep'
        """
        # Clear tree
        for item in tree.get_children():
            tree.delete(item)

        # Add files (limit to 1000 for performance)
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

    def sort_tree(self, tree_type, column, files):
        """
        Sort tree by column

        Args:
            tree_type: 'delete' or 'keep'
            column: Column name to sort by
            files: List of file data to sort

        Returns:
            Sorted files list
        """
        tree = self.delete_tree if tree_type == 'delete' else self.keep_tree

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

        return files

    def on_tree_click(self, event, tree_type):
        """
        Handle tree click for selection

        Args:
            event: Click event
            tree_type: 'delete' or 'keep'
        """
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
        """
        Select all files in specified tree

        Args:
            tree_type: 'delete' or 'keep'
        """
        tree = self.delete_tree if tree_type == 'delete' else self.keep_tree
        self.selected_indices[tree_type].clear()

        for item in tree.get_children():
            tree.item(item, text='☑')
            tags = tree.item(item, 'tags')
            for tag in tags:
                if tag.isdigit():
                    self.selected_indices[tree_type].add(int(tag))

    def deselect_all(self):
        """Deselect all files in both trees"""
        self.selected_indices = {'delete': set(), 'keep': set()}

        for item in self.delete_tree.get_children():
            self.delete_tree.item(item, text='☐')
        for item in self.keep_tree.get_children():
            self.keep_tree.item(item, text='☐')

    def remove_deleted_files(self, delete_files_list, keep_files_list, failed_files):
        """
        Remove successfully deleted files from trees

        Args:
            delete_files_list: List of files in delete tree
            keep_files_list: List of files in keep tree
            failed_files: List of file paths that failed to delete
        """
        # Remove from delete tree
        items_to_remove = []
        for item in self.delete_tree.get_children():
            if self.delete_tree.item(item, 'text') == '☑':
                tags = self.delete_tree.item(item, 'tags')
                for tag in tags:
                    if tag.isdigit():
                        idx = int(tag)
                        if idx < len(delete_files_list):
                            if delete_files_list[idx].get('path') not in failed_files:
                                items_to_remove.append(item)
        for item in items_to_remove:
            self.delete_tree.delete(item)

        # Remove from keep tree
        items_to_remove = []
        for item in self.keep_tree.get_children():
            if self.keep_tree.item(item, 'text') == '☑':
                tags = self.keep_tree.item(item, 'tags')
                for tag in tags:
                    if tag.isdigit():
                        idx = int(tag)
                        if idx < len(keep_files_list):
                            if keep_files_list[idx].get('path') not in failed_files:
                                items_to_remove.append(item)
        for item in items_to_remove:
            self.keep_tree.delete(item)

        # Clear selection
        self.selected_indices = {'delete': set(), 'keep': set()}

    def reset_sort_state(self):
        """Reset sorting state to default"""
        self.delete_sort_column = None
        self.delete_sort_reverse = False
        self.keep_sort_column = None
        self.keep_sort_reverse = False
