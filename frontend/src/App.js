import { useState, useEffect, useCallback } from "react";

function useIsMobile() {
  const [isMobile, setIsMobile] = useState(() => window.innerWidth < 768);
  useEffect(() => {
    const handler = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', handler);
    return () => window.removeEventListener('resize', handler);
  }, []);
  return isMobile;
}

const STATUS = {
  unassigned:   { label: "Unassigned",   color: "#c53030", border: "#fc8181", light: "#fed7d7" },
  message_sent: { label: "Message Sent", color: "#b7791f", border: "#ecc94b", light: "#fefcbf" },
  confirmed:    { label: "Confirmed",    color: "#276749", border: "#48bb78", light: "#c6f6d5" },
  past_event:   { label: "Past Event",   color: "#2d3748", border: "#718096", light: "#e2e8f0" },
};

function parseWallClock(dtStr) {
  return new Date(dtStr.replace(/([+-]\d{2}:\d{2}|Z)$/, ""));
}

function formatTime(dtStr) {
  const d = parseWallClock(dtStr);
  const h = d.getHours(), m = d.getMinutes();
  return `${h % 12 || 12}:${String(m).padStart(2, "0")} ${h >= 12 ? "PM" : "AM"}`;
}

function toDateKey(dtStr) {
  const d = parseWallClock(dtStr);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function toMondayKey(dateKey) {
  const [y, m, d] = dateKey.split("-").map(Number);
  const dt = new Date(y, m - 1, d, 12);
  const dow = dt.getDay();
  dt.setDate(dt.getDate() - (dow === 0 ? 6 : dow - 1));
  return `${dt.getFullYear()}-${String(dt.getMonth() + 1).padStart(2, "0")}-${String(dt.getDate()).padStart(2, "0")}`;
}

function formatDayHeader(dateKey) {
  const [y, m, d] = dateKey.split("-").map(Number);
  return new Date(y, m - 1, d, 12).toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" });
}

function weekLabel(mondayKey) {
  const [y, m, d] = mondayKey.split("-").map(Number);
  const start = new Date(y, m - 1, d, 12);
  const end   = new Date(y, m - 1, d + 6, 12);
  const fmt = x => x.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  return `${fmt(start)} – ${fmt(end)}`;
}

function todayPST() {
  return new Date().toLocaleDateString("en-CA", { timeZone: "America/Los_Angeles" });
}

function groupTours(tours) {
  const grouped = {};
  tours.forEach(t => {
    const dk = toDateKey(t.start_dt);
    const wk = toMondayKey(dk);
    if (!grouped[wk]) grouped[wk] = {};
    if (!grouped[wk][dk]) grouped[wk][dk] = [];
    grouped[wk][dk].push(t);
  });
  return grouped;
}

function authHeaders(token) {
  return token
    ? { "Content-Type": "application/json", "Authorization": `Token ${token}` }
    : { "Content-Type": "application/json" };
}

function Badge({ children, color = "#4a5568", border = "rgba(0,0,0,0.08)", bold = false }) {
  return (
    <span style={{ fontSize: 12, color, background: "rgba(255,255,255,0.7)", border: `1px solid ${border}`, borderRadius: 4, padding: "2px 8px", fontWeight: bold ? 600 : 400 }}>
      {children}
    </span>
  );
}

function NavBtn({ onClick, disabled, dir }) {
  const [hov, setHov] = useState(false);
  return (
    <button onClick={onClick} disabled={disabled} onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)}
      style={{ width: 36, height: 36, borderRadius: "50%", outline: "none", flexShrink: 0, display: "flex", alignItems: "center", justifyContent: "center",
        border: `2px solid ${disabled ? "#e2e8f0" : hov ? "#94a3b8" : "#cbd5e0"}`,
        background: disabled ? "transparent" : hov ? "#f1f5f9" : "#fff",
        color: disabled ? "#cbd5e0" : "#0f172a", fontSize: 18, fontWeight: 600,
        cursor: disabled ? "default" : "pointer", transition: "all 0.15s" }}>
      {dir === "left" ? "‹" : "›"}
    </button>
  );
}

