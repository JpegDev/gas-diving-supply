# main.py
import customtkinter as ctk
import sqlite3
from datetime import datetime
from calcul_gaz import CalculateurMelange
import tkinter.messagebox as mb
from tkinter import ttk

DB_PATH = "club_plongee.db"

# ─────────────────────────────────────────────
# BASE DE DONNÉES
# ─────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS stock_gaz (
            id INTEGER PRIMARY KEY,
            nom TEXT NOT NULL,
            type_gaz TEXT NOT NULL,
            pression_bar REAL DEFAULT 0,
            capacite_litres REAL DEFAULT 0,
            date_maj TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS bouteilles (
            id INTEGER PRIMARY KEY,
            numero_serie TEXT UNIQUE NOT NULL,
            proprietaire TEXT,
            capacite_litres REAL NOT NULL,
            pression_max_bar INTEGER DEFAULT 232,
            actif BOOLEAN DEFAULT 1
        );
        
        CREATE TABLE IF NOT EXISTS releves (
            id INTEGER PRIMARY KEY,
            bouteille_id INTEGER,
            date_releve TIMESTAMP,
            pression_actuelle_bar REAL,
            o2_pourcent REAL DEFAULT 21.0,
            he_pourcent REAL DEFAULT 0.0,
            pression_cible_bar REAL,
            o2_cible_pourcent REAL DEFAULT 21.0,
            he_cible_pourcent REAL DEFAULT 0.0,
            o2_pur_bl REAL DEFAULT 0,
            he_pur_bl REAL DEFAULT 0,
            air_bl REAL DEFAULT 0,
            statut TEXT DEFAULT 'EN_ATTENTE',
            FOREIGN KEY (bouteille_id) REFERENCES bouteilles(id)
        );
        
        -- Données de démo
        INSERT OR IGNORE INTO stock_gaz (nom, type_gaz, pression_bar, capacite_litres, date_maj)
        VALUES 
            ('Bouteille O2 50L', 'O2', 180, 50, datetime('now')),
            ('Bloc Hélium 50L',  'HE', 150, 50, datetime('now')),
            ('Compresseur Air',  'AIR', 300, 200, datetime('now'));
    """)
    conn.commit()
    conn.close()


def get_conn():
    return sqlite3.connect(DB_PATH)


# ─────────────────────────────────────────────
# FENÊTRE PRINCIPALE
# ─────────────────────────────────────────────
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.title("🤿 GazDive - Gestion des gaz club")
        self.geometry("1100x700")
        self.resizable(True, True)
        
        self._build_ui()
    
    def _build_ui(self):
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.pack(side="left", fill="y", padx=0, pady=0)
        self.sidebar.pack_propagate(False)
        
        ctk.CTkLabel(
            self.sidebar, text="🤿 GazDive",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=20)
        
        buttons = [
            ("📦 Stock",        self.show_stock),
            ("🧪 Bouteilles",   self.show_bouteilles),
            ("📋 Relevés",      self.show_releves),
            ("⚗️  Remplissage",  self.show_remplissage),
        ]
        for label, cmd in buttons:
            ctk.CTkButton(
                self.sidebar, text=label, command=cmd,
                anchor="w", height=45,
                font=ctk.CTkFont(size=14)
            ).pack(fill="x", padx=10, pady=5)
        
        # Zone principale
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        self.show_stock()
    
    def _clear_main(self):
        for w in self.main_frame.winfo_children():
            w.destroy()
    
    # ── STOCK ──────────────────────────────────
    def show_stock(self):
        self._clear_main()
        frame = self.main_frame
        
        ctk.CTkLabel(frame, text="📦 Stock de gaz",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        
        # Tableau
        cols = ("ID", "Nom", "Type", "Pression (bar)", "Capacité (L)", "Stock (bar·L)", "MAJ")
        tree = self._make_tree(frame, cols)
        
        conn = get_conn()
        rows = conn.execute(
            "SELECT id, nom, type_gaz, pression_bar, capacite_litres, "
            "ROUND(pression_bar * capacite_litres,0), date_maj FROM stock_gaz"
        ).fetchall()
        conn.close()
        
        for r in rows:
            tree.insert("", "end", values=r)
        
        # Boutons
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(btn_frame, text="➕ Ajouter source",
                      command=self.dialog_add_stock).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="✏️ Modifier pression",
                      command=lambda: self.dialog_edit_stock(tree)).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="🔄 Rafraîchir",
                      command=self.show_stock).pack(side="left", padx=5)
    
    def dialog_add_stock(self):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Ajouter source de gaz")
        dlg.geometry("400x350")
        dlg.grab_set()
        
        fields = {}
        for label, default in [
            ("Nom",             "O2 50L"),
            ("Type (O2/HE/AIR)","O2"),
            ("Pression (bar)",  "200"),
            ("Capacité (L)",    "50"),
        ]:
            ctk.CTkLabel(dlg, text=label).pack(pady=(10,0))
            e = ctk.CTkEntry(dlg, width=250)
            e.insert(0, default)
            e.pack()
            fields[label] = e
        
        def save():
            conn = get_conn()
            conn.execute(
                "INSERT INTO stock_gaz (nom, type_gaz, pression_bar, capacite_litres, date_maj)"
                " VALUES (?,?,?,?,?)",
                (fields["Nom"].get(),
                 fields["Type (O2/HE/AIR)"].get().upper(),
                 float(fields["Pression (bar)"].get()),
                 float(fields["Capacité (L)"].get()),
                 datetime.now())
            )
            conn.commit(); conn.close()
            dlg.destroy(); self.show_stock()
        
        ctk.CTkButton(dlg, text="💾 Enregistrer", command=save).pack(pady=20)
    
    def dialog_edit_stock(self, tree):
        sel = tree.selection()
        if not sel:
            mb.showwarning("Sélection", "Sélectionnez une ligne")
            return
        item = tree.item(sel[0])["values"]
        stock_id = item[0]
        
        dlg = ctk.CTkToplevel(self)
        dlg.title("Modifier pression")
        dlg.geometry("300x200")
        dlg.grab_set()
        
        ctk.CTkLabel(dlg, text=f"Source : {item[1]}").pack(pady=10)
        ctk.CTkLabel(dlg, text="Nouvelle pression (bar)").pack()
        e = ctk.CTkEntry(dlg, width=200)
        e.insert(0, str(item[3]))
        e.pack(pady=5)
        
        def save():
            conn = get_conn()
            conn.execute(
                "UPDATE stock_gaz SET pression_bar=?, date_maj=? WHERE id=?",
                (float(e.get()), datetime.now(), stock_id)
            )
            conn.commit(); conn.close()
            dlg.destroy(); self.show_stock()
        
        ctk.CTkButton(dlg, text="💾 Enregistrer", command=save).pack(pady=15)
    
    # ── BOUTEILLES ─────────────────────────────
    def show_bouteilles(self):
        self._clear_main()
        frame = self.main_frame
        
        ctk.CTkLabel(frame, text="🧪 Bouteilles",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        
        cols = ("ID", "N° Série", "Propriétaire", "Capacité (L)", "Pmax (bar)")
        tree = self._make_tree(frame, cols)
        
        conn = get_conn()
        rows = conn.execute(
            "SELECT id, numero_serie, proprietaire, capacite_litres, pression_max_bar"
            " FROM bouteilles WHERE actif=1"
        ).fetchall()
        conn.close()
        
        for r in rows:
            tree.insert("", "end", values=r)
        
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(btn_frame, text="➕ Ajouter",
                      command=lambda: self.dialog_add_bouteille()).pack(side="left", padx=5)
    
    def dialog_add_bouteille(self):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Ajouter bouteille")
        dlg.geometry("400x400")
        dlg.grab_set()
        
        fields = {}
        for label, default in [
            ("N° Série",         "BTL-001"),
            ("Propriétaire",     "Jean Dupont"),
            ("Capacité (L)",     "12"),
            ("Pression max (bar)","232"),
        ]:
            ctk.CTkLabel(dlg, text=label).pack(pady=(10,0))
            e = ctk.CTkEntry(dlg, width=250)
            e.insert(0, default)
            e.pack()
            fields[label] = e
        
        def save():
            conn = get_conn()
            conn.execute(
                "INSERT INTO bouteilles (numero_serie, proprietaire, capacite_litres, pression_max_bar)"
                " VALUES (?,?,?,?)",
                (fields["N° Série"].get(), fields["Propriétaire"].get(),
                 float(fields["Capacité (L)"].get()),
                 int(fields["Pression max (bar)"].get()))
            )
            conn.commit(); conn.close()
            dlg.destroy(); self.show_bouteilles()
        
        ctk.CTkButton(dlg, text="💾 Enregistrer", command=save).pack(pady=20)
    
    # ── RELEVÉS ────────────────────────────────
    def show_releves(self):
        self._clear_main()
        frame = self.main_frame
        
        ctk.CTkLabel(frame, text="📋 Relevés de bouteilles",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        
        cols = ("ID", "Bouteille", "Propriétaire", "Date", 
                "P.actu (bar)", "O2% actu", "He% actu",
                "P.cible (bar)", "O2% cible", "He% cible", "Statut")
        tree = self._make_tree(frame, cols, height=12)
        self._load_releves(tree)
        
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(btn_frame, text="➕ Nouveau relevé",
                      command=lambda: self.dialog_add_releve(tree)).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="🗑️ Supprimer",
                      command=lambda: self.delete_releve(tree)).pack(side="left", padx=5)
    
    def _load_releves(self, tree):
        for i in tree.get_children():
            tree.delete(i)
        conn = get_conn()
        rows = conn.execute("""
            SELECT r.id, b.numero_serie, b.proprietaire,
                   strftime('%d/%m/%Y %H:%M', r.date_releve),
                   r.pression_actuelle_bar, r.o2_pourcent, r.he_pourcent,
                   r.pression_cible_bar, r.o2_cible_pourcent, r.he_cible_pourcent,
                   r.statut
            FROM releves r
            JOIN bouteilles b ON b.id = r.bouteille_id
            ORDER BY r.date_releve DESC
        """).fetchall()
        conn.close()
        for r in rows:
            tag = "rempli" if r[-1] == "REMPLI" else ""
            tree.insert("", "end", values=r, tags=(tag,))
        tree.tag_configure("rempli", foreground="#4CAF50")
    
    def dialog_add_releve(self, tree):
        # Récupérer les bouteilles
        conn = get_conn()
        bouteilles = conn.execute(
            "SELECT id, numero_serie, proprietaire FROM bouteilles WHERE actif=1"
        ).fetchall()
        conn.close()
        
        if not bouteilles:
            mb.showwarning("Aucune bouteille", "Ajoutez d'abord des bouteilles")
            return
        
        dlg = ctk.CTkToplevel(self)
        dlg.title("Nouveau relevé")
        dlg.geometry("450x550")
        dlg.grab_set()
        
        ctk.CTkLabel(dlg, text="Bouteille").pack(pady=(10,0))
        btl_var = ctk.StringVar()
        btl_map = {f"{b[1]} - {b[2]}": b[0] for b in bouteilles}
        combo = ctk.CTkComboBox(dlg, values=list(btl_map.keys()), 
                                 variable=btl_var, width=300)
        combo.set(list(btl_map.keys())[0])
        combo.pack()
        
        fields = {}
        specs = [
            ("Pression actuelle (bar)", "50"),
            ("O2% actuel",             "21.0"),
            ("He% actuel",             "0.0"),
            ("Pression cible (bar)",   "200"),
            ("O2% cible",              "32.0"),
            ("He% cible",              "0.0"),
        ]
        for label, default in specs:
            ctk.CTkLabel(dlg, text=label).pack(pady=(8,0))
            e = ctk.CTkEntry(dlg, width=250)
            e.insert(0, default)
            e.pack()
            fields[label] = e
        
        def save():
            btl_id = btl_map[btl_var.get()]
            conn = get_conn()
            conn.execute("""
                INSERT INTO releves 
                (bouteille_id, date_releve, pression_actuelle_bar,
                 o2_pourcent, he_pourcent, pression_cible_bar,
                 o2_cible_pourcent, he_cible_pourcent, statut)
                VALUES (?,?,?,?,?,?,?,?,'EN_ATTENTE')
            """, (
                btl_id, datetime.now(),
                float(fields["Pression actuelle (bar)"].get()),
                float(fields["O2% actuel"].get()),
                float(fields["He% actuel"].get()),
                float(fields["Pression cible (bar)"].get()),
                float(fields["O2% cible"].get()),
                float(fields["He% cible"].get()),
            ))
            conn.commit(); conn.close()
            dlg.destroy()
            self._load_releves(tree)
        
        ctk.CTkButton(dlg, text="💾 Enregistrer", command=save).pack(pady=20)
    
    def delete_releve(self, tree):
        sel = tree.selection()
        if not sel: return
        rid = tree.item(sel[0])["values"][0]
        if mb.askyesno("Supprimer", "Supprimer ce relevé ?"):
            conn = get_conn()
            conn.execute("DELETE FROM releves WHERE id=?", (rid,))
            conn.commit(); conn.close()
            self._load_releves(tree)
    
    # ── REMPLISSAGE ────────────────────────────
    def show_remplissage(self):
        self._clear_main()
        frame = self.main_frame
        
        ctk.CTkLabel(frame, text="⚗️ Session de remplissage",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        
        # Récupérer les relevés EN_ATTENTE
        conn = get_conn()
        releves = conn.execute("""
            SELECT r.id, b.numero_serie, b.proprietaire, b.capacite_litres,
                   r.pression_actuelle_bar, r.o2_pourcent, r.he_pourcent,
                   r.pression_cible_bar, r.o2_cible_pourcent, r.he_cible_pourcent
            FROM releves r
            JOIN bouteilles b ON b.id = r.bouteille_id
            WHERE r.statut = 'EN_ATTENTE'
        """).fetchall()
        
        stock = conn.execute(
            "SELECT type_gaz, SUM(pression_bar * capacite_litres) "
            "FROM stock_gaz GROUP BY type_gaz"
        ).fetchall()
        conn.close()
        
        stock_dict = {row[0]: row[1] for row in stock}
        
        if not releves:
            ctk.CTkLabel(frame, text="✅ Aucun relevé en attente",
                         font=ctk.CTkFont(size=14)).pack(pady=50)
            return
        
        # Calculs
        calc = CalculateurMelange()
        resultats = []
        total_o2 = total_he = total_air = 0.0
        
        for r in releves:
            (rid, serie, proprio, capa,
             p_act, o2_act, he_act,
             p_cib, o2_cib, he_cib) = r
            
            res = calc.calculer_remplissage(
                p_act, o2_act, he_act, capa,
                p_cib, o2_cib, he_cib
            )
            res["releve_id"] = rid
            res["serie"]     = serie
            res["proprio"]   = proprio
            resultats.append(res)
            total_o2  += res["o2_pur_bl"]
            total_he  += res["he_pur_bl"]
            total_air += res["air_bl"]
        
        # Tableau des besoins
        cols = ("Bouteille", "Proprio", "O2 pur (b·L)", "He pur (b·L)", "Air (b·L)", "O2% final", "Alertes")
        tree = self._make_tree(frame, cols, height=8)
        
        for res in resultats:
            warn = " | ".join(res["warnings"]) if res["warnings"] else "✅ OK"
            tree.insert("", "end", values=(
                res["serie"], res["proprio"],
                res["o2_pur_bl"], res["he_pur_bl"], res["air_bl"],
                res["o2_final_theorique"],
                warn
            ))
        
        # Résumé stock
        sum_frame = ctk.CTkFrame(frame)
        sum_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(sum_frame, text="📊 Bilan stock",
                     font=ctk.CTkFont(size=14, weight="bold")).grid(
                         row=0, column=0, columnspan=4, pady=5)
        
        for col, (label, besoin, type_gaz) in enumerate([
            ("O2 pur",  total_o2,  "O2"),
            ("Hélium",  total_he,  "HE"),
            ("Air",     total_air, "AIR"),
        ]):
            dispo = stock_dict.get(type_gaz, 0)
            ok    = dispo >= besoin
            color = "#4CAF50" if ok else "#f44336"
            
            ctk.CTkLabel(sum_frame, text=label,
                         font=ctk.CTkFont(weight="bold")).grid(
                             row=1, column=col, padx=20)
            ctk.CTkLabel(sum_frame,
                         text=f"Besoin: {besoin:.0f} b·L\nDispo: {dispo:.0f} b·L",
                         text_color=color).grid(row=2, column=col, padx=20)
        
        # Bouton valider
        def valider_remplissage():
            # Vérif stock
            verification = calc.verifier_stock_suffisant(resultats, {
                "o2_bl":  stock_dict.get("O2",  0),
                "he_bl":  stock_dict.get("HE",  0),
                "air_bl": stock_dict.get("AIR", 0),
            })
            
            manques = [k for k, v in verification.items() if not v["ok"]]
            if manques and not mb.askyesno(
                "Stock insuffisant",
                f"Stock insuffisant pour : {', '.join(manques)}\nContinuer quand même ?"
            ):
                return
            
            conn = get_conn()
            # Déduire du stock
            conn.execute("""
                UPDATE stock_gaz SET 
                    pression_bar = pression_bar - (? / capacite_litres),
                    date_maj = ?
                WHERE type_gaz = 'O2'
                AND id = (SELECT id FROM stock_gaz WHERE type_gaz='O2' 
                          ORDER BY pression_bar DESC LIMIT 1)
            """, (total_o2, datetime.now()))
            
            conn.execute("""
                UPDATE stock_gaz SET 
                    pression_bar = pression_bar - (? / capacite_litres),
                    date_maj = ?
                WHERE type_gaz = 'HE'
                AND id = (SELECT id FROM stock_gaz WHERE type_gaz='HE' 
                          ORDER BY pression_bar DESC LIMIT 1)
            """, (total_he, datetime.now()))
            
            conn.execute("""
                UPDATE stock_gaz SET 
                    pression_bar = pression_bar - (? / capacite_litres),
                    date_maj = ?
                WHERE type_gaz = 'AIR'
                AND id = (SELECT id FROM stock_gaz WHERE type_gaz='AIR' 
                          ORDER BY pression_bar DESC LIMIT 1)
            """, (total_air, datetime.now()))
            
            # Marquer les relevés comme REMPLI
            for res in resultats:
                conn.execute(
                    "UPDATE releves SET statut='REMPLI', "
                    "o2_pur_bl=?, he_pur_bl=?, air_bl=? WHERE id=?",
                    (res["o2_pur_bl"], res["he_pur_bl"], 
                     res["air_bl"], res["releve_id"])
                )
            
            conn.commit(); conn.close()
            mb.showinfo("✅ Succès", 
                        f"Remplissage validé !\n"
                        f"O2 consommé  : {total_o2:.0f} bar·L\n"
                        f"He consommé  : {total_he:.0f} bar·L\n"
                        f"Air consommé : {total_air:.0f} bar·L")
            self.show_remplissage()
        
        ctk.CTkButton(
            frame,
            text="✅ VALIDER LE REMPLISSAGE & DÉDUIRE DU STOCK",
            command=valider_remplissage,
            height=50,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#2e7d32",
            hover_color="#1b5e20"
        ).pack(pady=15, padx=20, fill="x")
    
    # ── UTILS ──────────────────────────────────
    def _make_tree(self, parent, cols, height=10):
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                         background="#2b2b2b", foreground="white",
                         fieldbackground="#2b2b2b", rowheight=28)
        style.configure("Treeview.Heading",
                         background="#1f538d", foreground="white",
                         font=("Arial", 10, "bold"))
        
        sb = ttk.Scrollbar(frame, orient="vertical")
        sb.pack(side="right", fill="y")
        
        tree = ttk.Treeview(frame, columns=cols, show="headings",
                             height=height, yscrollcommand=sb.set)
        sb.config(command=tree.yview)
        
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=max(80, len(col) * 9), anchor="center")
        
        tree.pack(fill="both", expand=True)
        return tree


# ─────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    app = App()
    app.mainloop()
