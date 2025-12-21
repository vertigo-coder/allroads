#!/usr/bin/env python3
"""
Software Development Roadmap Builder
A GUI application for creating and managing software development roadmaps with quarterly timeline view
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser
import json
import datetime
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
import os

@dataclass
class Feature:
    id: str
    title: str
    description: str
    completed: bool = False
    color: str = "#2196F3"

@dataclass
class Quarter:
    year: int
    quarter: int
    features: Optional[List[Feature]] = None
    
    def __post_init__(self):
        if self.features is None:
            self.features = []
    
    @property
    def name(self):
        return f"Q{self.quarter} {self.year}"
    
    @property
    def date_range(self):
        months = {1: (1, 3), 2: (4, 6), 3: (7, 9), 4: (10, 12)}
        start_month, end_month = months[self.quarter]
        start_date = datetime.date(self.year, start_month, 1)
        if end_month == 12:
            end_date = datetime.date(self.year, end_month, 31)
        else:
            # Get last day of the month
            next_month = end_month + 1
            end_date = datetime.date(self.year, next_month, 1) - datetime.timedelta(days=1)
        return f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}"

class QuarterFrame(ttk.Frame):
    def __init__(self, parent, quarter: Quarter, app):
        super().__init__(parent, relief=tk.RIDGE, borderwidth=2)
        self.quarter = quarter
        self.app = app
        self.min_width = 250  # Set minimum width
        self.setup_ui()
        
    def setup_ui(self):
        # Header
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, padx=5, pady=5)
        
        title_label = tk.Label(header_frame, text=self.quarter.name, 
                               font=("Arial", 12, "bold"), fg="white", bg="#333333")
        title_label.pack(fill=tk.X)
        
        date_label = tk.Label(header_frame, text=self.quarter.date_range, 
                              font=("Arial", 9), fg="gray")
        date_label.pack(fill=tk.X)
        
        # Add feature button
        add_btn = ttk.Button(self, text="+ Add Feature", command=self.add_feature)
        add_btn.pack(pady=5)
        
        # Features list
        self.features_frame = tk.Frame(self, bg="white")
        self.features_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.feature_widgets = []
        self.refresh_features()
    
    def add_feature(self):
        """Add a new feature to this quarter"""
        dialog = FeatureDialog(self.app.root, "Add Feature")
        if dialog.result:
            feature = Feature(
                id=f"feature_{len(self.quarter.features) if self.quarter.features else 0}",
                title=dialog.result['title'],
                description=dialog.result['description'],
                color=dialog.result.get('color', '#2196F3')
            )
            if self.quarter.features is not None:
                self.quarter.features.append(feature)
            else:
                self.quarter.features = [feature]
            self.refresh_features()
            self.app.status_var.set(f"Added feature: {feature.title}")
    
    def refresh_features(self):
        """Refresh the features display"""
        # Clear existing widgets
        for widget in self.feature_widgets:
            widget.destroy()
        self.feature_widgets.clear()
        
        # Add feature widgets
        if self.quarter.features:
            for feature in self.quarter.features:
                feature_frame = tk.Frame(self.features_frame, bg="white", relief=tk.RAISED, borderwidth=1)
                feature_frame.pack(fill=tk.X, pady=2)
                
                # Color indicator
                color_label = tk.Label(feature_frame, width=2, bg=feature.color)
                color_label.pack(side=tk.LEFT, fill=tk.Y)
                
                # Content frame
                content_frame = tk.Frame(feature_frame, bg="white")
                content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=2)
                
                # Checkbox and title
                title_frame = tk.Frame(content_frame, bg="white")
                title_frame.pack(fill=tk.X)
                
                var = tk.BooleanVar(value=feature.completed)
                cb = tk.Checkbutton(title_frame, text=feature.title, variable=var,
                                  command=lambda f=feature, v=var: self.toggle_feature(f, v),
                                  bg="white", fg="black", font=("Arial", 9, "bold" if not feature.completed else "normal"))
                cb.pack(side=tk.LEFT)
                
                # Description
                desc_label = tk.Label(content_frame, text=feature.description, 
                                     bg="white", fg="gray", font=("Arial", 8), 
                                     anchor="w", justify="left")
                desc_label.pack(fill=tk.X, padx=(20, 0))
                
                # Edit and delete buttons
                btn_frame = tk.Frame(feature_frame, bg="white")
                btn_frame.pack(side=tk.RIGHT, padx=2, pady=1)
                
                edit_btn = tk.Button(btn_frame, text="Edit", 
                                   command=lambda f=feature: self.edit_feature(f),
                                   font=("Arial", 8))
                edit_btn.pack(side=tk.LEFT)
                
                delete_btn = tk.Button(btn_frame, text="Delete", 
                                     command=lambda f=feature: self.delete_feature(f),
                                     font=("Arial", 8))
                delete_btn.pack(side=tk.LEFT)
                
                # Move up/down buttons
                move_frame = tk.Frame(btn_frame, bg="white")
                move_frame.pack(side=tk.LEFT)
                
                up_btn = tk.Button(move_frame, text="↑", 
                                 command=lambda f=feature: self.move_feature_up(f),
                                 font=("Arial", 8), width=2)
                up_btn.pack(side=tk.LEFT)
                
                down_btn = tk.Button(move_frame, text="↓", 
                                   command=lambda f=feature: self.move_feature_down(f),
                                   font=("Arial", 8), width=2)
                down_btn.pack(side=tk.LEFT)
                
                self.feature_widgets.append(feature_frame)
    
    def toggle_feature(self, feature, var):
        """Toggle feature completion"""
        feature.completed = var.get()
        self.refresh_features()
    
    def edit_feature(self, feature):
        """Edit a feature"""
        dialog = FeatureDialog(self.app.root, "Edit Feature", feature)
        if dialog.result:
            feature.title = dialog.result['title']
            feature.description = dialog.result['description']
            feature.color = dialog.result.get('color', feature.color)
            self.refresh_features()
            self.app.status_var.set(f"Updated feature: {feature.title}")
    
    def delete_feature(self, feature):
        """Delete a feature"""
        if messagebox.askyesno("Delete Feature", f"Delete '{feature.title}'?"):
            if self.quarter.features and feature in self.quarter.features:
                self.quarter.features.remove(feature)
            self.refresh_features()
            self.app.status_var.set(f"Deleted feature: {feature.title}")
    
    def move_feature_up(self, feature):
        """Move feature up within quarter or to previous quarter"""
        if not self.quarter.features:
            return
        
        current_index = self.quarter.features.index(feature)
        
        if current_index > 0:
            # Move up within same quarter
            self.quarter.features[current_index], self.quarter.features[current_index - 1] = \
                self.quarter.features[current_index - 1], self.quarter.features[current_index]
            self.refresh_features()
            self.app.status_var.set(f"Moved '{feature.title}' up")
        else:
            # Move to previous quarter
            self.move_to_previous_quarter(feature)
    
    def move_feature_down(self, feature):
        """Move feature down within quarter or to next quarter"""
        if not self.quarter.features:
            return
        
        current_index = self.quarter.features.index(feature)
        
        if current_index < len(self.quarter.features) - 1:
            # Move down within same quarter
            self.quarter.features[current_index], self.quarter.features[current_index + 1] = \
                self.quarter.features[current_index + 1], self.quarter.features[current_index]
            self.refresh_features()
            self.app.status_var.set(f"Moved '{feature.title}' down")
        else:
            # Move to next quarter
            self.move_to_next_quarter(feature)
    
    def move_to_previous_quarter(self, feature):
        """Move feature to previous quarter"""
        current_quarter_index = self.app.quarters.index(self.quarter)
        
        if current_quarter_index > 0:
            previous_quarter = self.app.quarters[current_quarter_index - 1]
            
            # Remove from current quarter
            if self.quarter.features:
                self.quarter.features.remove(feature)
            
            # Add to previous quarter (at the end)
            if previous_quarter.features is not None:
                previous_quarter.features.append(feature)
            else:
                previous_quarter.features = [feature]
            
            # Refresh both quarters
            self.refresh_features()
            previous_key = f"{previous_quarter.year}_{previous_quarter.quarter}"
            if previous_key in self.app.quarter_frames:
                self.app.quarter_frames[previous_key].refresh_features()
            
            self.app.status_var.set(f"Moved '{feature.title}' to {previous_quarter.name}")
    
    def move_to_next_quarter(self, feature):
        """Move feature to next quarter"""
        current_quarter_index = self.app.quarters.index(self.quarter)
        
        if current_quarter_index < len(self.app.quarters) - 1:
            next_quarter = self.app.quarters[current_quarter_index + 1]
            
            # Remove from current quarter
            if self.quarter.features:
                self.quarter.features.remove(feature)
            
            # Add to next quarter (at the beginning)
            if next_quarter.features is not None:
                next_quarter.features.insert(0, feature)
            else:
                next_quarter.features = [feature]
            
            # Refresh both quarters
            self.refresh_features()
            next_key = f"{next_quarter.year}_{next_quarter.quarter}"
            if next_key in self.app.quarter_frames:
                self.app.quarter_frames[next_key].refresh_features()
            
            self.app.status_var.set(f"Moved '{feature.title}' to {next_quarter.name}")


class FeatureDialog:
    def __init__(self, parent, title, feature=None):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("750x750")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Title
        tk.Label(self.dialog, text="Title:", font=("Arial", 10, "bold")).pack(pady=5)
        self.title_entry = tk.Entry(self.dialog, width=50)
        self.title_entry.pack(pady=5)
        self.title_entry.insert(0, feature.title if feature else "")
        
        # Description
        tk.Label(self.dialog, text="Description:", font=("Arial", 10, "bold")).pack(pady=5)
        self.desc_text = tk.Text(self.dialog, width=50, height=6)
        self.desc_text.pack(pady=5)
        if feature:
            self.desc_text.insert("1.0", feature.description)
        
        # Color
        tk.Label(self.dialog, text="Color:", font=("Arial", 10, "bold")).pack(pady=5)
        color_frame = tk.Frame(self.dialog)
        color_frame.pack(pady=5)
        
        self.color_var = tk.StringVar(value=feature.color if feature else "#2196F3")
        self.color_label = tk.Label(color_frame, width=20, bg=self.color_var.get())
        self.color_label.pack(side=tk.LEFT, padx=5)
        
        tk.Button(color_frame, text="Choose Color", 
                 command=self.choose_color).pack(side=tk.LEFT)
        
        # Buttons
        button_frame = tk.Frame(self.dialog)
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=self.cancel_clicked).pack(side=tk.LEFT, padx=5)
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        self.dialog.wait_window()
    
    def choose_color(self):
        color = colorchooser.askcolor(initialcolor=self.color_var.get())[1]
        if color:
            self.color_var.set(color)
            self.color_label.config(bg=color)
    
    def ok_clicked(self):
        self.result = {
            'title': self.title_entry.get().strip(),
            'description': self.desc_text.get("1.0", tk.END).strip(),
            'color': self.color_var.get()
        }
        if self.result['title']:
            self.dialog.destroy()
    
    def cancel_clicked(self):
        self.dialog.destroy()


class RoadmapApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Software Development Roadmap Builder")
        self.root.geometry("1200x700")
        
        self.quarters = []
        self.quarter_frames = {}
        self.current_file = None
        
        self.setup_ui()
        self.initialize_quarters()
    
    def setup_ui(self):
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self.new_roadmap)
        file_menu.add_command(label="Open", command=self.open_roadmap)
        file_menu.add_command(label="Save", command=self.save_roadmap)
        file_menu.add_command(label="Save As", command=self.save_as_roadmap)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Templates menu
        template_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Templates", menu=template_menu)
        template_menu.add_command(label="Web Application", command=lambda: self.load_template("web"))
        template_menu.add_command(label="Mobile App", command=lambda: self.load_template("mobile"))
        template_menu.add_command(label="API Development", command=lambda: self.load_template("api"))
        
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top controls
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(controls_frame, text="Timeline:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Add Quarter", command=self.add_quarter).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Remove Quarter", command=self.remove_quarter).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Clear All", command=self.clear_all).pack(side=tk.LEFT, padx=5)
        
        # Scrollable area for quarters
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas and scrollbars
        self.canvas = tk.Canvas(canvas_frame, bg="#f0f0f0")
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        
        self.canvas.configure(yscrollcommand=v_scrollbar.set)
        
        # Pack scrollbars and canvas
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Frame to hold quarters
        self.quarters_container = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.quarters_container, anchor="nw")
        
        # Configure scrolling
        self.quarters_container.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def on_frame_configure(self, event):
        """Reset the scroll region to encompass the inner frame"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def on_canvas_configure(self, event):
        """Adjust inner frame width to canvas width"""
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)
    
    def on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def initialize_quarters(self):
        """Initialize with current year quarters"""
        current_year = datetime.datetime.now().year
        current_quarter = (datetime.datetime.now().month - 1) // 3 + 1
        
        # Add current and next 3 quarters
        for i in range(4):
            q = current_quarter + i
            year = current_year
            if q > 4:
                q -= 4
                year += 1
            self.add_quarter_to_ui(Quarter(year, q))
    
    def add_quarter(self):
        """Add a new quarter"""
        if not self.quarters:
            year = datetime.datetime.now().year
            quarter = 1
        else:
            last_quarter = self.quarters[-1]
            if last_quarter.quarter == 4:
                year = last_quarter.year + 1
                quarter = 1
            else:
                year = last_quarter.year
                quarter = last_quarter.quarter + 1
        
        self.add_quarter_to_ui(Quarter(year, quarter))
        self.status_var.set(f"Added {Quarter(year, quarter).name}")
    
    def add_quarter_to_ui(self, quarter: Quarter):
        """Add a quarter to the UI"""
        self.quarters.append(quarter)
        
        # Create frame for this quarter with minimum width
        quarter_frame = QuarterFrame(self.quarters_container, quarter, self)
        quarter_frame.pack(fill=tk.BOTH, padx=5, pady=5)
        quarter_frame.config(width=400)  # Set minimum width
        
        self.quarter_frames[f"{quarter.year}_{quarter.quarter}"] = quarter_frame
        
        # Update scroll region after adding
        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def remove_quarter(self):
        """Remove the last quarter"""
        if self.quarters:
            last_quarter = self.quarters.pop()
            key = f"{last_quarter.year}_{last_quarter.quarter}"
            if key in self.quarter_frames:
                self.quarter_frames[key].destroy()
                del self.quarter_frames[key]
            self.status_var.set(f"Removed {last_quarter.name}")
    
    def clear_all(self):
        """Clear all quarters and features"""
        if messagebox.askyesno("Clear All", "This will remove all quarters and features. Continue?"):
            for quarter_frame in self.quarter_frames.values():
                quarter_frame.destroy()
            self.quarter_frames.clear()
            self.quarters.clear()
            self.status_var.set("Cleared all quarters")
    
    def new_roadmap(self):
        """Create a new roadmap"""
        if self.quarters:
            if messagebox.askyesno("New Roadmap", "Clear current roadmap and start new?"):
                self.clear_all()
                self.initialize_quarters()
                self.current_file = None
                self.status_var.set("New roadmap created")
        else:
            self.current_file = None
            self.status_var.set("New roadmap created")
    
    def open_roadmap(self):
        """Open a roadmap file"""
        filename = filedialog.askopenfilename(
            title="Open Roadmap",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                
                # Clear existing
                self.clear_all()
                self.quarters.clear()
                
                # Load quarters
                for quarter_data in data.get('quarters', []):
                    quarter = Quarter(
                        year=quarter_data['year'],
                        quarter=quarter_data['quarter']
                    )
                    
                    # Load features
                    for feature_data in quarter_data.get('features', []):
                        feature = Feature(
                            id=feature_data['id'],
                            title=feature_data['title'],
                            description=feature_data['description'],
                            completed=feature_data.get('completed', False),
                            color=feature_data.get('color', '#2196F3')
                        )
                        if quarter.features is not None:
                            quarter.features.append(feature)
                        else:
                            quarter.features = [feature]
                    
                    self.add_quarter_to_ui(quarter)
                
                self.current_file = filename
                self.status_var.set(f"Opened: {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file: {e}")
    
    def save_roadmap(self):
        """Save the roadmap"""
        if self.current_file:
            self.save_to_file(self.current_file)
        else:
            self.save_as_roadmap()
    
    def save_as_roadmap(self):
        """Save roadmap to a new file"""
        filename = filedialog.asksaveasfilename(
            title="Save Roadmap",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.save_to_file(filename)
    
    def save_to_file(self, filename):
        """Save roadmap to specific file"""
        try:
            data = {
                'quarters': [
                    {
                        'year': quarter.year,
                        'quarter': quarter.quarter,
                        'features': [
                            {
                                'id': feature.id,
                                'title': feature.title,
                                'description': feature.description,
                                'completed': feature.completed,
                                'color': feature.color
                            }
                            for feature in quarter.features
                        ]
                    }
                    for quarter in self.quarters
                ],
                'created': datetime.datetime.now().isoformat(),
                'version': '2.0'
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.current_file = filename
            self.status_var.set(f"Saved: {os.path.basename(filename)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {e}")
    
    def load_template(self, template_type):
        """Load a predefined template"""
        templates = {
            "web": [
                "Planning & Design",
                "Backend Setup", 
                "Frontend Development",
                "Authentication System",
                "Payment Integration",
                "Testing & QA",
                "Deployment"
            ],
            "mobile": [
                "UI/UX Design",
                "Core Architecture",
                "User Authentication",
                "Main Features",
                "Push Notifications",
                "App Store Submission",
                "Marketing Launch"
            ],
            "api": [
                "API Specification",
                "Database Design",
                "Authentication & Auth",
                "Core Endpoints",
                "Documentation",
                "Testing Suite",
                "Monitoring Setup"
            ]
        }
        
        if template_type in templates:
            if self.quarters:
                if not messagebox.askyesno("Load Template", "This will replace current roadmap. Continue?"):
                    return
            
            # Clear and recreate quarters
            self.clear_all()
            current_year = datetime.datetime.now().year
            
            # Distribute features across quarters
            features = templates[template_type]
            features_per_quarter = 2
            
            num_quarters = (len(features) + features_per_quarter - 1) // features_per_quarter
            
            for i in range(num_quarters):
                quarter = Quarter(current_year, i + 1)
                
                # Add features to this quarter
                start_idx = i * features_per_quarter
                end_idx = min(start_idx + features_per_quarter, len(features))
                
                for j, feature_title in enumerate(features[start_idx:end_idx]):
                    feature = Feature(
                        id=f"feature_{template_type}_{i}_{j}",
                        title=feature_title,
                        description=f"Implementation of {feature_title}",
                        color=["#4CAF50", "#2196F3", "#FF9800", "#9C27B0"][i % 4]
                    )
                    if quarter.features is not None:
                        quarter.features.append(feature)
                    else:
                        quarter.features = [feature]
                
                self.add_quarter_to_ui(quarter)
            
            self.status_var.set(f"Loaded {template_type} template")

def main():
    root = tk.Tk()
    app = RoadmapApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