function DeleteBtn({ onClick, disabled }) {
  const [hov, setHov] = useState(false);
  return (
    <button onClick={onClick} disabled={disabled}
      onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)}
      title="Delete tour"
      style={{ height: 30, minWidth: 30, borderRadius: 6, outline: "none", display: "flex", alignItems: "center", justifyContent: "center",
        gap: 4, padding: hov ? "0 10px" : "0",
        background: hov ? "#fee2e2" : "#fff",
        border: `2px solid ${hov ? "#fca5a5" : "#e2e8f0"}`,
        color: hov ? "#b91c1c" : "#1a202c",
        fontSize: hov ? 12 : 14, fontWeight: 700,
        cursor: disabled ? "default" : "pointer",
        transition: "all 0.15s", flexShrink: 0, overflow: "hidden", whiteSpace: "nowrap" }}>
      ✕{hov && <span style={{ fontSize: 11, fontWeight: 600 }}>delete</span>}
    </button>
  );
}

function LoginModal({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/auth/login/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || "Login failed");
      } else {
        onLogin(data.token, data.username);
      }
    } catch {
      setError("Network error");
    }
    setLoading(false);
  };

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(15,23,42,0.7)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}>
      <div style={{ background: "#fff", borderRadius: 12, padding: "36px 40px", width: 340, boxShadow: "0 20px 60px rgba(0,0,0,0.3)" }}>
        <div style={{ fontFamily: "'Playfair Display',serif", fontSize: 22, fontWeight: 700, color: "#0f172a", marginBottom: 4 }}>Sign In</div>
        <div style={{ fontSize: 13, color: "#64748b", marginBottom: 24 }}>EA Tours — Director Access</div>
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "#374151", marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.05em" }}>Username</label>
            <input
              type="text" value={username} onChange={e => setUsername(e.target.value)} required autoFocus
              style={{ width: "100%", padding: "10px 12px", borderRadius: 6, border: "1px solid #cbd5e0", fontSize: 14, outline: "none", boxSizing: "border-box" }}
            />
          </div>
          <div style={{ marginBottom: 20 }}>
            <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "#374151", marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.05em" }}>Password</label>
            <input
              type="password" value={password} onChange={e => setPassword(e.target.value)} required
              style={{ width: "100%", padding: "10px 12px", borderRadius: 6, border: "1px solid #cbd5e0", fontSize: 14, outline: "none", boxSizing: "border-box" }}
            />
          </div>
          {error && <div style={{ marginBottom: 16, padding: "8px 12px", background: "#fee2e2", border: "1px solid #fca5a5", borderRadius: 6, fontSize: 13, color: "#b91c1c" }}>{error}</div>}
          <button type="submit" disabled={loading}
            style={{ width: "100%", padding: "11px", borderRadius: 6, border: "none", background: loading ? "#94a3b8" : "#0f172a", color: "#fff", fontSize: 14, fontWeight: 600, cursor: loading ? "default" : "pointer" }}>
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>
      </div>
    </div>
  );
}

