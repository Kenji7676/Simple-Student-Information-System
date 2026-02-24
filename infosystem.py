import tkinter as tk
from tkinter import ttk, messagebox
import csv
import os
import re

STUDENT_CSV = "student.csv"
PROGRAM_CSV = "program.csv"
COLLEGE_CSV = "college.csv"

def ensure_csv(file, headers):
    if not os.path.exists(file):
        with open(file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)

ensure_csv(STUDENT_CSV, ["id", "firstname", "lastname", "prog_code", "year", "gender"])
ensure_csv(PROGRAM_CSV, ["prog_code", "name", "college_code"])
ensure_csv(COLLEGE_CSV, ["college_code", "name"])

def read_csv(file):
    try:
        with open(file, newline="") as f:
            return list(csv.DictReader(f))
    except FileNotFoundError: return []

def write_csv(file, data, headers):
    with open(file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)

class StudentDirectoryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Student Directory System")
        self.configure(bg="#f5f5dc")
        
        self.edit_mode = False
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.handle_empty_search)
        
        self.active_filters = {"gender": [], "year": [], "program": [], "college": []}
        self.filter_win = None
        self.add_popup_win = None 
        self.edit_popup_win = None
        self.sidebar = tk.Frame(self, bg="#d2b48c", width=180)
        self.sidebar.pack(side="left", fill="y", padx=10, pady=10)
        self.active_section = tk.StringVar(value="Students")
        for section in ["Students", "Programs", "Colleges"]:
            tk.Radiobutton(self.sidebar, text=section, variable=self.active_section, value=section,
                indicatoron=0, width=15, padx=10, pady=10, bg="#d2b48c", fg="white",
                selectcolor="#8b4513", font=("Arial", 12), 
                command=lambda s=section: self.reset_all_and_switch(s)).pack(pady=5)
        self.content_frame = tk.Frame(self, bg="white")
        self.content_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        self.button_container = tk.Frame(self, bg="#f5f5dc")
        self.button_container.place(relx=0.98, rely=0.95, anchor="se")
        tk.Button(self.button_container, text="+", font=("Arial", 18, "bold"), bg="#8b4513", fg="white", command=self.add_entry_popup, bd=0, width=2).pack(side="left", padx=5)
        self.edit_btn = tk.Button(self.button_container, text="📝", font=("Arial", 18), bg="#d2b48c", fg="white", command=self.toggle_edit_mode, bd=0, width=2)
        self.edit_btn.pack(side="left")
        self.bind_all("<Button-1>", self.check_filter_focus)
        self.center_window(1150, 600)
        self.switch_section("Students")

    def handle_empty_search(self, *args):
        if self.search_var.get() == "":
            self.switch_section(self.active_section.get())

    def toggle_edit_mode(self):
        self.edit_mode = not self.edit_mode
        self.edit_btn.config(bg="#8b4513" if self.edit_mode else "#d2b48c")
        self.switch_section(self.active_section.get())

    def reset_all_and_switch(self, section):
        self.search_var.set("") 
        self.active_filters = {"gender": [], "year": [], "program": [], "college": []}
        self.edit_mode = False
        self.edit_btn.config(bg="#d2b48c")
        self.switch_section(section)

    def center_window(self, width, height):
        x = (self.winfo_screenwidth() // 2) - (width // 2); y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def create_popup_dropdown(self, parent, label, options, is_filter=False, filter_key=None, refresh_callback=None, default_value=""):
        frame = tk.Frame(parent, bg="white")
        frame.pack(fill="x", pady=2)
        tk.Label(frame, text=label, font=("Arial", 8, "bold"), bg="white", fg="#555").pack(anchor="w")
        var = tk.StringVar(value=default_value)
        ent = tk.Entry(frame, textvariable=var, font=("Arial", 10), bg="#f4f4f4", bd=0)
        ent.pack(fill="x", ipady=3)
        drop_outer = tk.Frame(frame, bg="white", highlightbackground="#d2b48c", highlightthickness=1)
        
        canvas = tk.Canvas(drop_outer, bg="white", height=100 if is_filter else 80, highlightthickness=0)
        scrollbar = tk.Scrollbar(drop_outer, orient="vertical", command=canvas.yview)
        drop_inner = tk.Frame(canvas, bg="white")
        canvas.configure(yscrollcommand=scrollbar.set); canvas.create_window((0, 0), window=drop_inner, anchor="nw")
        selected_val = {"val": default_value}; matches = []

        def update_results(*args):
            nonlocal matches
            for child in drop_inner.winfo_children(): child.destroy()
            query = var.get().lower()
            matches = [o for o in options if query in o.lower() and (not is_filter or o not in self.pending_filters[filter_key])]
            if matches:
                drop_outer.pack(fill="x")
                for i, m in enumerate(matches):
                    bg_c = "#8b4513" if (i == 0 and query != "") else "white"
                    fg_c = "white" if (i == 0 and query != "") else "black"
                    tk.Button(drop_inner, text=m, anchor="w", bg=bg_c, fg=fg_c, relief="flat", font=("Arial", 8),
                              command=lambda v=m: select_action(v)).pack(fill="x")
                drop_inner.update_idletasks(); canvas.config(scrollregion=canvas.bbox("all"))
                if len(matches) > 3: scrollbar.pack(side="right", fill="y")
                else: scrollbar.pack_forget()
                canvas.pack(side="left", fill="both", expand=True)
            else: drop_outer.pack_forget()

        def select_action(v):
            if is_filter: self.pending_filters[filter_key].append(v); var.set(""); refresh_callback()
            else: selected_val["val"] = v; var.set(v)
            drop_outer.pack_forget()

        var.trace_add("write", update_results); ent.bind("<FocusIn>", lambda e: update_results())
        ent.bind("<Return>", lambda e: select_action(matches[0]) if matches else None)
        return selected_val, ent

    def switch_section(self, section):
        if section == "Students": self.show_students()
        elif section == "Programs": self.show_programs()
        elif section == "Colleges": self.show_colleges()

    def display_table(self, columns, rows, section_type):
        for w in self.content_frame.winfo_children(): w.destroy()
        header = tk.Frame(self.content_frame, bg="white")
        header.pack(fill="x", pady=10)
        tk.Label(header, text=section_type, font=("Arial", 16, "bold"), bg="white", fg="#8b4513").pack(side="left", padx=10)
        
        ctrls = tk.Frame(header, bg="white")
        ctrls.pack(side="right", padx=10)
        
        if self.edit_mode:
            tk.Button(ctrls, text="Delete Selected", bg="#ff4d4d", fg="white", command=lambda: self.delete_selected(section_type)).pack(side="left", padx=2)
            if section_type == "Students":
                tk.Button(ctrls, text="Edit Selected", bg="#4CAF50", fg="white", command=self.edit_selected_student).pack(side="left", padx=2)
            tk.Button(ctrls, text="Cancel", bg="gray", fg="white", command=self.toggle_edit_mode).pack(side="left", padx=2)
        else:
            s_ent = tk.Entry(ctrls, textvariable=self.search_var, font=("Arial", 10), width=25, bg="#f4f4f4", bd=0)
            s_ent.pack(side="left", padx=5, ipady=3)
            s_ent.bind("<Return>", lambda e: self.switch_section(section_type))
            tk.Button(ctrls, text="Search", bg="#d2b48c", fg="white", command=lambda: self.switch_section(section_type)).pack(side="left", padx=2)
            
            if section_type == "Students":
                f_btn = tk.Button(ctrls, text="Filter ▽", bg="#8b4513", fg="white", padx=12, command=lambda: self.show_filter_menu(f_btn))
                f_btn.pack(side="left", padx=2)

        display_cols = ["Select"] + columns if self.edit_mode else columns
        self.tree = ttk.Treeview(self.content_frame, columns=display_cols, show="headings")
        
        for col in self.tree["columns"]: 
            self.tree.heading(col, text=col)
            if col == "Select":
                self.tree.column(col, width=50, minwidth=50, anchor="center", stretch=False)
            else:
                self.tree.column(col, width=100, minwidth=80, anchor="center", stretch=True)
        
        tree_scroll = ttk.Scrollbar(self.content_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
        tree_scroll.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
        
        if rows:
            for r in rows: self.tree.insert("", "end", values=(["[ ]"] + r if self.edit_mode else r))
        elif self.search_var.get().strip() != "":
            no_res_frame = tk.Frame(self.tree, bg="white")
            no_res_frame.place(relx=0.5, rely=0.4, anchor="center")
            tk.Label(no_res_frame, text="No search results found.", font=("Arial", 12, "italic"), fg="gray", bg="white").pack()
        if self.edit_mode: self.tree.bind("<ButtonRelease-1>", self.on_tree_click)

    def show_students(self):
        d = read_csv(STUDENT_CSV); p_map = {p["prog_code"]: p for p in read_csv(PROGRAM_CSV)}
        c_map = {c["college_code"]: c["name"] for c in read_csv(COLLEGE_CSV)}
        rows = [[s["id"], f"{s['lastname']}, {s['firstname']}", s["gender"], s["year"], p_map.get(s["prog_code"], {}).get("name", "N/A"), c_map.get(p_map.get(s["prog_code"], {}).get("college_code"), "N/A")] for s in d]
        q = self.search_var.get().lower()
        fdata = [r for r in rows if (not q or any(q in str(c).lower() for c in r)) and (not self.active_filters["gender"] or r[2] in self.active_filters["gender"]) and (not self.active_filters["year"] or str(r[3]) in self.active_filters["year"]) and (not self.active_filters["program"] or r[4] in self.active_filters["program"]) and (not self.active_filters["college"] or r[5] in self.active_filters["college"])]
        self.display_table(["ID", "Name", "Gender", "Year", "Program", "College"], fdata, "Students")

    def show_programs(self):
        d = read_csv(PROGRAM_CSV); c_map = {c["college_code"]: c["name"] for c in read_csv(COLLEGE_CSV)}
        rows = [[p["prog_code"], p["name"], c_map.get(p["college_code"], "N/A")] for p in d]
        q = self.search_var.get().lower()
        fdata = [r for r in rows if not q or any(q in str(c).lower() for c in r)]
        self.display_table(["Code", "Program Name", "College"], fdata, "Programs")

    def show_colleges(self):
        d = read_csv(COLLEGE_CSV); rows = [[c["college_code"], c["name"]] for c in d]
        q = self.search_var.get().lower()
        fdata = [r for r in rows if not q or any(q in str(c).lower() for c in r)]
        self.display_table(["Code", "College Name"], fdata, "Colleges")

    def add_entry_popup(self):
        if self.add_popup_win and self.add_popup_win.winfo_exists():
            self.add_popup_win.lift()
            return
        self.add_popup_win = tk.Toplevel(self)
        current = self.active_section.get()
        self.add_popup_win.title(f"Add {current}")
        self.add_popup_win.configure(bg="white")
        self.add_popup_win.transient(self) 
        self.add_popup_win.grab_set()      
        self.center_window_small(self.add_popup_win, 400, 680)
        container = tk.Frame(self.add_popup_win, bg="white", padx=20, pady=20); container.pack(fill="both", expand=True)
        if current == "Students":
            tk.Label(container, text="ID Number", bg="white", font=("Arial", 8, "bold")).pack(anchor="w")
            id_ent = tk.Entry(container, bg="#f4f4f4", bd=0); id_ent.pack(fill="x", pady=(5,0), ipady=3)
            err_msg = tk.Label(container, text="Invalid Input. ID Number must follow the\nformat YYYY-NNNN (e.g. 2024-0001)", font=("Arial", 7, "italic"), fg="red", bg="white", justify="right")
            tk.Label(container, text="First Name", bg="white", font=("Arial", 8, "bold")).pack(anchor="w", pady=(10,0))
            fn_ent = tk.Entry(container, bg="#f4f4f4", bd=0); fn_ent.pack(fill="x", pady=5, ipady=3)
            tk.Label(container, text="Last Name", bg="white", font=("Arial", 8, "bold")).pack(anchor="w")
            ln_ent = tk.Entry(container, bg="#f4f4f4", bd=0); ln_ent.pack(fill="x", pady=5, ipady=3)
            all_programs = read_csv(PROGRAM_CSV); prog_names = sorted([p['name'] for p in all_programs])
            prog_sel, _ = self.create_popup_dropdown(container, "Program", prog_names)
            year_sel, _ = self.create_popup_dropdown(container, "Year Level", ["1", "2", "3", "4", "5"])
            gen_sel, _ = self.create_popup_dropdown(container, "Gender", ["Male", "Female", "Other"])
            def save():
                err_msg.pack_forget()
                raw_id = id_ent.get().strip()
                if not re.match(r"^\d{4}-\d{4}$", raw_id):
                    err_msg.pack(anchor="e"); return
                p_name = prog_sel["val"]; p_code = next((p['prog_code'] for p in all_programs if p['name'] == p_name), "")
                vals = [raw_id, fn_ent.get().title(), ln_ent.get().title(), p_code, year_sel["val"], gen_sel["val"]]
                if any(not v for v in vals): return messagebox.showwarning("!", "Fill all fields")
                data = read_csv(STUDENT_CSV); data.append(dict(zip(["id", "firstname", "lastname", "prog_code", "year", "gender"], vals)))
                write_csv(STUDENT_CSV, data, ["id", "firstname", "lastname", "prog_code", "year", "gender"]); self.show_students(); self.add_popup_win.destroy()
            tk.Button(container, text="SAVE", bg="#8b4513", fg="white", font=("Arial", 10, "bold"), command=save).pack(pady=20)
        elif current == "Programs":
            tk.Label(container, text="Code", bg="white", font=("Arial", 8, "bold")).pack(anchor="w")
            c_ent = tk.Entry(container, bg="#f4f4f4", bd=0); c_ent.pack(fill="x", pady=5, ipady=3)
            tk.Label(container, text="Name", bg="white", font=("Arial", 8, "bold")).pack(anchor="w")
            n_ent = tk.Entry(container, bg="#f4f4f4", bd=0); n_ent.pack(fill="x", pady=5, ipady=3)
            coll_sel, _ = self.create_popup_dropdown(container, "College", [f"{c['college_code']} - {c['name']}" for c in read_csv(COLLEGE_CSV)])
            def save_p():
                cc = coll_sel["val"].split(" - ")[0] if " - " in coll_sel["val"] else ""
                data = read_csv(PROGRAM_CSV); data.append({"prog_code": c_ent.get().upper(), "name": n_ent.get().title(), "college_code": cc})
                write_csv(PROGRAM_CSV, data, ["prog_code", "name", "college_code"]); self.show_programs(); self.add_popup_win.destroy()
            tk.Button(container, text="SAVE", bg="#8b4513", fg="white", font=("Arial", 10, "bold"), command=save_p).pack(pady=20)
        elif current == "Colleges":
            tk.Label(container, text="Code", bg="white", font=("Arial", 8, "bold")).pack(anchor="w")
            c_ent = tk.Entry(container, bg="#f4f4f4", bd=0); c_ent.pack(fill="x", pady=5, ipady=3)
            tk.Label(container, text="Name", bg="white", font=("Arial", 8, "bold")).pack(anchor="w")
            n_ent = tk.Entry(container, bg="#f4f4f4", bd=0); n_ent.pack(fill="x", pady=5, ipady=3)
            def save_c():
                data = read_csv(COLLEGE_CSV); data.append({"college_code": c_ent.get().upper(), "name": n_ent.get().title()})
                write_csv(COLLEGE_CSV, data, ["college_code", "name"]); self.show_colleges(); self.add_popup_win.destroy()
            tk.Button(container, text="SAVE", bg="#8b4513", fg="white", font=("Arial", 10, "bold"), command=save_c).pack(pady=20)

    def edit_selected_student(self):
        selected_items = [item for item in self.tree.get_children() 
                         if self.tree.item(item, "values")[0] == "[X]"]
        
        if not selected_items:
            messagebox.showwarning("Warning", "Please select a student to edit.")
            return
        
        if len(selected_items) > 1:
            messagebox.showwarning("Warning", "Please select only one student to edit.")
            return
        
        selected_values = self.tree.item(selected_items[0], "values")
        student_id = selected_values[1]  
        
        students_data = read_csv(STUDENT_CSV)
        student_data = next((s for s in students_data if s["id"] == student_id), None)
        
        if not student_data:
            messagebox.showerror("Error", "Student data not found.")
            return
        
        self.open_edit_student_popup(student_data)

    def open_edit_student_popup(self, student_data):
        if self.edit_popup_win and self.edit_popup_win.winfo_exists():
            self.edit_popup_win.lift()
            return
            
        self.edit_popup_win = tk.Toplevel(self)
        self.edit_popup_win.title("Edit Student")
        self.edit_popup_win.configure(bg="white")
        self.edit_popup_win.transient(self)
        self.edit_popup_win.grab_set()
        self.center_window_small(self.edit_popup_win, 400, 680)
        
        container = tk.Frame(self.edit_popup_win, bg="white", padx=20, pady=20)
        container.pack(fill="both", expand=True)
        
        tk.Label(container, text="ID Number (Read Only)", bg="white", font=("Arial", 8, "bold")).pack(anchor="w")
        id_ent = tk.Entry(container, bg="#e0e0e0", bd=0, state="readonly")
        id_ent.pack(fill="x", pady=(5,0), ipady=3)
        id_ent.config(state="normal")
        id_ent.insert(0, student_data["id"])
        id_ent.config(state="readonly")
        
        tk.Label(container, text="First Name", bg="white", font=("Arial", 8, "bold")).pack(anchor="w", pady=(10,0))
        fn_ent = tk.Entry(container, bg="#f4f4f4", bd=0)
        fn_ent.pack(fill="x", pady=5, ipady=3)
        fn_ent.insert(0, student_data["firstname"])
        
        tk.Label(container, text="Last Name", bg="white", font=("Arial", 8, "bold")).pack(anchor="w")
        ln_ent = tk.Entry(container, bg="#f4f4f4", bd=0)
        ln_ent.pack(fill="x", pady=5, ipady=3)
        ln_ent.insert(0, student_data["lastname"])
        
        all_programs = read_csv(PROGRAM_CSV)
        prog_names = sorted([p['name'] for p in all_programs])
        current_prog_name = next((p['name'] for p in all_programs if p['prog_code'] == student_data["prog_code"]), "")
        prog_sel, _ = self.create_popup_dropdown(container, "Program", prog_names, default_value=current_prog_name)
        
        year_sel, _ = self.create_popup_dropdown(container, "Year Level", ["1", "2", "3", "4", "5"], default_value=student_data["year"])
        
        gen_sel, _ = self.create_popup_dropdown(container, "Gender", ["Male", "Female", "Other"], default_value=student_data["gender"])
        
        btn_frame = tk.Frame(container, bg="white")
        btn_frame.pack(pady=20)
        
        def save_changes():
            new_firstname = fn_ent.get().title().strip()
            new_lastname = ln_ent.get().title().strip()
            new_gender = gen_sel["val"]
            new_year = year_sel["val"]
            new_prog_name = prog_sel["val"]
            
            if not all([new_firstname, new_lastname, new_gender, new_year, new_prog_name]):
                messagebox.showwarning("Warning", "Please fill all fields.")
                return
            
            new_prog_code = next((p['prog_code'] for p in all_programs if p['name'] == new_prog_name), "")
            if not new_prog_code:
                messagebox.showerror("Error", "Invalid program selected.")
                return
            
            students_data = read_csv(STUDENT_CSV)
            for i, student in enumerate(students_data):
                if student["id"] == student_data["id"]:
                    students_data[i] = {
                        "id": student_data["id"],
                        "firstname": new_firstname,
                        "lastname": new_lastname,
                        "prog_code": new_prog_code,
                        "year": new_year,
                        "gender": new_gender
                    }
                    break
            
            write_csv(STUDENT_CSV, students_data, ["id", "firstname", "lastname", "prog_code", "year", "gender"])
            self.show_students()
            self.edit_popup_win.destroy()
            messagebox.showinfo("Success", "Student information updated successfully!")
        
        def cancel_edit():
            self.edit_popup_win.destroy()
        
        tk.Button(btn_frame, text="SAVE CHANGES", bg="#8b4513", fg="white", 
                 font=("Arial", 10, "bold"), command=save_changes).pack(side="left", padx=5)
        tk.Button(btn_frame, text="CANCEL", bg="gray", fg="white", 
                 font=("Arial", 10, "bold"), command=cancel_edit).pack(side="left", padx=5)

    def show_filter_menu(self, widget):
        if self.filter_win and self.filter_win.winfo_exists():
            self.filter_win.destroy(); self.filter_win = None; return
        self.pending_filters = {k: list(v) for k, v in self.active_filters.items()}
        self.filter_win = tk.Toplevel(self); self.filter_win.withdraw(); self.filter_win.overrideredirect(True)
        w_width, w_height = 330, 480
        app_x, app_y = self.winfo_rootx(), self.winfo_rooty(); app_w, app_h = self.winfo_width(), self.winfo_height()
        start_x = widget.winfo_rootx() - 150; start_y = widget.winfo_rooty() + 30
        if start_x + w_width > app_x + app_w: start_x = (app_x + app_w) - w_width - 10
        if start_x < app_x: start_x = app_x + 10
        if start_y + w_height > app_y + app_h: start_y = (app_y + app_h) - w_height - 10
        self.filter_win.geometry(f"{w_width}x{w_height}+{start_x}+{start_y}"); self.filter_win.deiconify()
        container = tk.Frame(self.filter_win, bg="white", bd=2, relief="groove"); container.pack(fill="both", expand=True)
        tk.Label(container, text="Filters", font=("Arial", 10, "bold"), bg="#8b4513", fg="white", pady=5).pack(fill="x")
        tk.Button(container, text="APPLY FILTERS", bg="#8b4513", fg="white", font=("Arial", 9, "bold"), 
                  command=lambda: [setattr(self, 'active_filters', self.pending_filters), self.show_students(), setattr(self, 'filter_win', None), self.filter_win.destroy()]).pack(side="bottom", pady=15)
        scroll_cont = tk.Frame(container, bg="white"); scroll_cont.pack(fill="both", expand=True)
        c_area = tk.Frame(scroll_cont, bg="white"); c_area.pack(fill="x", padx=5)
        tag_canvas = tk.Canvas(scroll_cont, bg="#f9f9f9", height=0, highlightthickness=0); tag_frame = tk.Frame(tag_canvas, bg="#f9f9f9")
        cl_btn_cont = tk.Frame(scroll_cont, bg="white")
        def refresh_tags():
            for c in tag_frame.winfo_children(): c.destroy()
            total_tags = sum(len(v) for v in self.pending_filters.values())
            [w.destroy() for w in cl_btn_cont.winfo_children()]
            if total_tags > 0:
                tag_canvas.pack(fill="x", padx=10, pady=5)
                cl_btn_cont.pack(fill="x", padx=10)
                tk.Button(cl_btn_cont, text="Clear All ✕", bg="white", fg="#cc0000", font=("Arial", 8, "bold"), bd=0, command=lambda: [self.pending_filters.update({k: [] for k in self.pending_filters}), refresh_tags()]).pack(side="right")
                for k, vs in self.pending_filters.items():
                    for v in vs:
                        t = tk.Frame(tag_frame, bg="#d2b48c", padx=4, pady=1); t.pack(side="left", padx=2, pady=2)
                        tk.Label(t, text=v, bg="#d2b48c", fg="white", font=("Arial", 8)).pack(side="left")
                        tk.Button(t, text="✕", bg="#d2b48c", fg="white", bd=0, command=lambda key=k, val=v: [self.pending_filters[key].remove(val), refresh_tags()]).pack(side="left")
                tag_frame.update_idletasks()
                tag_canvas.config(height=min(tag_frame.winfo_reqheight(), 60))
            else: 
                tag_canvas.pack_forget(); cl_btn_cont.pack_forget()
            tag_canvas.create_window((0, 0), window=tag_frame, anchor="nw"); tag_canvas.config(scrollregion=tag_canvas.bbox("all"))
        self.create_popup_dropdown(c_area, "Gender", ["Male", "Female", "Other"], True, "gender", refresh_tags)
        self.create_popup_dropdown(c_area, "Year Level", ["1", "2", "3", "4", "5"], True, "year", refresh_tags)
        self.create_popup_dropdown(c_area, "Program", sorted(list(set(p["name"] for p in read_csv(PROGRAM_CSV)))), True, "program", refresh_tags)
        self.create_popup_dropdown(c_area, "College", sorted(list(set(c["name"] for c in read_csv(COLLEGE_CSV)))), True, "college", refresh_tags)
        refresh_tags()

    def center_window_small(self, win, w, h):
        x = (self.winfo_screenwidth() // 2) - (w // 2); y = (self.winfo_screenheight() // 2) - (h // 2); win.geometry(f"{w}x{h}+{x}+{y}")

    def check_filter_focus(self, event):
        if self.filter_win and self.filter_win.winfo_exists():
            x, y = event.x_root, event.y_root; fx, fy = self.filter_win.winfo_rootx(), self.filter_win.winfo_rooty()
            fw, fh = self.filter_win.winfo_width(), self.filter_win.winfo_height()
            if not (fx <= x <= fx + fw and fy <= y <= fy + fh): 
                self.filter_win.destroy(); self.filter_win = None

    def on_tree_click(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            vals = list(self.tree.item(item, "values")); vals[0] = "[X]" if vals[0] == "[ ]" else "[ ]"
            self.tree.item(item, values=vals)

    def delete_selected(self, section):
        fn, pk = {"Students": (STUDENT_CSV, "id"), "Programs": (PROGRAM_CSV, "prog_code"), "Colleges": (COLLEGE_CSV, "college_code")}[section]
        head = {"Students": ["id", "firstname", "lastname", "prog_code", "year", "gender"], "Programs": ["prog_code", "name", "college_code"], "Colleges": ["college_code", "name"]}[section]
        data = read_csv(fn); to_del = [self.tree.item(i, "values")[1] for i in self.tree.get_children() if self.tree.item(i, "values")[0] == "[X]"]
        if to_del and messagebox.askyesno("Confirm", f"Delete {len(to_del)} items?"):
            write_csv(fn, [r for r in data if r[pk] not in to_del], head); self.switch_section(section)

if __name__ == "__main__":
    app = StudentDirectoryApp(); app.mainloop()