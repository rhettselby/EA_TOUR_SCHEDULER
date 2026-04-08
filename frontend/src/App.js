import { useState, useEffect } from "react";

const STATUS = {
  unassigned:    { label: "Unassigned",    color: "#c53030", bg: "#fff5f5", border: "#fc8181", light: "#fed7d7" },
  message_sent:  { label: "Message Sent",  color: "#b7791f", bg: "#fffff0", border: "#ecc94b", light: "#fefcbf" },
  confirmed:     { label: "Confirmed",     color: "#276749", bg: "#f0fff4", border: "#48bb78", light: "#c6f6d5" },
  past_event:    { label: "Past Event",    color: "#2d3748", bg: "#f7fafc", border: "#718096", light: "#e2e8f0" },
};

// Parse backend datetime strings as wall-clock (backend already converts to PST)
function parseLocal(dtStr) {
  return new Date(dtStr.replace(/([+-]\d{2}:\d{2}|Z)$/, ""));
}

function formatTime(dtStr) {
  const d = parseLocal(dtStr);
  const h = d.getHours(), m = d.getMinutes();
  return `${h % 12 || 12}:${String(m).padStart(2, "0")} ${h >= 12 ? "PM" : "AM"}`;
}

function toDateKey(dtStr) {
  const d = parseLocal(dtStr);
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

// Use Intl to get today's date in PST/PDT correctly
function todayPST() {
  return new Date().toLocaleDateString("en-CA", { timeZone: "America/Los_Angeles" }); // en-CA gives YYYY-MM-DD
}

// Group tours: { weekKey: { dateKey: [tours] } }
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

// ── TourCard ──────────────────────────────────────────────────────────────────

function TourCard({ tour, onStatusChange }) {
  const [updating, setUpdating] = useState(false);
  const cfg = STATUS[tour.status] || STATUS.unassigned;
  const guests = Array.isArray(tour.guest_name) ? tour.guest_name : tour.guest_name ? [tour.guest_name] : ["Guest"];

  const setStatus = async (newStatus) => {
    setUpdating(true);
    try {
      await fetch(`/api/tours/${tour.id}/update_status/`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus }),
      });
      onStatusChange(tour.id, newStatus);
    } catch (e) {
      console.error("Failed to update status", e);
    }
    setUpdating(false);
  };

  return (
    <div style={{
      background: cfg.light, border: `2px solid ${cfg.border}`, borderRadius: 10,
      padding: "16px 20px", marginBottom: 10, display: "flex", alignItems: "center",
      justifyContent: "space-between", boxShadow: "0 1px 4px rgba(0,0,0,0.06)",
      opacity: updating ? 0.6 : 1, transition: "opacity 0.2s",
    }}>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 13, color: cfg.color, fontFamily: "'DM Mono',monospace", fontWeight: 600, letterSpacing: "0.05em" }}>
          {formatTime(tour.start_dt)}
        </div>

        {guests.length > 1 ? guests.map((name, i) => (
          <div key={i} style={{ fontSize: i === 0 ? 15 : 14, fontWeight: i === 0 ? 600 : 400, color: i === 0 ? "#1a202c" : "#4a5568", fontFamily: "'Playfair Display',serif", lineHeight: 1.4, marginTop: i === 0 ? 4 : 0 }}>
            {name}
          </div>
        )) : (
          <div style={{ fontSize: 16, fontWeight: 600, color: "#1a202c", marginTop: 2, fontFamily: "'Playfair Display',serif" }}>
            {guests[0]}
          </div>
        )}

        <div style={{ display: "flex", gap: 8, marginTop: 6, flexWrap: "wrap", alignItems: "center" }}>
          <Badge>{tour.number_of_guests} {tour.number_of_guests === 1 ? "guest" : "guests"}</Badge>
          {guests.length > 1 && <Badge color="#2b6cb0" border="#90cdf4">{guests.length} groups</Badge>}
          {tour.group_tour && <Badge color="#553c9a" border="#d6bcfa">Group Tour</Badge>}
          <Badge color={cfg.color} border={cfg.border} bold>{cfg.label}</Badge>
        </div>
      </div>

      <div style={{ display: "flex", gap: 8, marginLeft: 16, flexShrink: 0 }}>
        {Object.entries(STATUS).map(([key, s]) => (
          <button key={key} onClick={() => setStatus(key)} disabled={updating || tour.status === key} title={s.label}
            style={{
              width: 30, height: 30, borderRadius: "50%", cursor: tour.status === key ? "default" : "pointer",
              border: tour.status === key ? "3px solid #1a202c" : `2px solid ${s.border}`,
              background: s.border, opacity: tour.status === key ? 1 : 0.5, outline: "none",
              transform: tour.status === key ? "scale(1.2)" : "scale(1)", transition: "all 0.15s",
            }}
          />
        ))}
      </div>
    </div>
  );
}