function GuestDetailModal({ tour, onClose }) {
  const guests = tour.guests || [];
  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(15,23,42,0.6)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}
      onClick={onClose}>
      <div style={{ background: "#fff", borderRadius: 12, padding: "32px 36px", width: 480, maxWidth: "90vw", boxShadow: "0 20px 60px rgba(0,0,0,0.25)", maxHeight: "80vh", overflowY: "auto" }}
        onClick={e => e.stopPropagation()}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
          <div style={{ fontFamily: "'Playfair Display',serif", fontSize: 20, fontWeight: 700, color: "#0f172a" }}>
            Guest Details
          </div>
          <button onClick={onClose} style={{ border: "none", background: "none", fontSize: 20, cursor: "pointer", color: "#64748b" }}>✕</button>
        </div>

        {guests.length === 0 ? (
          <div style={{ color: "#94a3b8", fontSize: 14 }}>No detail information available for this tour.</div>
        ) : guests.map((g, i) => (
          <div key={i} style={{ marginBottom: guests.length > 1 ? 24 : 0 }}>
            {guests.length > 1 && (
              <div style={{ fontSize: 12, fontWeight: 700, color: "#3b82f6", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 12 }}>
                Guest {i + 1} — {g.guest_name}
              </div>
            )}
            {[
              ["Contact Name", g.contact_name],
              ["Group Name", g.group_name],
              ["Cell # Day of Tour", g.cell_number],
              ["Purpose of Visit", g.purpose_of_visit],
              ["Major of Interest", g.major_of_interest],
              ["Questions / Comments", g.questions_comments],
            ].map(([label, value]) => value ? (
              <div key={label} style={{ marginBottom: 14 }}>
                <div style={{ fontSize: 11, fontWeight: 600, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 3 }}>{label}</div>
                <div style={{ fontSize: 14, color: "#1a202c" }}>{value}</div>
              </div>
            ) : null)}
            {i < guests.length - 1 && <div style={{ borderTop: "1px solid #e2e8f0", marginTop: 16 }} />}
          </div>
        ))}
      </div>
    </div>
  );
}

