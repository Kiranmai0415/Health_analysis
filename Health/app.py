from flask import Flask, render_template, jsonify, request, send_file, redirect, url_for, session
import sqlite3, os
from config import DB_PATH, EXCEL_PATH

app = Flask(__name__)
app.secret_key = "hospital_secret_2024"

# ── Users & Roles ─────────────────────────────────────
# Roles: admin | doctor | nurse | receptionist
# Each role controls what they can see in the dashboard
USERS = {
    "admin":        {"password": "admin123",       "role": "admin",        "name": "Admin User",      "avatar": "AD"},
    "dr_ramesh":    {"password": "doctor123",       "role": "doctor",       "name": "Dr. Ramesh",      "avatar": "DR"},
    "dr_preethi":   {"password": "doctor456",       "role": "doctor",       "name": "Dr. Preethi",     "avatar": "DP"},
    "nurse_kavya":  {"password": "nurse123",        "role": "nurse",        "name": "Nurse Kavya",     "avatar": "NK"},
    "nurse_sneha":  {"password": "nurse456",        "role": "nurse",        "name": "Nurse Sneha",     "avatar": "NS"},
    "reception":    {"password": "reception123",    "role": "receptionist", "name": "Receptionist",    "avatar": "RC"},
}

# What each role can access
ROLE_PERMISSIONS = {
    "admin":        {"stats": True,  "billing": True,  "charts": True,  "export": True,  "all_patients": True},
    "doctor":       {"stats": True,  "billing": False, "charts": True,  "export": False, "all_patients": True},
    "nurse":        {"stats": True,  "billing": False, "charts": False, "export": False, "all_patients": True},
    "receptionist": {"stats": False, "billing": True,  "charts": False, "export": True,  "all_patients": True},
}

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def current_user():
    u = session.get("user")
    if u and u in USERS:
        return {"username": u, **USERS[u]}
    return None

def require_login():
    if not current_user():
        return redirect(url_for("login"))
    return None

# ── Auth ──────────────────────────────────────────────
@app.route("/", methods=["GET","POST"])
def login():
    error = None
    if request.method == "POST":
        u = request.form.get("username","").strip()
        p = request.form.get("password","")
        if u in USERS and USERS[u]["password"] == p:
            session["user"] = u
            return redirect(url_for("dashboard"))
        error = "Invalid username or password."
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ── Dashboard ─────────────────────────────────────────
@app.route("/dashboard")
def dashboard():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    perms = ROLE_PERMISSIONS[user["role"]]
    return render_template("dashboard.html", user=user, perms=perms)

# ── API: current user info ─────────────────────────────
@app.route("/api/me")
def api_me():
    user = current_user()
    if not user:
        return jsonify({"error": "not logged in"}), 401
    return jsonify({"name": user["name"], "role": user["role"], "avatar": user["avatar"],
                    "permissions": ROLE_PERMISSIONS[user["role"]]})

# ── API: stats cards ──────────────────────────────────
@app.route("/api/stats")
def api_stats():
    if not current_user(): return jsonify({}), 401
    conn = get_db(); cur = conn.cursor()
    total      = cur.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
    admitted   = cur.execute("SELECT COUNT(*) FROM patients WHERE status='Admitted'").fetchone()[0]
    critical   = cur.execute("SELECT COUNT(*) FROM patients WHERE status='Critical'").fetchone()[0]
    discharged = cur.execute("SELECT COUNT(*) FROM patients WHERE status='Discharged'").fetchone()[0]
    observation= cur.execute("SELECT COUNT(*) FROM patients WHERE status='Under Observation'").fetchone()[0]
    total_bill = cur.execute("SELECT SUM(bill_amount) FROM patients").fetchone()[0] or 0
    paid_amt   = cur.execute("SELECT SUM(bill_amount) FROM patients WHERE paid=1").fetchone()[0] or 0
    conn.close()
    return jsonify({"total": total, "admitted": admitted, "critical": critical,
                    "discharged": discharged, "observation": observation,
                    "total_bill": round(total_bill,2), "paid": round(paid_amt,2),
                    "pending": round(total_bill-paid_amt,2)})

@app.route("/api/conditions")
def api_conditions():
    if not current_user(): return jsonify([]), 401
    conn = get_db()
    rows = conn.execute("SELECT condition, COUNT(*) as cnt FROM patients GROUP BY condition ORDER BY cnt DESC").fetchall()
    conn.close()
    return jsonify([{"condition": r["condition"], "count": r["cnt"]} for r in rows])

@app.route("/api/wards")
def api_wards():
    if not current_user(): return jsonify([]), 401
    conn = get_db()
    rows = conn.execute("SELECT ward, COUNT(*) as cnt FROM patients GROUP BY ward").fetchall()
    conn.close()
    return jsonify([{"ward": r["ward"], "count": r["cnt"]} for r in rows])

@app.route("/api/statuses")
def api_statuses():
    if not current_user(): return jsonify([]), 401
    conn = get_db()
    rows = conn.execute("SELECT status, COUNT(*) as cnt FROM patients GROUP BY status").fetchall()
    conn.close()
    return jsonify([{"status": r["status"], "count": r["cnt"]} for r in rows])

@app.route("/api/patients")
def api_patients():
    if not current_user(): return jsonify({}), 401
    search = request.args.get("search","").strip()
    status = request.args.get("status","")
    ward   = request.args.get("ward","")
    page   = int(request.args.get("page",1))
    per    = int(request.args.get("per_page",10))

    query  = "SELECT * FROM patients WHERE 1=1"
    params = []
    if search:
        query += " AND (name LIKE ? OR condition LIKE ? OR doctor LIKE ?)"
        s = f"%{search}%"; params += [s,s,s]
    if status:
        query += " AND status=?"; params.append(status)
    if ward:
        query += " AND ward=?"; params.append(ward)

    conn  = get_db()
    total = conn.execute(f"SELECT COUNT(*) FROM ({query})", params).fetchone()[0]
    rows  = conn.execute(query + f" ORDER BY id LIMIT {per} OFFSET {(page-1)*per}", params).fetchall()
    conn.close()
    return jsonify({"total": total, "page": page, "per_page": per,
                    "patients": [dict(r) for r in rows]})

@app.route("/export")
def export():
    user = current_user()
    if not user: return redirect(url_for("login"))
    if ROLE_PERMISSIONS[user["role"]]["export"]:
        if os.path.exists(EXCEL_PATH):
            return send_file(os.path.abspath(EXCEL_PATH), as_attachment=True, download_name="hospital_report.xlsx")
        return "Excel file not found. Run main.py first.", 404
    return "Access denied: your role cannot export reports.", 403

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print("hospital.db not found! Please run main.py first.")
    else:
        print("\n🏥 Hospital Dashboard starting at http://127.0.0.1:5000")
        print("\n── Login Credentials ──────────────────────")
        print("  admin        / admin123       (Admin)")
        print("  dr_ramesh    / doctor123      (Doctor)")
        print("  dr_preethi   / doctor456      (Doctor)")
        print("  nurse_kavya  / nurse123       (Nurse)")
        print("  nurse_sneha  / nurse456       (Nurse)")
        print("  reception    / reception123   (Receptionist)")
        print("───────────────────────────────────────────\n")
        app.run(debug=True)