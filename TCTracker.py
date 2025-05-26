# trench_campaign_tracker.py

import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import json
import os
import webbrowser
from collections import defaultdict

DATA_FILE = "campaign_data.json"

class CampaignTracker:
    def __init__(self):
        self.data = {"warbands": {}, "rounds": defaultdict(list)}
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                self.data = json.load(f)

    def save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump(self.data, f, indent=2)

    def add_warband(self, name):
        if name in self.data["warbands"]:
            return False
        self.data["warbands"][name] = {
            "wins": 0,
            "losses": 0,
            "glory": 0,
            "casualties": 0,
            "victory_points": 0,
            "matches": []
        }
        return True

    def remove_warband(self, name):
        if name not in self.data["warbands"]:
            return False
        del self.data["warbands"][name]
        return True

    def add_match(self, round_num, w1, w2, winner, vp1, vp2, g1, g2, c1, c2):
        # track match with victory_points, glory, casualties
        match = {
            "round": round_num,
            "warband1": w1,
            "warband2": w2,
            "winner": winner,
            "victory_points1": vp1,
            "victory_points2": vp2,
            "glory1": g1,
            "glory2": g2,
            "casualties1": c1,
            "casualties2": c2
        }
        key = str(round_num)
        self.data["rounds"].setdefault(key, []).append(match)
        # update warband totals
        for wb, vp, glory, casualties, result in [
            (w1, vp1, g1, c1, w1 == winner),
            (w2, vp2, g2, c2, w2 == winner)
        ]:
            if wb not in self.data["warbands"]:
                continue
            stats = self.data["warbands"][wb]
            stats["victory_points"] += vp
            stats["glory"] += glory
            stats["casualties"] += casualties
            stats["wins"] += int(result)
            stats["losses"] += int(not result)
            stats["matches"].append(match)

    def get_warbands(self):
        return list(self.data["warbands"].keys())