function TourCard({ tour, onStatusChange, onDelete, token }) {
  const [updating, setUpdating] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const isMobile = useIsMobile();
  const cfg = STATUS[tour.status] || STATUS.unassigned;
  const guests = Array.isArray(tour.guest_name) ? tour.guest_name : tour.guest_name ? [tour.guest_name] : ["Guest"];
  const isAuth = !!token;
  const hasDetails = tour.guests && tour.guests.length > 0 && tour.guests.some(g => g.contact_name || g.cell_number || g.major_of_interest);

  const setStatus = async (newStatus) => {
    setUpdating(true);
    try {
      await fetch(`/api/tours/${tour.id}/update_status/`, { method: "PATCH", headers: authHeaders(token), body: JSON.stringify({ status: newStatus }) });
      onStatusChange(tour.id, newStatus);
    } catch (e) { console.error(e); }
    setUpdating(false);
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await fetch(`/api/tours/${tour.id}/delete/`, { method: "DELETE", headers: authHeaders(token) });
      onDelete(tour.id);
      window.location.reload();
    } catch (e) { console.error(e); setDeleting(false); setConfirmDelete(false); }
  };

  return (
    <>
    {showDetails && <GuestDetailModal tour={tour} onClose={() => setShowDetails(false)} />}
    <div style={{ background: cfg.light, border: `2px solid ${cfg.border}`, borderRadius: 10, padding: isMobile ? "14px 14px" : "16px 20px", marginBottom: 10,
      display: "flex", flexDirection: isMobile ? "column" : "row", alignItems: isMobile ? "flex-start" : "center",
      justifyContent: "space-between", boxShadow: "0 1px 4px rgba(0,0,0,0.06)", opacity: (updating || deleting) ? 0.6 : 1, transition: "opacity 0.2s" }}>
      <div style={{ flex: 1, width: "100%" }}>
        <div style={{ fontSize: 13, color: cfg.color, fontFamily: "'DM Mono',monospace", fontWeight: 600, letterSpacing: "0.05em" }}>
          {formatTime(tour.start_dt)}
        </div>
        {guests.map((name, i) => (
          <div key={i} style={{ fontSize: i === 0 ? (isMobile ? 18 : 16) : 14, fontWeight: i === 0 ? 600 : 400, color: i === 0 ? "#1a202c" : "#4a5568", fontFamily: "'Playfair Display',serif", marginTop: i === 0 ? 2 : 0, lineHeight: 1.4 }}>
            {name}
          </div>
        ))}
        <div style={{ display: "flex", gap: 8, marginTop: 6, flexWrap: "wrap", alignItems: "center" }}>
          <Badge>{tour.number_of_guests} {tour.number_of_guests === 1 ? "guest" : "guests"}</Badge>
          {guests.length > 1 && <Badge color="#2b6cb0" border="#90cdf4">{guests.length} groups</Badge>}
          {tour.group_tour && <Badge color="#553c9a" border="#d6bcfa">Group Tour</Badge>}
          <Badge color={cfg.color} border={cfg.border} bold>{cfg.label}</Badge>
          {hasDetails && (
            <button onClick={() => setShowDetails(true)}
              style={{ fontSize: 11, color: "#3b82f6", background: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: 4, padding: "2px 8px", fontWeight: 600, cursor: "pointer" }}>
              View Details
            </button>
          )}
        </div>
      </div>

      {isAuth && (
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginLeft: isMobile ? 0 : 16, marginTop: isMobile ? 12 : 0, flexShrink: 0, width: isMobile ? "100%" : "auto", justifyContent: isMobile ? "space-between" : "flex-end" }}>
          {confirmDelete && (
            <div style={{ display: "flex", alignItems: "center", gap: 8, background: "#fff1f2", border: "1px solid #fecdd3", borderRadius: 8, padding: "6px 12px" }}>
              <span style={{ fontSize: 12, color: "#9f1239", fontWeight: 500 }}>Delete?</span>
              <button onClick={handleDelete} disabled={deleting}
                style={{ padding: "3px 10px", borderRadius: 5, border: "none", background: "#e11d48", color: "#fff", fontSize: 12, fontWeight: 600, cursor: "pointer" }}>
                {deleting ? "…" : "Yes"}
              </button>
              <button onClick={() => setConfirmDelete(false)} disabled={deleting}
                style={{ padding: "3px 10px", borderRadius: 5, border: "1px solid #cbd5e0", background: "#fff", color: "#475569", fontSize: 12, fontWeight: 500, cursor: "pointer" }}>
                Cancel
              </button>
            </div>
          )}

          <div style={{ display: "flex", gap: isMobile ? 12 : 8 }}>
            {Object.entries(STATUS).map(([key, s]) => (
              <button key={key} onClick={() => setStatus(key)} disabled={updating || tour.status === key} title={s.label}
                style={{ width: isMobile ? 36 : 30, height: isMobile ? 36 : 30, borderRadius: "50%", outline: "none", background: s.border, transition: "all 0.15s",
                  border: tour.status === key ? "3px solid #1a202c" : `2px solid ${s.border}`,
                  opacity: tour.status === key ? 1 : 0.5, transform: tour.status === key ? "scale(1.2)" : "scale(1)",
                  cursor: tour.status === key ? "default" : "pointer" }} />
            ))}
          </div>

          <DeleteBtn onClick={() => setConfirmDelete(true)} disabled={updating || confirmDelete} />
        </div>
      )}
    </div>
    </>
  );
}

