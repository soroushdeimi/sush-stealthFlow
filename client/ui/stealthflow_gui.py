#!/usr/bin/env python3
"""
StealthFlow GUI Application
Clean modern GUI for StealthFlow anti-censorship tool
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import json

class ModernStealthFlowGUI:
    """Modern StealthFlow GUI Application"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("StealthFlow - Smart Anti-Censorship Tool")
        self.root.geometry("900x600")
        self.root.minsize(800, 500)
        
        # Configure modern theme
        self.setup_theme()
        
        # Application state
        self.is_connected = False
        self.current_profile = None
        
        # Create GUI components
        self.create_main_interface()
    
    def setup_theme(self):
        """Setup modern dark theme"""
        style = ttk.Style()
        
        # Configure colors
        self.colors = {
            'bg': '#2b2b2b',
            'fg': '#ffffff',
            'select': '#404040',
            'accent': '#0078d4',
            'success': '#107c10',
            'error': '#d13438'
        }
        
        # Configure root window
        self.root.configure(bg=self.colors['bg'])
        
        # Configure ttk styles
        style.theme_use('clam')
        style.configure('TNotebook', background=self.colors['bg'])
        style.configure('TFrame', background=self.colors['bg'])
        style.configure('TLabelFrame', background=self.colors['bg'])
        style.configure('TLabel', background=self.colors['bg'], foreground=self.colors['fg'])
    
    def create_main_interface(self):
        """Create main interface components"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_connection_tab()
        self.create_profiles_tab()
        self.create_logs_tab()
    
    def create_connection_tab(self):
        """Create connection management tab"""
        main_frame = ttk.Frame(self.notebook)
        self.notebook.add(main_frame, text="Connection")
        
        # Status section
        status_frame = ttk.LabelFrame(main_frame, text="Connection Status", padding=10)
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="Disconnected", 
                                     font=("Arial", 12, "bold"))
        self.status_label.pack(side=tk.LEFT)
        
        # Connection controls
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.connect_btn = ttk.Button(
            control_frame,
            text="Connect",
            command=self.toggle_connection
        )
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        
        # Statistics section
        stats_frame = ttk.LabelFrame(main_frame, text="Connection Statistics", padding=10)
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Statistics table
        columns = ("Name", "Status", "Latency", "Success Rate")
        self.stats_tree = ttk.Treeview(stats_frame, columns=columns, show="headings", height=8)
        
        for col in columns:
            self.stats_tree.heading(col, text=col)
            self.stats_tree.column(col, width=120)
        
        self.stats_tree.pack(fill=tk.BOTH, expand=True)
    
    def create_profiles_tab(self):
        """Create profiles management tab"""
        profiles_frame = ttk.Frame(self.notebook)
        self.notebook.add(profiles_frame, text="Profiles")
        
        # Profile selector
        selector_frame = ttk.LabelFrame(profiles_frame, text="Select Profile", padding=10)
        selector_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.profile_var = tk.StringVar()
        self.profile_combo = ttk.Combobox(selector_frame, textvariable=self.profile_var, 
                                         state="readonly", width=40)
        self.profile_combo.pack(side=tk.LEFT, padx=5)
        
        # Profile details
        details_frame = ttk.LabelFrame(profiles_frame, text="Profile Details", padding=10)
        details_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.profile_text = scrolledtext.ScrolledText(details_frame, width=70, height=15,
                                                     bg=self.colors['select'], 
                                                     fg=self.colors['fg'])
        self.profile_text.pack(fill=tk.BOTH, expand=True)
    
    def create_logs_tab(self):
        """Create logs tab"""
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text="Logs")
        
        # Log display
        self.log_text = scrolledtext.ScrolledText(logs_frame, width=80, height=25,
                                                 bg=self.colors['bg'], 
                                                 fg=self.colors['fg'])
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    def toggle_connection(self):
        """Toggle connection state"""
        if self.is_connected:
            self.disconnect()
        else:
            self.connect()
    
    def connect(self):
        """Connect to StealthFlow"""
        try:
            self.log_message("Attempting to connect...")
            self.connect_btn.configure(text="Connecting...", state="disabled")
            
            # Simulate connection
            def connect_thread():
                time.sleep(2)
                self.root.after(0, self.on_connected)
            
            threading.Thread(target=connect_thread, daemon=True).start()
            
        except Exception as e:
            self.log_message(f"Connection failed: {e}")
            self.connect_btn.configure(text="Connect", state="normal")
    
    def disconnect(self):
        """Disconnect from StealthFlow"""
        self.is_connected = False
        self.status_label.configure(text="Disconnected")
        self.connect_btn.configure(text="Connect", state="normal")
        self.log_message("Disconnected successfully")
    
    def on_connected(self):
        """Handle successful connection"""
        self.is_connected = True
        self.status_label.configure(text="Connected")
        self.connect_btn.configure(text="Disconnect", state="normal")
        self.log_message("Connected successfully")
    
    def log_message(self, message):
        """Add message to log display"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
    
    def run(self):
        """Run the GUI application"""
        try:
            # Load initial data
            self.profile_combo['values'] = ["Default", "Gaming", "Streaming"]
            self.profile_var.set("Default")
            
            self.log_message("StealthFlow GUI started")
            
            # Start main loop
            self.root.mainloop()
            
        except Exception as e:
            messagebox.showerror("Error", f"Application error: {e}")

def main():
    """Main entry point"""
    try:
        app = ModernStealthFlowGUI()
        app.run()
    except Exception as e:
        print(f"Failed to start GUI: {e}")

if __name__ == "__main__":
    main()