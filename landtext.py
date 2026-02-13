"""
LandText - A Simple Text Editor
Version: 1.0.0
Description: A lightweight, cross-platform text editor with themes and customization
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.colorchooser import askcolor
import json
import os
import sys

# Settings file path
SETTINGS_FILE = "landtext_settings.json"

# Default themes
THEMES = {
    "Light": {
        "bg": "white",
        "fg": "black",
        "insertbackground": "black",
        "selectbackground": "lightblue",
        "selectforeground": "black",
        "status_bg": "lightgray",
        "status_fg": "black"
    },
    "Dark": {
        "bg": "#1e1e1e",
        "fg": "#d4d4d4",
        "insertbackground": "white",
        "selectbackground": "#264f78",
        "selectforeground": "white",
        "status_bg": "#2d2d2d",
        "status_fg": "white"
    },
    "Custom": {
        "bg": "white",
        "fg": "black",
        "insertbackground": "black",
        "selectbackground": "lightblue",
        "selectforeground": "black",
        "status_bg": "lightgray",
        "status_fg": "black"
    }
}

# Default font size
current_font_size = 12

# Load settings
def load_settings():
    global current_font_size
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
                if "custom_theme" in settings:
                    THEMES["Custom"] = settings["custom_theme"]
                current_font_size = settings.get("font_size", 12)
                return settings.get("current_theme", "Light")
        except:
            return "Light"
    return "Light"

# Save settings
def save_settings(theme_name):
    settings = {
        "current_theme": theme_name,
        "custom_theme": THEMES["Custom"],
        "font_size": current_font_size
    }
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)

# Get resource path (for PyInstaller)
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Current theme
current_theme = load_settings()

# Track all editor instances
all_editors = []

# Single dialog references
theme_dialog_ref = None
font_dialog_ref = None


class Editor:
    """Single editor instance - can be root or toplevel window"""
    
    def __init__(self, parent=None, is_root=False):
        self.is_root = is_root
        self.current_file = {"path": None, "modified": False}
        
        if is_root:
            self.window = parent
        else:
            self.window = tk.Toplevel(parent)
            self.window.title("LandText")
            self.window.geometry("800x600")
            self.window.minsize(400, 300)
            
            # Set icon for new window
            try:
                icon_path = resource_path('landtext.ico')
                self.window.iconbitmap(icon_path)
            except:
                pass
        
        all_editors.append(self)
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Build UI
        self._create_widgets()
        self._create_menus()
        self._setup_bindings()
        
        # Apply theme and font size
        self.apply_theme(current_theme)
        self.apply_font_size(current_font_size)
    
    def _create_widgets(self):
        # Status bar first
        self.status_bar = tk.Label(
            self.window, text="Line: 1, Column: 0",
            bd=1, relief=tk.SUNKEN, anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Text frame
        frame = tk.Frame(self.window)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        v_scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        h_scrollbar = tk.Scrollbar(frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.text_area = tk.Text(
            frame, wrap=tk.NONE, width=80, height=35,
            font=("Consolas", current_font_size),
            xscrollcommand=h_scrollbar.set,
            yscrollcommand=v_scrollbar.set,
            undo=True, maxundo=-1
        )
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        h_scrollbar.config(command=self.text_area.xview)
        v_scrollbar.config(command=self.text_area.yview)
        self.text_area.focus()
    
    def _create_menus(self):
        menubar = tk.Menu(self.window)
        self.window.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New", command=self.new_file)
        file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_command(label="Save", command=self.save_file)
        file_menu.add_command(label="Save As", command=self.save_as_file)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Action menu
        action_menu = tk.Menu(menubar, tearoff=0)
        action_menu.add_command(label="Undo", command=self.text_area.edit_undo, accelerator="Ctrl+Z")
        action_menu.add_command(label="Redo", command=self.text_area.edit_redo, accelerator="Ctrl+Y")
        action_menu.add_separator()
        action_menu.add_command(label="Find", command=self.open_find_dialog, accelerator="Ctrl+F")
        menubar.add_cascade(label="Action", menu=action_menu)
        
        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="Theme", command=self.open_theme_settings)
        settings_menu.add_command(label="Font Size", command=self.open_font_size_settings)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        
        # Window menu
        window_menu = tk.Menu(menubar, tearoff=0)
        window_menu.add_command(label="Open New Window", command=lambda: Editor(self.window))
        menubar.add_cascade(label="Window", menu=window_menu)
    
    def _setup_bindings(self):
        # Keyboard shortcuts
        self.text_area.bind("<Control-z>", lambda e: self.text_area.edit_undo())
        self.text_area.bind("<Control-y>", lambda e: self.text_area.edit_redo())
        self.window.bind("<Control-f>", lambda e: self.open_find_dialog())
        
        # Mark modified on text changes
        self.text_area.bind("<Key>", self.mark_modified)
        self.text_area.bind("<<Paste>>", self.mark_modified)
        
        # Event-driven status bar
        self.text_area.bind("<KeyRelease>", self.update_status)
        self.text_area.bind("<ButtonRelease-1>", self.update_status)
        self.update_status()
    
    def update_status(self, event=None):
        """Update line/column display"""
        line, column = self.text_area.index(tk.INSERT).split('.')
        self.status_bar.config(text=f"Line: {line}, Column: {column}")
    
    def mark_modified(self, event=None):
        """Mark file as modified and update title"""
        if not self.current_file["modified"]:
            self.current_file["modified"] = True
            self.update_title()
    
    def update_title(self):
        """Update window title with filename and modified indicator"""
        if self.current_file["path"]:
            filename = self.current_file["path"].split('/')[-1].split('\\')[-1]
            title = f"LandText - {filename}"
        else:
            title = "LandText"
        
        if self.current_file["modified"]:
            title += " *"
        
        self.window.title(title)
    
    def apply_theme(self, theme_name):
        """Apply theme colors to this editor"""
        theme = THEMES[theme_name]
        self.text_area.config(
            bg=theme["bg"],
            fg=theme["fg"],
            insertbackground=theme["insertbackground"],
            selectbackground=theme["selectbackground"],
            selectforeground=theme["selectforeground"]
        )
        self.status_bar.config(
            bg=theme["status_bg"],
            fg=theme["status_fg"]
        )
    
    def apply_font_size(self, size):
        """Apply font size to this editor"""
        self.text_area.config(font=("Consolas", size))
    
    def new_file(self):
        """Create new file"""
        if self.current_file["modified"]:
            self.show_unsaved_dialog(lambda: self._do_new_file())
        else:
            self._do_new_file()
    
    def _do_new_file(self):
        self.text_area.delete("1.0", tk.END)
        self.current_file["path"] = None
        self.current_file["modified"] = False
        self.update_title()
    
    def open_file(self):
        """Open file dialog"""
        filename = filedialog.askopenfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Open...",
            parent=self.window
        )
        if filename:
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    content = f.read()
                self.text_area.delete("1.0", tk.END)
                self.text_area.insert("1.0", content)
                self.current_file["path"] = filename
                self.current_file["modified"] = False
                self.update_title()
            except Exception as e:
                messagebox.showerror("Open Error", str(e), parent=self.window)
    
    def save_file(self):
        """Save file (or Save As if no path)"""
        if self.current_file["path"]:
            try:
                content = self.text_area.get("1.0", tk.END)
                with open(self.current_file["path"], "w", encoding="utf-8") as f:
                    f.write(content)
                self.current_file["modified"] = False
                self.update_title()
            except Exception as e:
                messagebox.showerror("Save Error", str(e), parent=self.window)
        else:
            self.save_as_file()
    
    def save_as_file(self):
        """Save As dialog"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Save as...",
            parent=self.window
        )
        if filename:
            try:
                content = self.text_area.get("1.0", tk.END)
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(content)
                self.current_file["path"] = filename
                self.current_file["modified"] = False
                self.update_title()
            except Exception as e:
                messagebox.showerror("Save Error", str(e), parent=self.window)
    
    def show_unsaved_dialog(self, on_discard=None):
        """Show unsaved changes dialog"""
        dialog = tk.Toplevel(self.window)
        dialog.title("Unsaved Changes")
        dialog.geometry("300x120")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.transient(self.window)
        
        # Set icon for dialog
        try:
            icon_path = resource_path('landtext.ico')
            dialog.iconbitmap(icon_path)
        except:
            pass
        
        tk.Label(dialog, text="You have unsaved progress.", font=("Arial", 11)).pack(pady=15)
        
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)
        
        def on_save():
            dialog.destroy()
            self.save_file()
            if on_discard:
                on_discard()
        
        def on_discard():
            dialog.destroy()
            if on_discard:
                on_discard()
        
        save_btn = tk.Button(button_frame, text="Save", width=10, command=on_save)
        save_btn.pack(side=tk.LEFT, padx=5)
        save_btn.focus_set()
        
        tk.Button(button_frame, text="Don't Save", width=10, command=on_discard).pack(side=tk.LEFT, padx=5)
    
    def open_find_dialog(self):
        """Open find dialog for this editor"""
        find_dialog = tk.Toplevel(self.window)
        find_dialog.title("Find")
        find_dialog.geometry("350x120")
        find_dialog.resizable(False, False)
        find_dialog.transient(self.window)
        
        # Set icon for dialog
        try:
            icon_path = resource_path('landtext.ico')
            find_dialog.iconbitmap(icon_path)
        except:
            pass
        
        tk.Label(find_dialog, text="Find:", font=("Arial", 10)).pack(pady=10, padx=10, anchor=tk.W)
        
        search_entry = tk.Entry(find_dialog, width=40, font=("Arial", 10))
        search_entry.pack(padx=10, pady=5)
        search_entry.focus()
        
        def do_find():
            self.text_area.tag_remove("found", "1.0", tk.END)
            search_term = search_entry.get()
            if search_term:
                first_match = None
                idx = "1.0"
                while True:
                    idx = self.text_area.search(search_term, idx, nocase=1, stopindex=tk.END)
                    if not idx:
                        break
                    if first_match is None:
                        first_match = idx
                    lastidx = f"{idx}+{len(search_term)}c"
                    self.text_area.tag_add("found", idx, lastidx)
                    idx = lastidx
                
                self.text_area.tag_config("found", background="yellow")
                
                if first_match:
                    self.text_area.see(first_match)
                    self.text_area.focus()
        
        button_frame = tk.Frame(find_dialog)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Find All", width=10, height=2, command=do_find).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Close", width=10, height=2, command=find_dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        search_entry.bind("<Return>", lambda e: do_find())
    
    def open_font_size_settings(self):
        """Open font size settings (shared across all editors)"""
        global font_dialog_ref, current_font_size
        
        # Only allow one font dialog at a time
        if font_dialog_ref and font_dialog_ref.winfo_exists():
            font_dialog_ref.focus()
            return
        
        font_dialog = tk.Toplevel(self.window)
        font_dialog.title("Font Size Settings")
        font_dialog.geometry("550x320")
        font_dialog.resizable(False, False)
        font_dialog.transient(self.window)
        font_dialog_ref = font_dialog
        
        # Set icon for dialog
        try:
            icon_path = resource_path('landtext.ico')
            font_dialog.iconbitmap(icon_path)
        except:
            pass
        
        tk.Label(font_dialog, text="Adjust Font Size:", font=("Arial", 12, "bold")).pack(pady=20)
        
        # Font size variable
        size_var = tk.IntVar(value=current_font_size)
        
        # Preview label
        preview_label = tk.Label(
            font_dialog,
            text=f"Current size: {current_font_size}",
            font=("Arial", 11)
        )
        preview_label.pack(pady=10)
        
        # Slider frame
        slider_frame = tk.Frame(font_dialog)
        slider_frame.pack(pady=10)
        
        tk.Label(slider_frame, text="8", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        
        def on_slider_change(value):
            size = int(float(value))
            preview_label.config(text=f"Current size: {size}")
        
        slider = tk.Scale(
            slider_frame,
            from_=8,
            to=32,
            orient=tk.HORIZONTAL,
            variable=size_var,
            command=on_slider_change,
            length=280
        )
        slider.pack(side=tk.LEFT, padx=5)
        
        tk.Label(slider_frame, text="32", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        
        def apply_font_size():
            global current_font_size
            current_font_size = size_var.get()
            save_settings(current_theme)
            
            # Apply to ALL editors
            for editor in all_editors:
                editor.apply_font_size(current_font_size)
            
            font_dialog.destroy()
        
        # Button frame with Apply and Cancel
        button_frame = tk.Frame(font_dialog)
        button_frame.pack(pady=20)
        
        apply_btn = tk.Button(button_frame, text="Apply", width=15, height=2, command=apply_font_size)
        apply_btn.pack(side=tk.LEFT, padx=10)
        apply_btn.focus_set()
        
        cancel_btn = tk.Button(button_frame, text="Cancel", width=15, height=2, command=font_dialog.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=10)
    
    def open_theme_settings(self):
        """Open theme settings (shared across all editors)"""
        global theme_dialog_ref, current_theme
        
        # Only allow one theme dialog at a time
        if theme_dialog_ref and theme_dialog_ref.winfo_exists():
            theme_dialog_ref.focus()
            return
        
        theme_dialog = tk.Toplevel(self.window)
        theme_dialog.title("Theme Settings")
        theme_dialog.geometry("550x520")
        theme_dialog.resizable(False, False)
        theme_dialog.transient(self.window)
        theme_dialog_ref = theme_dialog
        
        # Set icon for dialog
        try:
            icon_path = resource_path('landtext.ico')
            theme_dialog.iconbitmap(icon_path)
        except:
            pass
        
        tk.Label(theme_dialog, text="Select Theme:", font=("Arial", 12, "bold")).pack(pady=15)
        
        theme_var = tk.StringVar(value=current_theme)
        
        for theme_name in ["Light", "Dark", "Custom"]:
            tk.Radiobutton(
                theme_dialog, text=theme_name, variable=theme_var,
                value=theme_name, font=("Arial", 11)
            ).pack(anchor=tk.W, padx=30, pady=5)
        
        tk.Label(theme_dialog, text="Custom Theme Colors:", font=("Arial", 11, "bold")).pack(pady=10)
        
        custom_frame = tk.Frame(theme_dialog)
        custom_frame.pack(pady=10)
        
        preview_labels = {}
        
        def pick_color(color_key, label_text):
            def pick():
                color = askcolor(
                    title=f"Choose {label_text}",
                    initialcolor=THEMES["Custom"][color_key],
                    parent=theme_dialog
                )
                if color[1]:
                    THEMES["Custom"][color_key] = color[1]
                    preview_labels[color_key].config(bg=color[1])
                    theme_var.set("Custom")
            
            row = tk.Frame(custom_frame)
            row.pack(pady=3)
            tk.Label(row, text=label_text + ":", width=22, anchor=tk.W).pack(side=tk.LEFT)
            tk.Button(row, text="Choose Color", width=15, command=pick).pack(side=tk.LEFT, padx=5)
            
            preview = tk.Label(
                row, text="  ", width=4,
                bg=THEMES["Custom"][color_key],
                relief=tk.SOLID, borderwidth=1
            )
            preview.pack(side=tk.LEFT, padx=5)
            preview_labels[color_key] = preview
        
        pick_color("bg", "Background")
        pick_color("fg", "Text Color")
        pick_color("selectbackground", "Selection Background")
        pick_color("selectforeground", "Selection Text")
        pick_color("status_bg", "Status Bar BG")
        pick_color("status_fg", "Status Bar Text")
        
        def save_custom_colors():
            save_settings(current_theme)
            messagebox.showinfo("Saved", "Custom theme colors saved!", parent=theme_dialog)
        
        def apply_theme():
            global current_theme
            selected = theme_var.get()
            current_theme = selected
            save_settings(current_theme)
            
            # Apply to ALL editors
            for editor in all_editors:
                editor.apply_theme(current_theme)
            
            theme_dialog.destroy()
        
        button_frame = tk.Frame(theme_dialog)
        button_frame.pack(pady=15)
        
        tk.Button(button_frame, text="Save Colors", width=15, height=2, command=save_custom_colors).pack(side=tk.LEFT, padx=5)
        apply_btn = tk.Button(button_frame, text="Apply Theme", width=15, height=2, command=apply_theme)
        apply_btn.pack(side=tk.LEFT, padx=5)
        apply_btn.focus_set()
        tk.Button(button_frame, text="Cancel", width=15, height=2, command=theme_dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def on_close(self):
        """Handle window close"""
        all_editors.remove(self)
        
        if self.is_root:
            self.window.withdraw()
            if not all_editors:
                self.window.quit()
        else:
            self.window.destroy()
            if not all_editors:
                tk._default_root.quit()


def main():
    """Main entry point"""
    root = tk.Tk()
    root.title("LandText")
    root.geometry("800x600")
    root.minsize(400, 300)
    
    # Set icon for main window
    try:
        icon_path = resource_path('landtext.ico')
        root.iconbitmap(icon_path)
    except:
        pass
    
    main_editor = Editor(root, is_root=True)
    
    root.mainloop()


if __name__ == "__main__":
    main()