export default function App() {
  const [tours, setTours] = useState([]);
  const [loading, setLoading] = useState(true);
  const [weekIdx, setWeekIdx] = useState(0);
  const [scraping, setScraping] = useState(false);
  const [scrapeMsg, setScrapeMsg] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem("auth_token"));
  const [username, setUsername] = useState(() => localStorage.getItem("auth_username"));
  const [showLogin, setShowLogin] = useState(false);
  const [showMobileMenu, setShowMobileMenu] = useState(false);
  const isMobile = useIsMobile();

  const handleLogin = (tok, user) => {
    localStorage.setItem("auth_token", tok);
    localStorage.setItem("auth_username", user);
    setToken(tok);
    setUsername(user);
    setShowLogin(false);
  };

  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("auth_username");
    setToken(null);
    setUsername(null);
  };

  // Send the token so signed-in users get full guest details; refetch when the
  // token changes (login/logout) so the view swaps between full and redacted data.
  useEffect(() => {
    fetch("/api/tours/", { headers: authHeaders(token) }).then(r => r.json()).then(data => { setTours(data); setLoading(false); }).catch(() => setLoading(false));
  }, [token]);

  const grouped = groupTours(tours);
  const weekKeys = Object.keys(grouped).sort();

  useEffect(() => {
    if (!loading && weekKeys.length) {
      const idx = weekKeys.indexOf(toMondayKey(todayPST()));
      setWeekIdx(idx >= 0 ? idx : 0);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading]);

  const activeWeek = weekKeys[weekIdx] || "";
  const weekDays = activeWeek ? grouped[activeWeek] : {};
  const weekTours = Object.values(weekDays).flat();
  const weekNum = tours.find(t => toMondayKey(toDateKey(t.start_dt)) === activeWeek)?.week_number ?? "—";
  const todayCount = tours.filter(t => toDateKey(t.start_dt) === todayPST()).length;

  const handleStatusChange = (id, status) => setTours(prev => prev.map(t => t.id === id ? { ...t, status } : t));
  const handleDelete = (id) => setTours(prev => prev.filter(t => t.id !== id));

  const handleLoad = async () => {
    setScraping(true); setScrapeMsg(null);
    try {
      const res = await fetch("/api/tours/scrape/", { method: "POST", headers: authHeaders(token) });
      const data = await res.json();
      setScrapeMsg({ type: res.status === 429 ? "warning" : "success", text: res.status === 429 ? data.message : "Scraper triggered! New tours will appear shortly." });
    } catch { setScrapeMsg({ type: "error", text: "Failed to trigger scraper." }); }
    setScraping(false);
    setTimeout(() => setScrapeMsg(null), 4000);
  };

  const msgColors = { success: ["#052e16","#86efac","#166534"], warning: ["#2d1f00","#fcd34d","#854d0e"], error: ["#2d0a0a","#fca5a5","#7f1d1d"] };

  return (
    <div style={{ display: "flex", flexDirection: "column", minHeight: "100vh", fontFamily: "'DM Sans',sans-serif", background: "#f8fafc" }}>
      <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=Playfair+Display:wght@600;700&family=DM+Mono&display=swap" rel="stylesheet" />

      {showLogin && <LoginModal onLogin={handleLogin} />}

      {/* Mobile drawer overlay */}
      {isMobile && showMobileMenu && (
        <div onClick={() => setShowMobileMenu(false)}
          style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", zIndex: 50 }} />
      )}

      {/* Mobile drawer */}
      {isMobile && (
        <div style={{ position: "fixed", top: 0, left: showMobileMenu ? 0 : "-280px", width: 260, height: "100%", background: "#0f172a", zIndex: 100, transition: "left 0.25s ease", display: "flex", flexDirection: "column", padding: "48px 0 24px" }}>
          <div style={{ padding: "0 24px 24px", borderBottom: "1px solid #1e293b" }}>
            <div style={{ fontSize: 11, letterSpacing: "0.15em", color: "#64748b", textTransform: "uppercase", marginBottom: 4 }}>EA Tours</div>
            <div style={{ fontSize: 20, fontWeight: 700, fontFamily: "'Playfair Display',serif", color: "#f1f5f9" }}>Scheduler</div>
          </div>
          <div style={{ padding: "20px 16px", flex: 1 }}>
            {token && (
              <button onClick={() => { handleLoad(); setShowMobileMenu(false); }} disabled={scraping}
                style={{ width: "100%", padding: "12px", borderRadius: 6, display: "flex", alignItems: "center", gap: 10, background: scraping ? "#1e293b" : "#1e3a5f", border: "1px solid #2d5a8e", color: scraping ? "#64748b" : "#93c5fd", fontSize: 14, fontWeight: 500, cursor: scraping ? "default" : "pointer", marginBottom: 8 }}>
                <span>{scraping ? "⏳" : "🔄"}</span>
                {scraping ? "Loading..." : "Load New Tours"}
              </button>
            )}
            {scrapeMsg && (
              <div style={{ padding: "8px 10px", borderRadius: 6, fontSize: 12, background: msgColors[scrapeMsg.type][0], color: msgColors[scrapeMsg.type][1], border: `1px solid ${msgColors[scrapeMsg.type][2]}`, marginBottom: 8 }}>
                {scrapeMsg.text}
              </div>
            )}
            <div style={{ marginTop: 16 }}>
              <div style={{ fontSize: 11, letterSpacing: "0.1em", color: "#475569", textTransform: "uppercase", marginBottom: 10 }}>Status</div>
              {Object.entries(STATUS).map(([, cfg]) => (
                <div key={cfg.label} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                  <div style={{ width: 10, height: 10, borderRadius: "50%", background: cfg.border }} />
                  <span style={{ fontSize: 13, color: "#94a3b8" }}>{cfg.label}</span>
                </div>
              ))}
            </div>
          </div>
          <div style={{ padding: "16px 24px", borderTop: "1px solid #1e293b" }}>
            {token ? (
              <>
                <div style={{ fontSize: 12, color: "#64748b", marginBottom: 8 }}>Signed in as <span style={{ color: "#94a3b8", fontWeight: 600 }}>{username}</span></div>
                <button onClick={() => { handleLogout(); setShowMobileMenu(false); }}
                  style={{ width: "100%", padding: "10px", borderRadius: 6, border: "1px solid #334155", background: "transparent", color: "#64748b", fontSize: 13, fontWeight: 500, cursor: "pointer" }}>
                  Sign Out
                </button>
              </>
            ) : (
              <button onClick={() => { setShowLogin(true); setShowMobileMenu(false); }}
                style={{ width: "100%", padding: "10px", borderRadius: 6, border: "1px solid #334155", background: "#1e293b", color: "#93c5fd", fontSize: 13, fontWeight: 500, cursor: "pointer" }}>
                Sign In
              </button>
            )}
          </div>
        </div>
      )}

      <div style={{ display: "flex", flex: 1 }}>
        {/* Desktop Sidebar */}
        {!isMobile && (
          <div style={{ width: 240, minWidth: 240, background: "#0f172a", color: "#e2e8f0", display: "flex", flexDirection: "column", padding: "32px 0" }}>
            <div style={{ padding: "0 24px 32px", borderBottom: "1px solid #1e293b" }}>
              <div style={{ fontSize: 11, letterSpacing: "0.15em", color: "#64748b", textTransform: "uppercase", marginBottom: 6 }}>EA Tours</div>
              <div style={{ fontSize: 22, fontWeight: 700, fontFamily: "'Playfair Display',serif", color: "#f1f5f9" }}>Scheduler</div>
            </div>
            <nav style={{ padding: "24px 16px", flex: 1 }}>
              {[{ label: "Tour Schedule", icon: "📅", active: true }].map(item => (
                <div key={item.label} style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 12px", borderRadius: 6, marginBottom: 4, fontSize: 14, fontWeight: 500, background: item.active ? "#1e293b" : "transparent", color: item.active ? "#f1f5f9" : "#64748b", cursor: "pointer" }}>
                  <span style={{ fontSize: 16 }}>{item.icon}</span>
                  {item.label}
                </div>
              ))}
              {token && (
                <div style={{ marginTop: 8 }}>
                  <button onClick={handleLoad} disabled={scraping} style={{ width: "100%", padding: "10px 12px", borderRadius: 6, display: "flex", alignItems: "center", gap: 10, background: scraping ? "#1e293b" : "#1e3a5f", border: "1px solid #2d5a8e", color: scraping ? "#64748b" : "#93c5fd", fontSize: 14, fontWeight: 500, cursor: scraping ? "default" : "pointer" }}>
                    <span style={{ fontSize: 16 }}>{scraping ? "⏳" : "🔄"}</span>
                    {scraping ? "Loading..." : "Load New Tours"}
                  </button>
                  {scrapeMsg && (
                    <div style={{ marginTop: 8, padding: "8px 10px", borderRadius: 6, fontSize: 12, background: msgColors[scrapeMsg.type][0], color: msgColors[scrapeMsg.type][1], border: `1px solid ${msgColors[scrapeMsg.type][2]}` }}>
                      {scrapeMsg.text}
                    </div>
                  )}
                </div>
              )}
            </nav>
            <div style={{ padding: 24, borderTop: "1px solid #1e293b" }}>
              <div style={{ fontSize: 11, letterSpacing: "0.1em", color: "#475569", textTransform: "uppercase", marginBottom: 12 }}>Status</div>
              {Object.entries(STATUS).map(([, cfg]) => (
                <div key={cfg.label} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                  <div style={{ width: 10, height: 10, borderRadius: "50%", background: cfg.border }} />
                  <span style={{ fontSize: 13, color: "#94a3b8" }}>{cfg.label}</span>
                </div>
              ))}
              <div style={{ marginTop: 16, paddingTop: 16, borderTop: "1px solid #1e293b" }}>
                {token ? (
                  <div>
                    <div style={{ fontSize: 12, color: "#64748b", marginBottom: 8 }}>Signed in as <span style={{ color: "#94a3b8", fontWeight: 600 }}>{username}</span></div>
                    <button onClick={handleLogout} style={{ width: "100%", padding: "8px 12px", borderRadius: 6, border: "1px solid #334155", background: "transparent", color: "#64748b", fontSize: 13, fontWeight: 500, cursor: "pointer" }}>Sign Out</button>
                  </div>
                ) : (
                  <button onClick={() => setShowLogin(true)} style={{ width: "100%", padding: "8px 12px", borderRadius: 6, border: "1px solid #334155", background: "#1e293b", color: "#93c5fd", fontSize: 13, fontWeight: 500, cursor: "pointer" }}>Sign In</button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Main content */}
        <div style={{ flex: 1, overflowY: "auto" }}>

          {/* Mobile top bar */}
          {isMobile && (
            <div style={{ background: "#0f172a", padding: "14px 16px", display: "flex", alignItems: "center", justifyContent: "space-between", position: "sticky", top: 0, zIndex: 40 }}>
              <button onClick={() => setShowMobileMenu(true)}
                style={{ background: "none", border: "none", color: "#e2e8f0", fontSize: 22, cursor: "pointer", padding: 4 }}>☰</button>
              <div style={{ fontFamily: "'Playfair Display',serif", fontWeight: 700, color: "#f1f5f9", fontSize: 18 }}>EA Tours</div>
              <button onClick={() => token ? setShowLogin(false) : setShowLogin(true)}
                style={{ background: "none", border: "none", color: token ? "#48bb78" : "#93c5fd", fontSize: 13, fontWeight: 600, cursor: "pointer" }}>
                {token ? "✓ In" : "Sign In"}
              </button>
            </div>
          )}

          <div style={{ padding: isMobile ? "20px 16px" : "40px 48px", maxWidth: isMobile ? "100%" : 860 + 96, margin: "0 auto" }}>
            <div style={{ maxWidth: 860 }}>

              {/* Header */}
              <div style={{ marginBottom: isMobile ? 20 : 32, display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
                <div>
                  <h1 style={{ fontSize: isMobile ? 24 : 28, fontWeight: 700, fontFamily: "'Playfair Display',serif", color: "#0f172a", margin: 0 }}>Tour Schedule</h1>
                  <p style={{ color: "#64748b", fontSize: 13, margin: "4px 0 0" }}>
                    {new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", timeZone: "America/Los_Angeles" })}
                  </p>
                </div>
                {!loading && (
                  <div style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: 8, padding: "8px 14px", textAlign: "center", boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
                    <div style={{ fontSize: 20, fontWeight: 700, color: "#3b82f6", fontFamily: "'Playfair Display',serif", lineHeight: 1 }}>{todayCount}</div>
                    <div style={{ fontSize: 10, color: "#94a3b8", marginTop: 3, textTransform: "uppercase", letterSpacing: "0.05em" }}>Today</div>
                  </div>
                )}
              </div>

              {/* Week navigator */}
              {!loading && weekKeys.length > 0 && (
                <div style={{ marginBottom: isMobile ? 20 : 32, background: "#fff", border: "1px solid #e2e8f0", borderRadius: 10, padding: isMobile ? "12px 14px" : "16px 20px", display: "flex", alignItems: "center", gap: isMobile ? 8 : 16, boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
                  <NavBtn onClick={() => setWeekIdx(i => Math.max(0, i - 1))} disabled={weekIdx === 0} dir="left" />
                  <div style={{ flex: 1, textAlign: "center" }}>
                    <div style={{ fontSize: isMobile ? 17 : 20, fontWeight: 700, fontFamily: "'Playfair Display',serif", color: "#0f172a", marginBottom: 2 }}>Week {weekNum}</div>
                    <div style={{ fontSize: 12, color: "#64748b", marginBottom: isMobile ? 4 : 6 }}>{weekLabel(activeWeek)}</div>
                    <div style={{ fontSize: 11, display: "flex", justifyContent: "center", gap: isMobile ? 6 : 12, flexWrap: "wrap" }}>
                      <span style={{ color: "#3b82f6", fontWeight: 500 }}>{weekTours.length} {weekTours.length === 1 ? "tour" : "tours"}</span>
                      <span style={{ color: "#cbd5e0" }}>|</span>
                      <span style={{ color: "#22c55e", fontWeight: 500 }}>{weekTours.filter(t => t.status === "confirmed").length} confirmed</span>
                      {!isMobile && <span style={{ color: "#cbd5e0" }}>|</span>}
                      {weekTours.filter(t => t.status === "unassigned").length > 0
                        ? <span style={{ color: "#ef4444", fontWeight: 600 }}>⚠️ {weekTours.filter(t => t.status === "unassigned").length} need attention</span>
                        : <span style={{ color: "#94a3b8" }}>✓ all assigned</span>}
                    </div>
                  </div>
                  <NavBtn onClick={() => setWeekIdx(i => Math.min(weekKeys.length - 1, i + 1))} disabled={weekIdx === weekKeys.length - 1} dir="right" />
                </div>
              )}

              {/* Tours */}
              {loading ? (
                <div style={{ color: "#94a3b8", fontSize: 15 }}>Loading tours...</div>
              ) : weekKeys.length === 0 ? (
                <div style={{ color: "#94a3b8", fontSize: 15 }}>No upcoming tours found.</div>
              ) : (
                Object.keys(weekDays).sort().map(dk => {
                  const dayTours = [...weekDays[dk]].sort((a, b) => parseWallClock(a.start_dt) - parseWallClock(b.start_dt));
                  return (
                    <div key={dk} style={{ marginBottom: isMobile ? 20 : 28 }}>
                      <div style={{ fontSize: 13, fontWeight: 700, color: "#334155", marginBottom: 10, display: "flex", alignItems: "center", gap: 8 }}>
                        <div style={{ width: 7, height: 7, borderRadius: "50%", background: "#3b82f6" }} />
                        {formatDayHeader(dk)}
                        <span style={{ fontSize: 11, color: "#94a3b8", fontWeight: 400 }}>{dayTours.length} {dayTours.length === 1 ? "tour" : "tours"}</span>
                      </div>
                      {dayTours.map(tour => <TourCard key={tour.id} tour={tour} onStatusChange={handleStatusChange} onDelete={handleDelete} token={token} />)}
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