function Badge({ children, color = "#4a5568", border = "rgba(0,0,0,0.08)", bold = false }) {
  return (
    <span style={{
      fontSize: 12, color, background: "rgba(255,255,255,0.7)", border: `1px solid ${border}`,
      borderRadius: 4, padding: "2px 8px", fontWeight: bold ? 600 : 400,
    }}>
      {children}
    </span>
  );
}

function NavBtn({ onClick, disabled, dir }) {
  const [hov, setHov] = useState(false);
  return (
    <button onClick={onClick} disabled={disabled}
      onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)}
      style={{
        width: 36, height: 36, borderRadius: "50%", outline: "none", flexShrink: 0,
        border: `2px solid ${disabled ? "#e2e8f0" : hov ? "#94a3b8" : "#cbd5e0"}`,
        background: disabled ? "transparent" : hov ? "#f1f5f9" : "#fff",
        color: disabled ? "#cbd5e0" : "#0f172a", fontSize: 18, fontWeight: 600,
        cursor: disabled ? "default" : "pointer", transition: "all 0.15s",
        display: "flex", alignItems: "center", justifyContent: "center",
      }}>
      {dir === "left" ? "‹" : "›"}
    </button>
  );
}

// ── App ───────────────────────────────────────────────────────────────────────

export default function App() {
  const [tours, setTours] = useState([]);
  const [loading, setLoading] = useState(true);
  const [weekIdx, setWeekIdx] = useState(0);
  const [scraping, setScraping] = useState(false);
  const [scrapeMsg, setScrapeMsg] = useState(null);

  useEffect(() => {
    fetch("/api/tours/").then(r => r.json()).then(data => { setTours(data); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  const grouped = groupTours(tours);
  const weekKeys = Object.keys(grouped).sort();

  // Jump to current week on load
  useEffect(() => {
    if (!loading && weekKeys.length) {
      const idx = weekKeys.indexOf(toMondayKey(todayPST()));
      setWeekIdx(idx >= 0 ? idx : 0);
    }
  }, [loading]);

  const activeWeek = weekKeys[weekIdx] || "";
  const weekDays = activeWeek ? grouped[activeWeek] : {};
  const todayTours = tours.filter(t => toDateKey(t.start_dt) === todayPST());
  const weekTours = Object.values(weekDays).flat();
  const weekNum = tours.find(t => toMondayKey(toDateKey(t.start_dt)) === activeWeek)?.week_number ?? "—";

  const handleStatusChange = (id, status) =>
    setTours(prev => prev.map(t => t.id === id ? { ...t, status } : t));

  const handleLoad = async () => {
    setScraping(true); setScrapeMsg(null);
    try {
      const res = await fetch("/api/tours/scrape/", { method: "POST" });
      const data = await res.json();
      setScrapeMsg({ type: res.status === 429 ? "warning" : "success", text: res.status === 429 ? data.message : "Scraper triggered! New tours will appear shortly." });
    } catch { setScrapeMsg({ type: "error", text: "Failed to trigger scraper." }); }
    setScraping(false);
    setTimeout(() => setScrapeMsg(null), 4000);
  };

  const msgBg   = { success: "#052e16", warning: "#2d1f00", error: "#2d0a0a" };
  const msgFg   = { success: "#86efac", warning: "#fcd34d", error: "#fca5a5" };
  const msgBord = { success: "#166534", warning: "#854d0e", error: "#7f1d1d" };

  return (
    <div style={{ display: "flex", minHeight: "100vh", fontFamily: "'DM Sans',sans-serif", background: "#f8fafc" }}>
      <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=Playfair+Display:wght@600;700&family=DM+Mono&display=swap" rel="stylesheet" />

      {/* Sidebar */}
      <div style={{ width: 240, minWidth: 240, background: "#0f172a", color: "#e2e8f0", display: "flex", flexDirection: "column", padding: "32px 0" }}>
        <div style={{ padding: "0 24px 32px", borderBottom: "1px solid #1e293b" }}>
          <div style={{ fontSize: 11, letterSpacing: "0.15em", color: "#64748b", textTransform: "uppercase", marginBottom: 6 }}>EA Tours</div>
          <div style={{ fontSize: 22, fontWeight: 700, fontFamily: "'Playfair Display',serif", color: "#f1f5f9" }}>Scheduler</div>
        </div>

        <nav style={{ padding: "24px 16px", flex: 1 }}>
          {[{ label: "Tour Schedule", icon: "📅", active: true }, { label: "AI Agent", icon: "🤖", soon: true }].map(item => (
            <div key={item.label} style={{
              display: "flex", alignItems: "center", gap: 10, padding: "10px 12px", borderRadius: 6, marginBottom: 4,
              background: item.active ? "#1e293b" : "transparent", color: item.active ? "#f1f5f9" : "#64748b",
              cursor: item.soon ? "default" : "pointer", fontSize: 14, fontWeight: 500,
            }}>
              <span style={{ fontSize: 16 }}>{item.icon}</span>
              {item.label}
              {item.soon && <span style={{ marginLeft: "auto", fontSize: 10, color: "#475569", background: "#1e293b", padding: "2px 6px", borderRadius: 4 }}>Soon</span>}
            </div>
          ))}

          <div style={{ marginTop: 8 }}>
            <button onClick={handleLoad} disabled={scraping} style={{
              width: "100%", padding: "10px 12px", borderRadius: 6, display: "flex", alignItems: "center", gap: 10,
              background: scraping ? "#1e293b" : "#1e3a5f", border: "1px solid #2d5a8e",
              color: scraping ? "#64748b" : "#93c5fd", fontSize: 14, fontWeight: 500,
              cursor: scraping ? "default" : "pointer", transition: "background 0.2s",
            }}>
              <span style={{ fontSize: 16 }}>{scraping ? "⏳" : "🔄"}</span>
              {scraping ? "Loading..." : "Load New Tours"}
            </button>
            <div style={{ fontSize: 11, color: "#475569", marginTop: 6, padding: "0 4px", lineHeight: 1.4 }}>⚠️ Use sparingly — high memory usage</div>
            {scrapeMsg && (
              <div style={{ marginTop: 8, padding: "8px 10px", borderRadius: 6, fontSize: 12, background: msgBg[scrapeMsg.type], color: msgFg[scrapeMsg.type], border: `1px solid ${msgBord[scrapeMsg.type]}` }}>
                {scrapeMsg.text}
              </div>
            )}
          </div>
        </nav>

        <div style={{ padding: 24, borderTop: "1px solid #1e293b" }}>
          <div style={{ fontSize: 11, letterSpacing: "0.1em", color: "#475569", textTransform: "uppercase", marginBottom: 12 }}>Status</div>
          {Object.entries(STATUS).map(([, cfg]) => (
            <div key={cfg.label} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
              <div style={{ width: 10, height: 10, borderRadius: "50%", background: cfg.border }} />
              <span style={{ fontSize: 13, color: "#94a3b8" }}>{cfg.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Main */}
      <div style={{ flex: 1, padding: "40px 48px", overflowY: "auto" }}>
        <div style={{ maxWidth: 860 }}>

          {/* Header */}
          <div style={{ marginBottom: 32, display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
            <div>
              <h1 style={{ fontSize: 28, fontWeight: 700, fontFamily: "'Playfair Display',serif", color: "#0f172a", margin: 0 }}>Tour Schedule</h1>
              <p style={{ color: "#64748b", fontSize: 14, margin: "4px 0 0" }}>
                {new Date().toLocaleDateString("en-US", { weekday: "long", year: "numeric", month: "long", day: "numeric", timeZone: "America/Los_Angeles" })}
              </p>
            </div>
            {!loading && (
              <div style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: 8, padding: "10px 18px", textAlign: "center", boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
                <div style={{ fontSize: 22, fontWeight: 700, color: "#3b82f6", fontFamily: "'Playfair Display',serif", lineHeight: 1 }}>{todayTours.length}</div>
                <div style={{ fontSize: 11, color: "#94a3b8", marginTop: 3, textTransform: "uppercase", letterSpacing: "0.05em" }}>Tours Today</div>
              </div>
            )}
          </div>

          {/* Week navigator */}
          {!loading && weekKeys.length > 0 && (
            <div style={{ marginBottom: 32, background: "#fff", border: "1px solid #e2e8f0", borderRadius: 10, padding: "16px 20px", display: "flex", alignItems: "center", gap: 16, boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
              <NavBtn onClick={() => setWeekIdx(i => Math.max(0, i - 1))} disabled={weekIdx === 0} dir="left" />
              <div style={{ flex: 1, textAlign: "center" }}>
                <div style={{ fontSize: 20, fontWeight: 700, fontFamily: "'Playfair Display',serif", color: "#0f172a", marginBottom: 2 }}>Week {weekNum}</div>
                <div style={{ fontSize: 13, color: "#64748b", marginBottom: 6 }}>{weekLabel(activeWeek)}</div>
                <div style={{ fontSize: 12, display: "flex", justifyContent: "center", gap: 12 }}>
                  <span style={{ color: "#3b82f6", fontWeight: 500 }}>{weekTours.length} {weekTours.length === 1 ? "tour" : "tours"}</span>
                  <span style={{ color: "#cbd5e0" }}>|</span>
                  <span style={{ color: "#22c55e", fontWeight: 500 }}>{weekTours.filter(t => t.status === "confirmed").length} confirmed</span>
                  <span style={{ color: "#cbd5e0" }}>|</span>
                  {weekTours.filter(t => t.status === "unassigned").length > 0
                    ? <span style={{ color: "#ef4444", fontWeight: 600 }}>⚠️ {weekTours.filter(t => t.status === "unassigned").length} need attention</span>
                    : <span style={{ color: "#94a3b8" }}>✓ all assigned</span>}
                </div>
              </div>
              <NavBtn onClick={() => setWeekIdx(i => Math.min(weekKeys.length - 1, i + 1))} disabled={weekIdx === weekKeys.length - 1} dir="right" />
            </div>
          )}

          {/* Tours list */}
          {loading ? (
            <div style={{ color: "#94a3b8", fontSize: 15 }}>Loading tours...</div>
          ) : weekKeys.length === 0 ? (
            <div style={{ color: "#94a3b8", fontSize: 15 }}>No upcoming tours found.</div>
          ) : (
            Object.keys(weekDays).sort().map(dk => {
              const dayTours = [...weekDays[dk]].sort((a, b) => parseLocal(a.start_dt) - parseLocal(b.start_dt));
              return (
                <div key={dk} style={{ marginBottom: 28 }}>
                  <div style={{ fontSize: 14, fontWeight: 700, color: "#334155", marginBottom: 12, display: "flex", alignItems: "center", gap: 10 }}>
                    <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#3b82f6" }} />
                    {formatDayHeader(dk)}
                    <span style={{ fontSize: 12, color: "#94a3b8", fontWeight: 400 }}>{dayTours.length} {dayTours.length === 1 ? "tour" : "tours"}</span>
                  </div>
                  {dayTours.map(tour => <TourCard key={tour.id} tour={tour} onStatusChange={handleStatusChange} />)}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}