class TrackerUI:
    def __init__(self, root):
        self.tracker = CampaignTracker()
        self.root = root
        root.title("Trench Crusade Campaign Tracker")

        # Warband entry
        self.warband_entry = tk.Entry(root)
        self.warband_entry.grid(row=0, column=0)
        tk.Button(root, text="Add Warband", command=self.add_warband).grid(row=0, column=1)

        # Warband list with context menu
        self.warband_list = tk.Listbox(root)
        self.warband_list.grid(row=1, column=0, columnspan=2)
        self.warband_list.bind("<Button-3>", self.show_context_menu)
        self.context_menu = tk.Menu(root, tearoff=0)
        self.context_menu.add_command(label="Edit Stats", command=self.open_stat_editor)
        self.context_menu.add_command(label="Delete Warband", command=self.delete_selected_warband)

        # Match entry fields
        tk.Label(root, text="Round").grid(row=2, column=0)
        self.round_entry = tk.Entry(root)
        self.round_entry.grid(row=2, column=1)

        tk.Label(root, text="Warband 1").grid(row=3, column=0)
        self.w1_combo = ttk.Combobox(root)
        self.w1_combo.grid(row=3, column=1)

        tk.Label(root, text="Warband 2").grid(row=4, column=0)
        self.w2_combo = ttk.Combobox(root)
        self.w2_combo.grid(row=4, column=1)

        tk.Label(root, text="Winner").grid(row=5, column=0)
        self.winner_combo = ttk.Combobox(root)
        self.winner_combo.grid(row=5, column=1)

        tk.Label(root, text="Victory Points W1 / W2").grid(row=6, column=0)
        self.vp1_entry = tk.Entry(root, width=5)
        self.vp2_entry = tk.Entry(root, width=5)
        self.vp1_entry.grid(row=6, column=1, sticky="w")
        self.vp2_entry.grid(row=6, column=1, sticky="e")

        tk.Label(root, text="Glory Points W1 / W2").grid(row=7, column=0)
        self.glory1_entry = tk.Entry(root, width=5)
        self.glory2_entry = tk.Entry(root, width=5)
        self.glory1_entry.grid(row=7, column=1, sticky="w")
        self.glory2_entry.grid(row=7, column=1, sticky="e")

        tk.Label(root, text="Casualties W1 / W2").grid(row=8, column=0)
        self.cas1_entry = tk.Entry(root, width=5)
        self.cas2_entry = tk.Entry(root, width=5)
        self.cas1_entry.grid(row=8, column=1, sticky="w")
        self.cas2_entry.grid(row=8, column=1, sticky="e")

        tk.Button(root, text="Add Match", command=self.add_match).grid(row=9, column=0, columnspan=2)
        tk.Button(root, text="Save & Exit", command=self.on_exit).grid(row=10, column=0, columnspan=2)
        tk.Button(root, text="Export to HTML", command=self.export_to_html).grid(row=11, column=0, columnspan=2, pady=(10,0))

        # populate combos
        self.refresh_warband_list()

    def add_warband(self):
        name = self.warband_entry.get().strip()
        if name and self.tracker.add_warband(name):
            self.refresh_warband_list()
        else:
            messagebox.showerror("Error", "Warband exists or invalid.")

    def add_match(self):
        try:
            r = int(self.round_entry.get())
            w1 = self.w1_combo.get(); w2 = self.w2_combo.get(); win = self.winner_combo.get()
            vp1 = int(self.vp1_entry.get()); vp2 = int(self.vp2_entry.get())
            g1 = int(self.glory1_entry.get()); g2 = int(self.glory2_entry.get())
            c1 = int(self.cas1_entry.get()); c2 = int(self.cas2_entry.get())
            if not all([w1, w2, win]) or w1==w2 or win not in [w1,w2]:
                raise ValueError("Invalid match setup.")
            self.tracker.add_match(r, w1, w2, win, vp1, vp2, g1, g2, c1, c2)
            messagebox.showinfo("Success", "Match added.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def show_context_menu(self, event):
        idx = self.warband_list.nearest(event.y)
        if idx>=0:
            self.warband_list.selection_clear(0, tk.END)
            self.warband_list.selection_set(idx)
            self.context_menu.tk_popup(event.x_root, event.y_root)

    def get_selected_warband(self):
        sel = self.warband_list.curselection()
        return self.warband_list.get(sel[0]) if sel else None

    def delete_selected_warband(self):
        name = self.get_selected_warband()
        if name and messagebox.askyesno("Confirm", f"Delete '{name}'?" ):
            self.tracker.remove_warband(name)
            self.refresh_warband_list()

    def open_stat_editor(self):
        name = self.get_selected_warband()
        if not name: return
        stat_win = tk.Toplevel(self.root); stat_win.title(f"Edit Stats - {name}")
        # VP
        tk.Label(stat_win, text="Victory Points").grid(row=0,column=0)
        vp_entry = tk.Entry(stat_win); vp_entry.grid(row=0,column=1)
        tk.Label(stat_win, text="Glory").grid(row=1,column=0)
        gl_entry = tk.Entry(stat_win); gl_entry.grid(row=1,column=1)
        tk.Label(stat_win, text="Casualties").grid(row=2,column=0)
        ca_entry = tk.Entry(stat_win); ca_entry.grid(row=2,column=1)
        cur = self.tracker.data["warbands"][name]
        vp_entry.insert(0, str(cur.get("victory_points",0)))
        gl_entry.insert(0, str(cur["glory"]))
        ca_entry.insert(0, str(cur["casualties"]))
        def apply():
            try:
                cur["victory_points"] = int(vp_entry.get())
                cur["glory"] = int(gl_entry.get())
                cur["casualties"] = int(ca_entry.get())
                messagebox.showinfo("Updated", f"Stats for {name} saved.")
                stat_win.destroy()
            except:
                messagebox.showerror("Error","Invalid input.")
        tk.Button(stat_win, text="Apply", command=apply).grid(row=3,column=0,columnspan=2)

    def export_to_html(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".html",
            filetypes=[("HTML files","*.html")])
        if not filepath: return
        html=["<!DOCTYPE html>","<html>","<head>","<meta charset='UTF-8'>",
            "<title>Trench Crusade Campaign</title>","<style>",
            "body{background:#111;color:#ddd;font-family:'Georgia',serif;padding:2em}",
            "h1,h2{color:#b53}table{width:100%;border-collapse:collapse;margin:1em 0}",
            "th,td{border:1px solid #555;padding:0.5em;text-align:left}",
            "th{background:#333}tr:nth-child(even){background:#222}","</style>","</head><body>",
            "<h1>Trench Crusade Campaign Report</h1>"]
        for name,st in self.tracker.data["warbands"].items():
            html += [f"<h2>{name}</h2>","<ul>",
                f"<li><strong>Wins:</strong> {st['wins']}</li>",
                f"<li><strong>Losses:</strong> {st['losses']}</li>",
                f"<li><strong>Victory Points:</strong> {st['victory_points']}</li>",
                f"<li><strong>Glory:</strong> {st['glory']}</li>",
                f"<li><strong>Casualties:</strong> {st['casualties']}</li>","</ul>","<table>",
                "<tr><th>Round</th><th>Opponent</th><th>Result</th>",
                "<th>VP</th><th>Glory</th><th>Casualties</th></tr>"]
            for m in st["matches"]:
                opp = m["warband2"] if m["warband1"]==name else m["warband1"]
                vp = m["victory_points1"] if m["warband1"]==name else m["victory_points2"]
                gl = m["glory1"] if m["warband1"]==name else m["glory2"]
                ca = m["casualties1"] if m["warband1"]==name else m["casualties2"]
                res = "Win" if m["winner"]==name else "Loss"
                html.append(f"<tr><td>{m['round']}</td><td>{opp}</td><td>{res}</td>"
                            +f"<td>{vp}</td><td>{gl}</td><td>{ca}</td></tr>")
            html.append("</table>")
        html.append("</body></html>")
        with open(filepath, "w", encoding="utf-8") as f: f.write("\n".join(html))
        webbrowser.open(filepath)

    def refresh_warband_list(self):
        self.warband_list.delete(0, tk.END)
        names = self.tracker.get_warbands()
        for n in names: self.warband_list.insert(tk.END,n)
        self.w1_combo['values'] = names
        self.w2_combo['values'] = names
        self.winner_combo['values'] = names

    def on_exit(self):
        self.tracker.save_data()
        self.root.quit()

if __name__=='__main__':
    root = tk.Tk()
    app = TrackerUI(root)
    root.mainloop()
