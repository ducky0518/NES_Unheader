import customtkinter
import tkinter
from tkinter import filedialog, messagebox
import os
import zipfile
import threading
import queue
import time # For small delays if needed

# --- Core NES ROM Functions (identical to before) ---
def is_nes_header(byte_data):
    if not byte_data or len(byte_data) < 16:
        return False
    return byte_data[0:4] == b'NES\x1a'

def unheader_rom_data(byte_data):
    if is_nes_header(byte_data):
        return byte_data[16:]
    return None

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("NES Unheader Tool (by -God-like)")
        self.geometry("700x650") # Adjusted size
        customtkinter.set_appearance_mode("System")  # Modes: "System" (default), "Dark", "Light"
        customtkinter.set_default_color_theme("blue")  # Themes: "blue" (default), "green", "dark-blue"

        self.rom_files_details = []
        self.stop_scan_flag = False
        self.stop_conversion_flag = False
        self.ui_queue = queue.Queue() # For thread communication

        self.create_widgets()
        self.update_button_states()
        self.process_ui_queue() # Start queue polling

    def create_widgets(self):
        self.grid_columnconfigure(1, weight=1)

        # --- Input Path ---
        self.input_path_label = customtkinter.CTkLabel(self, text="Input ROMs Directory:")
        self.input_path_label.grid(row=0, column=0, padx=10, pady=(10,5), sticky="w")
        self.input_path_var = tkinter.StringVar()
        self.input_path_entry = customtkinter.CTkEntry(self, textvariable=self.input_path_var, state="readonly", width=350)
        self.input_path_entry.grid(row=0, column=1, padx=10, pady=(10,5), sticky="ew")
        self.input_browse_button = customtkinter.CTkButton(self, text="Browse", command=self.select_input_dir)
        self.input_browse_button.grid(row=0, column=2, padx=10, pady=(10,5))

        # --- Output Path ---
        self.output_path_label = customtkinter.CTkLabel(self, text="Output Directory:")
        self.output_path_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.output_path_var = tkinter.StringVar()
        self.output_path_entry = customtkinter.CTkEntry(self, textvariable=self.output_path_var, state="readonly", width=350)
        self.output_path_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.output_browse_button = customtkinter.CTkButton(self, text="Browse", command=self.select_output_dir)
        self.output_browse_button.grid(row=1, column=2, padx=10, pady=5)

        # --- Scan Buttons ---
        self.scan_button = customtkinter.CTkButton(self, text="Scan for Headered ROMs", command=self.start_scan_thread)
        self.scan_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        self.stop_scan_button = customtkinter.CTkButton(self, text="Stop Scanning", command=self.trigger_stop_scan, fg_color="red", hover_color="#C00000")
        # self.stop_scan_button.grid(row=2, column=1, padx=10, pady=10, sticky="ew") # Will be managed by show/hide

        # --- File List ---
        self.listbox_label = customtkinter.CTkLabel(self, text="Headered ROMs to be processed (Alphabetical):")
        self.listbox_label.grid(row=3, column=0, columnspan=3, padx=10, pady=(10,0), sticky="w")
        
        self.listbox_frame = customtkinter.CTkFrame(self)
        self.listbox_frame.grid(row=4, column=0, columnspan=3, padx=10, pady=5, sticky="nsew")
        self.listbox_frame.grid_rowconfigure(0, weight=1)
        self.listbox_frame.grid_columnconfigure(0, weight=1)
        
        self.listbox = tkinter.Listbox(self.listbox_frame, height=15, selectmode=tkinter.SINGLE) # Or EXTENDED
        self.listbox.grid(row=0, column=0, sticky="nsew", padx=(0,0), pady=(0,0)) 
        
        self.listbox_scrollbar_y = customtkinter.CTkScrollbar(self.listbox_frame, command=self.listbox.yview)
        self.listbox_scrollbar_y.grid(row=0, column=1, sticky="ns")
        self.listbox.configure(yscrollcommand=self.listbox_scrollbar_y.set)
        
        self.listbox_scrollbar_x = customtkinter.CTkScrollbar(self.listbox_frame, command=self.listbox.xview, orientation="horizontal")
        self.listbox_scrollbar_x.grid(row=1, column=0, sticky="ew")
        self.listbox.configure(xscrollcommand=self.listbox_scrollbar_x.set)


        # --- Convert Buttons ---
        self.convert_button = customtkinter.CTkButton(self, text="Convert Selected ROMs", command=self.start_conversion_thread)
        self.convert_button.grid(row=5, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        self.stop_convert_button = customtkinter.CTkButton(self, text="Stop Conversion", command=self.trigger_stop_conversion, fg_color="red", hover_color="#C00000")
        # self.stop_convert_button.grid(row=5, column=1, padx=10, pady=10, sticky="ew") # Will be managed

        # --- Progress Bar & Status ---
        self.progress_label = customtkinter.CTkLabel(self, text="Progress:")
        self.progress_label.grid(row=6, column=0, padx=10, pady=5, sticky="w")
        self.progressbar = customtkinter.CTkProgressBar(self)
        self.progressbar.set(0)
        self.progressbar.grid(row=6, column=1, columnspan=2, padx=10, pady=5, sticky="ew")

        self.status_label = customtkinter.CTkLabel(self, text="Status: Idle", anchor="w")
        self.status_label.grid(row=7, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        
        self.grid_rowconfigure(4, weight=1) # Make listbox frame expand

    def select_input_dir(self):
        path = filedialog.askdirectory()
        if path:
            self.input_path_var.set(path)
            self.rom_files_details.clear() 
            self.listbox.delete(0, tkinter.END)
            self.update_button_states()

    def select_output_dir(self):
        path = filedialog.askdirectory()
        if path:
            self.output_path_var.set(path)
            self.update_button_states()

    def update_status(self, message):
        self.status_label.configure(text=f"Status: {message}")

    def update_button_states(self, is_scanning=False, is_converting=False):
        input_ok = bool(self.input_path_var.get())
        output_ok = bool(self.output_path_var.get())
        files_found = bool(self.rom_files_details)

        # Scan Button
        self.scan_button.configure(state="disabled" if (is_scanning or is_converting or not input_ok) else "normal")
        if is_scanning:
            self.scan_button.grid_remove()
            self.stop_scan_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        else:
            self.stop_scan_button.grid_remove()
            self.scan_button.grid() 
        
        # Convert Button
        self.convert_button.configure(state="disabled" if (is_converting or is_scanning or not (input_ok and output_ok and files_found)) else "normal")
        if is_converting:
            self.convert_button.grid_remove()
            self.stop_convert_button.grid(row=5, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        else:
            self.stop_convert_button.grid_remove()
            self.convert_button.grid()

        # Path Selection - CTkEntry uses 'disabled' or 'normal' for state to control editability
        # To make it look readonly but still copyable, one might use disabled and update text via StringVar
        # For simplicity, 'disabled' blocks interaction entirely. If text needs to be changed, temporarily set to 'normal'.
        path_interaction_state = "disabled" if (is_scanning or is_converting) else "normal"
        self.input_path_entry.configure(state=path_interaction_state)
        self.input_browse_button.configure(state=path_interaction_state)
        self.output_path_entry.configure(state=path_interaction_state)
        self.output_browse_button.configure(state=path_interaction_state)


    def trigger_stop_scan(self):
        self.stop_scan_flag = True
        self.update_status("Stop signal received for scan...")

    def trigger_stop_conversion(self):
        self.stop_conversion_flag = True
        self.update_status("Stop signal received for conversion...")

    def start_scan_thread(self):
        self.stop_scan_flag = False
        self.rom_files_details.clear()
        self.listbox.delete(0, tkinter.END)
        self.update_status("Initiating scan...")
        self.update_button_states(is_scanning=True)
        self.progressbar.set(0)

        scan_thread = threading.Thread(target=self._scan_roms_worker, 
                                       args=(self.input_path_var.get(), self.ui_queue),
                                       daemon=True)
        scan_thread.start()

    def _scan_roms_worker(self, input_dir, q):
        local_rom_files_found = [] 
        files_checked_count = 0
        scan_stopped_early = False

        try:
            potential_files_to_scan = []
            q.put(("status", "Gathering file list..."))
            time.sleep(0.01) 

            for root, _, files in os.walk(input_dir):
                if self.stop_scan_flag: scan_stopped_early = True; break
                for file_idx, file in enumerate(files):
                    if self.stop_scan_flag: scan_stopped_early = True; break
                    if file.lower().endswith((".nes", ".zip")):
                        potential_files_to_scan.append(os.path.join(root, file))
                    if file_idx % 100 == 0 and self.stop_scan_flag: 
                        scan_stopped_early = True; break
                if self.stop_scan_flag: scan_stopped_early = True; break
            
            total_potential_files = len(potential_files_to_scan)
            q.put(("scan_total_potential", total_potential_files))


            if not scan_stopped_early:
                for i, full_path in enumerate(potential_files_to_scan):
                    if self.stop_scan_flag:
                        scan_stopped_early = True
                        q.put(("status", f"Scan stopped. Processed {i} of {total_potential_files}"))
                        break
                    
                    files_checked_count += 1
                    short_path_display = os.path.relpath(full_path, input_dir)
                    q.put(("status", f"Scanning ({files_checked_count}/{total_potential_files}): {short_path_display[:50]}..."))
                    time.sleep(0.001) 

                    if full_path.lower().endswith(".nes"):
                        try:
                            with open(full_path, 'rb') as f: header_bytes = f.read(16)
                            if is_nes_header(header_bytes):
                                display_name = os.path.relpath(full_path, input_dir)
                                local_rom_files_found.append({'display_name': display_name, 'type': 'nes', 'full_path': full_path, 'zip_entry_name': None})
                        except Exception: pass 

                    elif full_path.lower().endswith(".zip"):
                        try:
                            with zipfile.ZipFile(full_path, 'r') as archive:
                                for entry_info in archive.infolist():
                                    if self.stop_scan_flag: break
                                    if entry_info.filename.lower().endswith(".nes") and not entry_info.is_dir():
                                        try:
                                            with archive.open(entry_info.filename, 'r') as f_entry: header_bytes = f_entry.read(16)
                                            if is_nes_header(header_bytes):
                                                display_name = f"{os.path.relpath(full_path, input_dir)} -> {entry_info.filename}"
                                                local_rom_files_found.append({'display_name': display_name, 'type': 'zip', 'full_path': full_path, 'zip_entry_name': entry_info.filename})
                                        except Exception : pass
                                if self.stop_scan_flag: break
                        except Exception: pass 
            
            if scan_stopped_early:
                q.put(("status", f"Scan stopped. Found {len(local_rom_files_found)} headered ROM(s) so far."))
            else:
                q.put(("status", f"Scan complete. Found {len(local_rom_files_found)} headered ROM(s)."))
            
            q.put(("scan_results", local_rom_files_found))

        except Exception as e:
            q.put(("status", f"Error during scan: {e}"))
            q.put(("scan_results", [])) 
        finally:
            q.put(("scan_finished", None))


    def start_conversion_thread(self):
        if not self.rom_files_details:
            messagebox.showinfo("No ROMs", "No headered ROMs to convert.")
            return
        
        self.stop_conversion_flag = False
        self.update_status("Starting conversion (alphabetical order)...")
        self.update_button_states(is_converting=True)
        self.progressbar.set(0)

        roms_to_convert = list(self.rom_files_details)

        conv_thread = threading.Thread(target=self._convert_roms_worker,
                                       args=(self.output_path_var.get(), roms_to_convert, self.ui_queue),
                                       daemon=True)
        conv_thread.start()

    def _convert_roms_worker(self, output_dir, roms_list, q):
        processed_count = 0
        converted_count = 0
        error_count = 0
        total_to_convert = len(roms_list)
        conversion_stopped_early = False

        try:
            for i, rom_info in enumerate(roms_list):
                if self.stop_conversion_flag:
                    conversion_stopped_early = True
                    processed_count = i 
                    break
                
                processed_count = i + 1
                q.put(("status", f"Converting ({processed_count}/{total_to_convert}): {rom_info['display_name'][:50]}..."))
                # CORRECTED LINE: Bundle progress data into a tuple for the second element
                q.put(("progress", (processed_count, total_to_convert))) 
                time.sleep(0.01) 

                try:
                    rom_data = None
                    if rom_info['type'] == 'nes':
                        with open(rom_info['full_path'], 'rb') as f: rom_data = f.read()
                    elif rom_info['type'] == 'zip':
                        with zipfile.ZipFile(rom_info['full_path'], 'r') as archive:
                            with archive.open(rom_info['zip_entry_name'], 'r') as f_entry: rom_data = f_entry.read()

                    if rom_data:
                        unheadered_data = unheader_rom_data(rom_data)
                        if unheadered_data:
                            base_filename = os.path.basename(rom_info['zip_entry_name'] if rom_info['type'] == 'zip' else rom_info['full_path'])
                            output_filepath = os.path.join(output_dir, base_filename)
                            with open(output_filepath, 'wb') as f_out: f_out.write(unheadered_data)
                            converted_count += 1
                        else: error_count += 1
                    else: error_count += 1
                except Exception:
                    error_count += 1
            
            summary_msg = ""
            if conversion_stopped_early:
                summary_msg = f"Conversion stopped. Attempted: {processed_count}, Converted: {converted_count}, Errors: {error_count}."
            else: # Normal completion
                # Ensure processed_count reflects total if not stopped early and list was processed
                if not conversion_stopped_early and total_to_convert > 0 : processed_count = total_to_convert
                summary_msg = f"Conversion Complete! Attempted: {processed_count}, Converted: {converted_count}, Errors: {error_count}."
            
            q.put(("status", summary_msg))
            q.put(("conversion_summary", summary_msg))

        except Exception as e:
            q.put(("status", f"Error during conversion: {e}"))
            q.put(("conversion_summary", f"Conversion failed with error: {e}"))
        finally:
            q.put(("conversion_finished", None))


    def process_ui_queue(self):
        try:
            while True: 
                msg_type, data = self.ui_queue.get_nowait()

                if msg_type == "status":
                    self.update_status(data)
                elif msg_type == "scan_total_potential":
                    pass 
                elif msg_type == "scan_results":
                    self.rom_files_details = data
                    self.rom_files_details.sort(key=lambda item: item['display_name'].lower())
                    self.listbox.delete(0, tkinter.END)
                    for item in self.rom_files_details:
                        self.listbox.insert(tkinter.END, item['display_name'])
                elif msg_type == "scan_finished":
                    self.stop_scan_flag = False 
                    self.update_button_states(is_scanning=False)
                elif msg_type == "progress":
                    current, total = data # 'data' is now expected to be (current_count, total_count)
                    if total > 0:
                        self.progressbar.set(float(current) / total)
                    else:
                        self.progressbar.set(0)
                elif msg_type == "conversion_summary":
                    messagebox.showinfo("Conversion Process Finished", data)
                elif msg_type == "conversion_finished":
                    self.stop_conversion_flag = False 
                    self.update_button_states(is_converting=False)
                    if not self.rom_files_details and self.progressbar.get() == 0: # Only reset progress if it was never started
                         self.progressbar.set(0)


        except queue.Empty:
            pass 
        finally:
            self.after(100, self.process_ui_queue) 


if __name__ == "__main__":
    app = App()
    app.mainloop()