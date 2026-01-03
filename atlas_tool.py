import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, ttk, colorchooser
import json
import random
import os

class AtlasTool:
    def __init__(self, root):
        self.root = root
        self.root.title("SOT Sprite Editor v13 (Import/Export Enhanced)")

        # --- DATI ---
        self.animations = {} 
        self.current_anim = "Default"
        self.scale = 1  
        self.raw_image = None     
        self.display_image = None 
        
        # Percorso file immagine corrente (per salvarlo nel JSON)
        self.current_image_path = ""
        self.current_atlas_name = "atlas"

        # Gestione Selezione
        self.selected_ids = set() 
        self.tag_colors = {} 

        # Variabili Mouse Drag
        self.drag_data = {"start_x": 0, "start_y": 0, "items_start_pos": {}}

        self.setup_ui()
        self.setup_bindings()
        self.reset_inspector_defaults()

    def setup_ui(self):
        # 1. TOOLBAR
        toolbar = tk.Frame(self.root, bd=1, relief=tk.RAISED)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        tk.Button(toolbar, text="Load Image", command=self.load_image).pack(side=tk.LEFT, padx=2)
        
        # NUOVO BOTTONE IMPORT
        tk.Button(toolbar, text="Import JSON", bg="#e1bee7", command=self.import_json).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Export JSON", command=self.save_json).pack(side=tk.LEFT, padx=2)
        
        tk.Label(toolbar, text="|").pack(side=tk.LEFT, padx=5)
        
        tk.Button(toolbar, text="DELETE ALL QUADS", bg="#ffcccc", fg="red", command=self.delete_all_quads).pack(side=tk.LEFT, padx=2)
        
        tk.Label(toolbar, text="|").pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="Zoom -", command=self.zoom_out).pack(side=tk.LEFT, padx=2)
        self.lbl_zoom = tk.Label(toolbar, text="1x")
        self.lbl_zoom.pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="Zoom +", command=self.zoom_in).pack(side=tk.LEFT, padx=2)
        
        self.lbl_status = tk.Label(toolbar, text=f"Active Tag: {self.current_anim}", fg="blue", font=("Arial", 10, "bold"))
        self.lbl_status.pack(side=tk.RIGHT, padx=10)

        # 2. CONTAINER PRINCIPALE
        main_container = tk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)

        # --- PANNELLO SINISTRO (Canvas) ---
        left_frame = tk.Frame(main_container, bg="#ccc")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.v_scroll = tk.Scrollbar(left_frame, orient=tk.VERTICAL)
        self.h_scroll = tk.Scrollbar(left_frame, orient=tk.HORIZONTAL)

        self.canvas = tk.Canvas(left_frame, bg="#ffffff", cursor="arrow",
                                yscrollcommand=self.v_scroll.set,
                                xscrollcommand=self.h_scroll.set)
        
        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.config(command=self.canvas.xview)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas.bind("<ButtonPress-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)

        # --- PANNELLO DESTRO ---
        self.right_panel = tk.Frame(main_container, width=300, bg="#f0f0f0", bd=2, relief=tk.SUNKEN)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.Y)
        self.right_panel.pack_propagate(False)

        # -- SEZIONE TAGS --
        tk.Label(self.right_panel, text="Tags & Colors", font=("Arial", 10, "bold"), bg="#f0f0f0").pack(pady=5)
        self.tree_frame = tk.Frame(self.right_panel)
        self.tree_frame.pack(fill=tk.BOTH, expand=False, padx=5, pady=0, ipady=30)
        
        columns = ("color", "count")
        self.tag_tree = ttk.Treeview(self.tree_frame, columns=columns, show="tree headings", height=5)
        self.tag_tree.heading("#0", text="Tag Name"); self.tag_tree.column("#0", width=110)
        self.tag_tree.heading("color", text="Color"); self.tag_tree.column("color", width=50)
        self.tag_tree.heading("count", text="#"); self.tag_tree.column("count", width=40)
        
        scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tag_tree.yview)
        self.tag_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tag_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tag_tree.bind("<<TreeviewSelect>>", self.on_tag_tree_select)

        # Pulsanti gestione Tag
        tag_btn_frame = tk.Frame(self.right_panel, bg="#f0f0f0")
        tag_btn_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Button(tag_btn_frame, text="Rename", bg="#ddd", command=self.rename_current_tag).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
        tk.Button(tag_btn_frame, text="Color", bg="#b3e5fc", command=self.pick_tag_color).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
        tk.Button(tag_btn_frame, text="Delete", bg="#ffcccc", command=self.delete_current_tag).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)

        # -- SEZIONE SELEZIONE --
        op_frame = tk.LabelFrame(self.right_panel, text="Selection Operations", bg="#f0f0f0")
        op_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Button(op_frame, text="Move Selection to Tag...", bg="#ffeb3b", command=self.move_selection_to_new_tag).pack(fill=tk.X, padx=5, pady=5)
        tk.Button(op_frame, text="Delete Selected (Del)", bg="#ffcccc", command=self.delete_selected).pack(fill=tk.X, padx=5, pady=2)

        # -- GEOMETRIA --
        geo_frame = tk.LabelFrame(self.right_panel, text="Single Inspector", bg="#f0f0f0")
        geo_frame.pack(fill=tk.X, padx=5, pady=5)
        grid_f = tk.Frame(geo_frame, bg="#f0f0f0"); grid_f.pack(fill=tk.X, padx=5)
        
        tk.Label(grid_f, text="X:", bg="#f0f0f0").grid(row=0, column=0)
        self.entry_x = tk.Entry(grid_f, width=6); self.entry_x.grid(row=0, column=1)
        tk.Label(grid_f, text="Y:", bg="#f0f0f0").grid(row=0, column=2)
        self.entry_y = tk.Entry(grid_f, width=6); self.entry_y.grid(row=0, column=3)
        tk.Label(grid_f, text="W:", bg="#f0f0f0").grid(row=1, column=0)
        self.entry_w = tk.Entry(grid_f, width=6); self.entry_w.grid(row=1, column=1)
        tk.Label(grid_f, text="H:", bg="#f0f0f0").grid(row=1, column=2)
        self.entry_h = tk.Entry(grid_f, width=6); self.entry_h.grid(row=1, column=3)
        tk.Button(geo_frame, text="Update Single", bg="#ddd", command=self.update_single_geometry).pack(fill=tk.X, padx=5, pady=5)

        # -- CLONER --
        clone_frame = tk.LabelFrame(self.right_panel, text="Strip Cloner", bg="#f0f0f0")
        clone_frame.pack(fill=tk.X, padx=5, pady=5)
        c_grid = tk.Frame(clone_frame, bg="#f0f0f0"); c_grid.pack(fill=tk.X)
        tk.Label(c_grid, text="Count:", bg="#f0f0f0").grid(row=0, column=0)
        self.entry_clone_count = tk.Entry(c_grid, width=5); self.entry_clone_count.insert(0, "1"); self.entry_clone_count.grid(row=0, column=1)
        tk.Label(c_grid, text="Off X:", bg="#f0f0f0").grid(row=0, column=2)
        self.entry_off_x = tk.Entry(c_grid, width=5); self.entry_off_x.insert(0, "16"); self.entry_off_x.grid(row=0, column=3)
        tk.Button(clone_frame, text="Clone Strip", bg="#b3e5fc", command=self.clone_strip).pack(fill=tk.X, padx=5, pady=5)

        self.lbl_info = tk.Label(self.right_panel, text="Ready", fg="gray", bg="#f0f0f0", wraplength=280)
        self.lbl_info.pack(side=tk.BOTTOM, pady=10)

    def setup_bindings(self):
        self.root.bind("<Delete>", lambda e: self.delete_selected())
        self.root.bind("<BackSpace>", lambda e: self.delete_selected())

    def reset_inspector_defaults(self):
        self.entry_x.delete(0, tk.END); self.entry_x.insert(0, "0")
        self.entry_y.delete(0, tk.END); self.entry_y.insert(0, "0")
        self.entry_w.delete(0, tk.END); self.entry_w.insert(0, "16")
        self.entry_h.delete(0, tk.END); self.entry_h.insert(0, "16")

    def get_color_for_tag(self, tag_name):
        if tag_name not in self.tag_colors:
            r = random.randint(50, 220); g = random.randint(50, 220); b = random.randint(50, 220)
            self.tag_colors[tag_name] = f"#{r:02x}{g:02x}{b:02x}"
        return self.tag_colors[tag_name]

    # --- LOADING ---
    def load_image_from_path(self, path):
        try:
            self.raw_image = tk.PhotoImage(file=path)
            self.current_image_path = path # Memorizza path
            
            # Estrae nome file senza estensione per usarlo come atlas name default
            base = os.path.basename(path)
            self.current_atlas_name = os.path.splitext(base)[0]
            
            self.scale = 1
            self.refresh_view()
        except Exception as e:
            messagebox.showerror("Image Error", f"Cannot load image:\n{e}")

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.gif")])
        if not file_path: return
        
        # Reset dati se carico nuova immagine manualmente
        self.animations = {}
        self.selected_ids = set()
        self.tag_colors = {}
        
        self.load_image_from_path(file_path)
        self.refresh_tag_tree()

    # --- IMPORT JSON (NUOVO) ---
    def import_json(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not file_path: return

        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            # 1. Parsing Struttura
            # Supportiamo sia la vecchia struttura (solo dict di liste) 
            # che la nuova (con metadati)
            
            anim_data = {}
            loaded_image_path = None
            
            if "animations" in data and "image_path" in data:
                # Nuova struttura v13
                loaded_image_path = data.get("image_path", "")
                self.current_atlas_name = data.get("atlas_name", "atlas")
                
                # Convertiamo la struttura nidificata {Tag: {frames: []}} in quella interna {Tag: []}
                raw_anims = data["animations"]
                for tag, content in raw_anims.items():
                    if "frames" in content:
                        anim_data[tag] = content["frames"]
                    else:
                        # Fallback se formato strano
                        anim_data[tag] = []
            else:
                # Vecchia struttura v1-v12 (Root è il dizionario)
                anim_data = data
                loaded_image_path = None # Non c'era path
            
            # 2. Caricamento Immagine
            if loaded_image_path:
                if os.path.exists(loaded_image_path):
                    self.load_image_from_path(loaded_image_path)
                else:
                    # Prova path relativo rispetto al json
                    json_dir = os.path.dirname(file_path)
                    rel_path = os.path.join(json_dir, os.path.basename(loaded_image_path))
                    if os.path.exists(rel_path):
                        self.load_image_from_path(rel_path)
                    else:
                        messagebox.showwarning("Warning", f"Image file not found:\n{loaded_image_path}\nPlease load image manually.")
            
            # 3. Popolamento Dati
            self.animations = anim_data
            self.selected_ids = set()
            self.tag_colors = {} # Reset colori, li rigenera random o si potrebbero salvare
            
            # Rigenera View (crea i canvas_id necessari)
            self.refresh_view()
            self.refresh_tag_tree()
            
            self.lbl_info.config(text=f"Imported JSON: {len(self.animations)} tags.", fg="blue")

        except Exception as e:
            messagebox.showerror("Import Error", str(e))

    # --- VIEW & DRAW ---
    def refresh_view(self):
        if not self.raw_image: return
        self.lbl_zoom.config(text=f"{self.scale}x")
        self.canvas.delete("all")
        self.display_image = self.raw_image.zoom(self.scale)
        self.draw_checkerboard()
        self.canvas.create_image(0, 0, image=self.display_image, anchor="nw")
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
        self.redraw_rectangles()

    def draw_checkerboard(self):
        vis_w = self.raw_image.width() * self.scale
        vis_h = self.raw_image.height() * self.scale
        check_size = 8 
        for y in range(0, vis_h, check_size):
            for x in range(0, vis_w, check_size):
                if ((x // check_size) + (y // check_size)) % 2 == 1:
                    x2 = min(x + check_size, vis_w); y2 = min(y + check_size, vis_h)
                    self.canvas.create_rectangle(x, y, x2, y2, fill="#e0e0e0", outline="", tags="checker")

    def redraw_rectangles(self):
        new_selected_ids = set()
        self.canvas.delete("saved_rect")
        for anim_name, frames in self.animations.items():
            color = self.get_color_for_tag(anim_name)
            for frame in frames:
                was_selected = frame.get('canvas_id') in self.selected_ids
                self.draw_single_rect(frame, color, was_selected)
                if was_selected: new_selected_ids.add(frame['canvas_id'])
        self.selected_ids = new_selected_ids

    def draw_single_rect(self, frame_data, color, is_selected):
        vis_x = frame_data['x'] * self.scale; vis_y = frame_data['y'] * self.scale
        vis_w = frame_data['w'] * self.scale; vis_h = frame_data['h'] * self.scale
        border_color = "#000000" if is_selected else color
        width = 3 if is_selected else 2
        rect_id = self.canvas.create_rectangle(
            vis_x, vis_y, vis_x + vis_w, vis_y + vis_h,
            outline=border_color, width=width, tags="saved_rect"
        )
        frame_data['canvas_id'] = rect_id

    def update_selection_visuals(self):
        for anim_name, frames in self.animations.items():
            base_color = self.get_color_for_tag(anim_name)
            for frame in frames:
                cid = frame['canvas_id']
                if cid in self.selected_ids:
                    self.canvas.itemconfig(cid, outline="#000000", width=3)
                    self.canvas.tag_raise(cid)
                else:
                    self.canvas.itemconfig(cid, outline=base_color, width=2)

    def zoom_in(self):
        if not self.raw_image: return
        self.scale += 1; self.refresh_view()

    def zoom_out(self):
        if not self.raw_image: return
        if self.scale > 1: self.scale -= 1; self.refresh_view()

    # --- INTERAZIONE ---
    def get_frame_by_pos(self, x, y):
        for anim_name, frames in self.animations.items():
            for idx, frame in enumerate(frames):
                if frame['x'] <= x < frame['x'] + frame['w'] and frame['y'] <= y < frame['y'] + frame['h']:
                    return anim_name, idx, frame
        return None, None, None

    def on_canvas_click(self, event):
        if not self.raw_image: return
        canv_x = self.canvas.canvasx(event.x); canv_y = self.canvas.canvasy(event.y)
        real_x = int(canv_x / self.scale); real_y = int(canv_y / self.scale)

        anim, idx, clicked_frame = self.get_frame_by_pos(real_x, real_y)
        is_shift = (event.state & 0x1) != 0

        if clicked_frame:
            cid = clicked_frame['canvas_id']
            if is_shift:
                if cid in self.selected_ids: self.selected_ids.remove(cid)
                else: self.selected_ids.add(cid)
            else:
                if cid not in self.selected_ids or len(self.selected_ids) > 1:
                    self.selected_ids = {cid}
            self.update_selection_visuals()
            self.update_inspector_from_selection()
            
            self.drag_data["start_x"] = real_x
            self.drag_data["start_y"] = real_y
            self.drag_data["items_start_pos"] = {}
            for a, fs in self.animations.items():
                for f in fs:
                    if f['canvas_id'] in self.selected_ids:
                        self.drag_data["items_start_pos"][f['canvas_id']] = (f['x'], f['y'])
        else:
            if not is_shift:
                self.selected_ids = set(); self.update_selection_visuals()
                try:
                    w = int(self.entry_w.get()); h = int(self.entry_h.get())
                    img_w = self.raw_image.width(); img_h = self.raw_image.height()
                    if real_x < 0: real_x = 0; 
                    if real_y < 0: real_y = 0
                    if real_x + w > img_w: real_x = img_w - w
                    if real_y + h > img_h: real_y = img_h - h
                    
                    duplicate = False
                    for a, fs in self.animations.items():
                        for f in fs:
                            if f['x'] == real_x and f['y'] == real_y and f['w'] == w and f['h'] == h: duplicate = True
                    
                    if not duplicate:
                        if self.current_anim not in self.animations: self.animations[self.current_anim] = []
                        new_data = {"x": real_x, "y": real_y, "w": w, "h": h}
                        self.animations[self.current_anim].append(new_data)
                        color = self.get_color_for_tag(self.current_anim)
                        self.draw_single_rect(new_data, color, True) 
                        self.selected_ids = {new_data['canvas_id']}
                        self.refresh_tag_tree()
                except: pass

    def on_canvas_drag(self, event):
        if not self.selected_ids: return
        canv_x = self.canvas.canvasx(event.x); canv_y = self.canvas.canvasy(event.y)
        mouse_real_x = int(canv_x / self.scale); mouse_real_y = int(canv_y / self.scale)

        delta_x = mouse_real_x - self.drag_data["start_x"]
        delta_y = mouse_real_y - self.drag_data["start_y"]
        img_w = self.raw_image.width(); img_h = self.raw_image.height()

        for anim_name, frames in self.animations.items():
            for frame in frames:
                cid = frame['canvas_id']
                if cid in self.selected_ids and cid in self.drag_data["items_start_pos"]:
                    orig_x, orig_y = self.drag_data["items_start_pos"][cid]
                    new_x = orig_x + delta_x; new_y = orig_y + delta_y
                    if new_x < 0: new_x = 0
                    if new_y < 0: new_y = 0
                    if new_x + frame['w'] > img_w: new_x = img_w - frame['w']
                    if new_y + frame['h'] > img_h: new_y = img_h - frame['h']
                    frame['x'] = new_x; frame['y'] = new_y
                    vis_x = new_x * self.scale; vis_y = new_y * self.scale
                    self.canvas.coords(cid, vis_x, vis_y, vis_x + frame['w']*self.scale, vis_y + frame['h']*self.scale)

        if len(self.selected_ids) == 1: self.update_inspector_from_selection()

    def on_canvas_release(self, event): pass

    # --- TAGS ---
    def refresh_tag_tree(self):
        for item in self.tag_tree.get_children(): self.tag_tree.delete(item)
        for tag, frames in self.animations.items():
            color = self.get_color_for_tag(tag)
            self.tag_tree.insert("", "end", iid=tag, text=tag, values=(color, len(frames)))

    def on_tag_tree_select(self, event):
        sel = self.tag_tree.selection()
        if not sel: return
        tag = sel[0]
        self.current_anim = tag
        self.lbl_status.config(text=f"Active Tag: {tag}")
        self.selected_ids = set()
        if tag in self.animations:
            for f in self.animations[tag]: self.selected_ids.add(f.get('canvas_id'))
        self.update_selection_visuals()

    def rename_current_tag(self):
        sel = self.tag_tree.selection()
        if not sel: return
        old = sel[0]
        new = simpledialog.askstring("Rename", f"Rename {old}", initialvalue=old)
        if new and new != old and new not in self.animations:
            self.animations[new] = self.animations.pop(old)
            if old in self.tag_colors: self.tag_colors[new] = self.tag_colors.pop(old)
            self.current_anim = new
            self.refresh_tag_tree(); self.refresh_view()

    def delete_current_tag(self):
        sel = self.tag_tree.selection()
        if not sel: return
        tag = sel[0]
        if messagebox.askyesno("Confirm", f"Delete {tag}?"):
            if tag in self.animations:
                for f in self.animations[tag]: self.canvas.delete(f['canvas_id'])
                del self.animations[tag]
            self.refresh_tag_tree()

    def pick_tag_color(self):
        sel = self.tag_tree.selection()
        if not sel: return
        tag = sel[0]
        curr = self.tag_colors.get(tag, "#fff")
        _, hex = colorchooser.askcolor(color=curr, title=f"Color for {tag}")
        if hex:
            self.tag_colors[tag] = hex
            self.refresh_tag_tree(); self.refresh_view()

    def move_selection_to_new_tag(self):
        if not self.selected_ids: return
        new = simpledialog.askstring("Tag", "New tag name:")
        if not new: return
        to_move = []
        for tag in list(self.animations.keys()):
            kept = []
            for f in self.animations[tag]:
                if f.get('canvas_id') in self.selected_ids: to_move.append(f)
                else: kept.append(f)
            self.animations[tag] = kept
        if new not in self.animations: self.animations[new] = []
        for f in to_move: self.animations[new].append(f)
        self.get_color_for_tag(new); self.current_anim = new
        self.refresh_tag_tree(); self.update_selection_visuals()

    def delete_selected(self):
        if not self.selected_ids: return
        for tag in list(self.animations.keys()):
            self.animations[tag] = [f for f in self.animations[tag] if f.get('canvas_id') not in self.selected_ids]
            for item in self.canvas.find_all():
                if item in self.selected_ids: self.canvas.delete(item)
        self.selected_ids = set()
        self.refresh_tag_tree()

    def delete_all_quads(self):
        if messagebox.askyesno("Confirm", "Delete ALL?"):
            self.animations = {}; self.selected_ids = set()
            self.refresh_view(); self.refresh_tag_tree()

    # --- OPS ---
    def update_inspector_from_selection(self):
        if len(self.selected_ids) == 1:
            cid = list(self.selected_ids)[0]
            for tag, frames in self.animations.items():
                for f in frames:
                    if f['canvas_id'] == cid:
                        self.entry_x.delete(0, tk.END); self.entry_x.insert(0, str(f['x']))
                        self.entry_y.delete(0, tk.END); self.entry_y.insert(0, str(f['y']))
                        self.entry_w.delete(0, tk.END); self.entry_w.insert(0, str(f['w']))
                        self.entry_h.delete(0, tk.END); self.entry_h.insert(0, str(f['h']))
                        self.entry_off_x.delete(0, tk.END); self.entry_off_x.insert(0, str(f['w']))
                        return

    def update_single_geometry(self):
        if len(self.selected_ids) != 1: return
        try:
            nx = int(self.entry_x.get()); ny = int(self.entry_y.get())
            nw = int(self.entry_w.get()); nh = int(self.entry_h.get())
            cid = list(self.selected_ids)[0]
            for tag, frames in self.animations.items():
                for f in frames:
                    if f['canvas_id'] == cid:
                        f['x'] = nx; f['y'] = ny; f['w'] = nw; f['h'] = nh; break
            self.refresh_view()
        except: pass

    def clone_strip(self):
        if not self.selected_ids: return
        ref, ref_tag = None, None
        for tag, frames in self.animations.items():
            for f in frames:
                if f['canvas_id'] in self.selected_ids: ref = f; ref_tag = tag; break
            if ref: break
        if not ref: return
        try:
            count = int(self.entry_clone_count.get()); off_x = int(self.entry_off_x.get())
            curr_x = ref['x']; curr_y = ref['y']; w, h = ref['w'], ref['h']
            img_w = self.raw_image.width()
            self.selected_ids = set()
            for i in range(count):
                curr_x += off_x
                if curr_x + w > img_w: curr_x = 0; curr_y += h
                dup = False
                for f in self.animations[ref_tag]:
                    if f['x'] == curr_x and f['y'] == curr_y: dup = True
                if not dup:
                    self.animations[ref_tag].append({"x": curr_x, "y": curr_y, "w": w, "h": h})
            
            self.refresh_view(); self.refresh_tag_tree()
            if self.animations[ref_tag]:
                last = self.animations[ref_tag][-1]
                self.selected_ids = {last['canvas_id']}
                self.update_selection_visuals(); self.update_inspector_from_selection()
        except: pass

    # --- SAVE (EXPORT v13) ---
    def save_json(self):
        if not self.animations: return
        
        # 1. Costruzione Struttura Dati Completa
        out_data = {
            "atlas_name": self.current_atlas_name,
            "image_path": self.current_image_path,
            "animations": {}
        }

        for tag, frames in self.animations.items():
            if not frames: continue
            
            clean_frames = []
            for f in frames:
                clean_frames.append({
                    "x": f["x"], "y": f["y"], "w": f["w"], "h": f["h"]
                })
            
            out_data["animations"][tag] = {
                "frame_count": len(clean_frames),
                "frames": clean_frames
            }

        # 2. Scrittura Personalizzata per "One-Liner Frames"
        # Usiamo json.dumps per creare la stringa base, ma per le liste di frame
        # vogliamo evitare i newlines interni.
        
        # Approccio manuale per la formattazione:
        # Serializziamo l'oggetto principale con indentazione, poi "compattiamo" le liste dei frame con regex o string manipulation
        # Oppure costruiamo la stringa noi per la parte 'frames'.
        
        # Metodo semplice ed efficace: Post-Processing stringa JSON
        # Cerchiamo pattern che assomigliano a oggetti frame e rimuoviamo i newline al loro interno.
        
        json_str = json.dumps(out_data, indent=4)
        
        # Trucco: "Compact" Frames. 
        # Convertiamo:
        # {
        #     "x": 0,
        #     "y": 0,
        #     "w": 16,
        #     "h": 16
        # }
        # in: { "x": 0, "y": 0, "w": 16, "h": 16 }
        
        import re
        # Regex per trovare blocchi graffe contenenti x,y,w,h e rimuovere whitespace
        def compact_match(match):
            text = match.group(0)
            # Rimuove newline e spazi multipli, lascia spazi singoli
            compacted = re.sub(r'\s+', ' ', text)
            # Sistema spaziature attorno alle graffe
            compacted = compacted.replace('{ ', '{').replace(' }', '}')
            return compacted

        # Pattern: cerca un oggetto JSON che ha le chiavi x, y, w, h
        # Questo pattern è un po' fragile, ma funziona per il formato standard di json.dump
        pattern = r'\{\s+"x": \d+,\s+"y": \d+,\s+"w": \d+,\s+"h": \d+\s+\}'
        
        json_str_compact = re.sub(pattern, compact_match, json_str)
        
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if file_path:
            with open(file_path, "w") as f:
                f.write(json_str_compact)
            messagebox.showinfo("Export Success", f"Saved to {file_path}")

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1200x800") 
    app = AtlasTool(root)
    root.mainloop()