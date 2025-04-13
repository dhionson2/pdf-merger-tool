import pathlib
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from pypdf import PdfReader, PdfWriter
from .merger import merge_pdfs_with_summary_and_cover

class PdfMergerGUI(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master, padding=20)
        self.master.title("PDF Merger Profissional")
        self.master.geometry("860x600")
        self.master.configure(bg="#FAFAFA")
        self.pack(fill="both", expand=True)

        self.folder: pathlib.Path | None = None
        self.pdf_files: list[pathlib.Path] = []

        self.title_var = tk.StringVar()
        self.subtitle_var = tk.StringVar()

        self._setup_styles()
        self._build_widgets()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#FAFAFA")
        style.configure("TLabel", background="#FAFAFA", foreground="#2D3436", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"), foreground="#4A90E2", background="#FAFAFA")

        style.configure("Modern.TButton",
                        font=("Segoe UI", 10, "bold"),
                        padding=10,
                        borderwidth=0,
                        relief="flat",
                        background="#4A90E2",
                        foreground="white")

        style.map("Modern.TButton",
                  background=[("active", "#3b7dc4"), ("!active", "#4A90E2")],
                  foreground=[("active", "white"), ("!active", "white")])

    def _styled_entry(self, parent, textvar):
        entry_bg = tk.Frame(parent, bg="#E0E0E0", bd=0, relief="flat")
        entry_bg.pack(fill="x", pady=5)
        entry = tk.Entry(entry_bg, textvariable=textvar, font=("Segoe UI", 10), bg="white",
                         relief="flat", highlightthickness=1, highlightbackground="#DDD", highlightcolor="#4A90E2")
        entry.pack(fill="x", ipady=8, padx=2)
        return entry

    def _build_widgets(self):
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)

        left_frame = ttk.Frame(container, width=540)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        right_frame = ttk.Frame(container, width=300)
        right_frame.pack(side="right", fill="y")

        # Etapa 1: seleção da pasta
        ttk.Label(left_frame, text="1. Selecione a pasta com os PDFs", style="Header.TLabel").pack(anchor="w")
        self.btn_select = ttk.Button(left_frame, text="📁 Selecionar Pasta", command=self.select_folder, style="Modern.TButton")
        self.btn_select.pack(fill="x", pady=(5, 15))

        # Etapa 2: Título
        ttk.Label(left_frame, text="2. Título da Capa (usado também no nome do arquivo)", style="Header.TLabel").pack(anchor="w")
        self._styled_entry(left_frame, self.title_var)
        self.title_var.trace_add("write", self.update_preview)

        # Etapa 3: Subtítulo (opcional)
        ttk.Label(left_frame, text="3. Subtítulo (opcional)", style="Header.TLabel").pack(anchor="w")
        self._styled_entry(left_frame, self.subtitle_var)
        self.subtitle_var.trace_add("write", self.update_preview)

        # Etapa 4: arquivos encontrados
        ttk.Label(left_frame, text="4. Arquivos encontrados", style="Header.TLabel").pack(anchor="w")
        self.listbox = tk.Listbox(left_frame, font=("Segoe UI", 9), height=12, selectmode="extended", bg="white", borderwidth=1, relief="solid")
        self.scroll = ttk.Scrollbar(left_frame, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=self.scroll.set)
        self.listbox.pack(fill="both", expand=True, side="left")
        self.scroll.pack(side="right", fill="y")

        self.label_count = ttk.Label(left_frame, text="0 arquivo(s) encontrados")
        self.label_count.pack(anchor="w", pady=(5, 5))

        # Etapa 5: excluir selecionado
        self.btn_delete = ttk.Button(left_frame, text="🗑️ Excluir selecionado", command=self.delete_selected, style="Modern.TButton", state="disabled")
        self.btn_delete.pack(fill="x", pady=(0, 15))

        # Preview da capa
        ttk.Label(right_frame, text="Preview da Capa", style="Header.TLabel").pack(anchor="center", pady=(10, 5))
        self.canvas_preview = tk.Canvas(right_frame, width=280, height=380, bg="white", highlightthickness=2, highlightbackground="#4A90E2")
        self.canvas_preview.pack(pady=5)
        self.update_preview()

        # Etapa 6: gerar PDF abaixo do preview
        self.btn_generate = ttk.Button(right_frame, text="🖨️ Gerar PDF completo", command=self.generate_pdf, style="Modern.TButton", state="disabled")
        self.btn_generate.pack(pady=(15, 10), fill="x")

    def update_preview(self, *_):
        self.canvas_preview.delete("all")
        title = self.title_var.get().strip()
        subtitle = self.subtitle_var.get().strip()

        if not title:
            title = "(Título)"

        self.canvas_preview.create_text(140, 180, text=title, font=("Segoe UI", 14, "bold"), fill="#2D3436", anchor="center")
        if subtitle:
            self.canvas_preview.create_text(140, 210, text=subtitle, font=("Segoe UI", 10), fill="#636e72", anchor="center")

    def select_folder(self):
        path = filedialog.askdirectory(title="Selecione a pasta com os PDFs")
        if not path:
            return
        self.folder = pathlib.Path(path)
        self.load_pdfs()

    def load_pdfs(self):
        self.pdf_files = sorted(self.folder.glob("*.pdf"))
        self.listbox.delete(0, tk.END)
        for pdf in self.pdf_files:
            self.listbox.insert(tk.END, pdf.name)

        total = len(self.pdf_files)
        self.label_count.config(text=f"{total} arquivo(s) encontrados")
        state = "normal" if total > 0 else "disabled"
        self.btn_delete.configure(state=state)
        self.btn_generate.configure(state=state)

    def delete_selected(self):
        for idx in sorted(self.listbox.curselection(), reverse=True):
            self.listbox.delete(idx)
            del self.pdf_files[idx]

        total = len(self.pdf_files)
        self.label_count.config(text=f"{total} arquivo(s) encontrados")
        if total == 0:
            self.btn_delete.configure(state="disabled")
            self.btn_generate.configure(state="disabled")

    def generate_pdf(self):
        if not self.pdf_files:
            return

        title = self.title_var.get().strip()
        subtitle = self.subtitle_var.get().strip()

        if not title:
            messagebox.showwarning("Campo obrigatório", "O título da capa é obrigatório.")
            return

        filename = title.lower().replace(" ", "_").replace("-", "_") + ".pdf"
        output_path = self.folder / filename

        try:
            merge_pdfs_with_summary_and_cover(self.pdf_files, output_path, title, subtitle)
            messagebox.showinfo("Sucesso", f"PDF gerado com sucesso como:\n\n{output_path}")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao gerar o PDF:\n{str(e)}")


def main():
    root = tk.Tk()
    PdfMergerGUI(master=root)
    root.mainloop()


if __name__ == "__main__":
    main()