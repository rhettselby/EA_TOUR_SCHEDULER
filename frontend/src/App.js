import { useState, useEffect } from "react";

const STATUS_CONFIG = {
  unassigned: { label: "Unassigned", color: "#e53e3e", bg: "#fff5f5", border: "#fc8181" },
  message_sent: { label: "Message Sent", color: "#b7791f", bg: "#fffff0", border: "#f6e05e" },
  confirmed: { label: "Confirmed", color: "#276749", bg: "#f0fff4", border: "#68d391" },
  past_event: { label: "Past Event", color: "#4a5568", bg: "#f7fafc", border: "#a0aec0" },
};

function formatTime(dt) {
  const d = new Date(dt);
  return d.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", hour12: true });
}

function formatDayHeader(dateStr) {
  const d = new Date(dateStr);
  return d.toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" });
}

function getWeekLabel(dateStr) {
  const d = new Date(dateStr);
  const weekStart = new Date(d);
  weekStart.setDate(d.getDate() - d.getDay());
  const weekEnd = new Date(weekStart);
  weekEnd.setDate(weekStart.getDate() + 6);
  const fmt = (x) => x.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  return `Week of ${fmt(weekStart)} – ${fmt(weekEnd)}`;
}

function getDateKey(dt) {
  const d = new Date(dt);
  return d.toISOString().split("T")[0];
}

function getWeekKey(dt) {
  const d = new Date(dt);
  const weekStart = new Date(d);
  weekStart.setDate(d.getDate() - d.getDay());
  return weekStart.toISOString().split("T")[0];
}

function TourCard({ tour, onStatusChange }) {
  const [updating, setUpdating] = useState(false);
  const status = STATUS_CONFIG[tour.status] || STATUS_CONFIG.unassigned;

  const handleStatus = async (newStatus) => {
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
      background: "#fff",
      border: `1px solid #e2e8f0`,
      borderLeft: `4px solid ${status.border}`,
      borderRadius: "8px",
      padding: "16px 20px",
      marginBottom: "10px",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
      transition: "box-shadow 0.2s",
      opacity: updating ? 0.6 : 1,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: "20px" }}>
        <div>
          <div style={{ fontSize: "13px", color: "#718096", fontFamily: "'DM Mono', monospace", letterSpacing: "0.05em" }}>
            {formatTime(tour.start_dt)} — {formatTime(tour.end_dt)}
          </div>
          <div style={{ fontSize: "16px", fontWeight: "600", color: "#1a202c", marginTop: "2px", fontFamily: "'Playfair Display', serif" }}>
            {tour.guest_name || "Guest"}
          </div>
          <div style={{ display: "flex", gap: "10px", marginTop: "6px", alignItems: "center" }}>
            <span style={{ fontSize: "12px", color: "#718096", background: "#f7fafc", border: "1px solid #e2e8f0", borderRadius: "4px", padding: "2px 8px" }}>
              {tour.number_of_guests} {tour.number_of_guests === 1 ? "guest" : "guests"}
            </span>
            {tour.group_tour && (
              <span style={{ fontSize: "12px", color: "#553c9a", background: "#faf5ff", border: "1px solid #d6bcfa", borderRadius: "4px", padding: "2px 8px" }}>
                Group Tour
              </span>
            )}
            <span style={{ fontSize: "12px", color: status.color, background: status.bg, border: `1px solid ${status.border}`, borderRadius: "4px", padding: "2px 8px", fontWeight: "500" }}>
              {status.label}
            </span>
          </div>
        </div>
      </div>

      <div style={{ display: "flex", gap: "6px" }}>
        {Object.entries(STATUS_CONFIG).map(([key, cfg]) => (
          <button
            key={key}
            onClick={() => handleStatus(key)}
            disabled={updating || tour.status === key}
            title={cfg.label}
            style={{
              width: "28px",
              height: "28px",
              borderRadius: "50%",
              border: tour.status === key ? `2px solid ${cfg.color}` : "2px solid transparent",
              background: cfg.border,
              cursor: tour.status === key ? "default" : "pointer",
              opacity: tour.status === key ? 1 : 0.45,
              transition: "opacity 0.15s, transform 0.15s",
              outline: "none",
              transform: tour.status === key ? "scale(1.15)" : "scale(1)",
            }}
          />
        ))}
      </div>
    </div>
  );
}

export default function App() {
  const [tours, setTours] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/tours/")
      .then((r) => r.json())
      .then((data) => { setTours(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const handleStatusChange = (id, newStatus) => {
    setTours((prev) => prev.map((t) => t.id === id ? { ...t, status: newStatus } : t));
  };

  // Group by week then by day
  const grouped = {};
  tours.forEach((tour) => {
    const wk = getWeekKey(tour.start_dt);
    const dk = getDateKey(tour.start_dt);
    if (!grouped[wk]) grouped[wk] = {};
    if (!grouped[wk][dk]) grouped[wk][dk] = [];
    grouped[wk][dk].push(tour);
  });

  const totalToday = tours.filter(t => getDateKey(t.start_dt) === getDateKey(new Date().toISOString())).length;
  const totalConfirmed = tours.filter(t => t.status === "confirmed").length;
  const totalUnassigned = tours.filter(t => t.status === "unassigned").length;

  return (
    <div style={{ display: "flex", minHeight: "100vh", fontFamily: "'DM Sans', sans-serif", background: "#f8fafc" }}>
      <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=Playfair+Display:wght@600;700&family=DM+Mono&display=swap" rel="stylesheet" />

      {/* Sidebar */}
      <div style={{
        width: "240px", minWidth: "240px", background: "#0f172a", color: "#e2e8f0",
        display: "flex", flexDirection: "column", padding: "32px 0",
      }}>
        <div style={{ padding: "0 24px 32px", borderBottom: "1px solid #1e293b" }}>
          <div style={{ fontSize: "11px", letterSpacing: "0.15em", color: "#64748b", textTransform: "uppercase", marginBottom: "6px" }}>
            EA Tours
          </div>
          <div style={{ fontSize: "22px", fontWeight: "700", fontFamily: "'Playfair Display', serif", color: "#f1f5f9" }}>
            Scheduler
          </div>
        </div>

        <nav style={{ padding: "24px 16px", flex: 1 }}>
          {[
            { label: "Tour Schedule", icon: "📅", active: true },
            { label: "AI Agent", icon: "🤖", active: false, soon: true },
          ].map((item) => (
            <div key={item.label} style={{
              display: "flex", alignItems: "center", gap: "10px",
              padding: "10px 12px", borderRadius: "6px", marginBottom: "4px",
              background: item.active ? "#1e293b" : "transparent",
              color: item.active ? "#f1f5f9" : "#64748b",
              cursor: item.soon ? "default" : "pointer",
              fontSize: "14px", fontWeight: "500",
            }}>
              <span>{item.icon}</span>
              {item.label}
              {item.soon && <span style={{ marginLeft: "auto", fontSize: "10px", color: "#475569", background: "#1e293b", padding: "2px 6px", borderRadius: "4px" }}>Soon</span>}
            </div>
          ))}
        </nav>

        {/* Status legend */}
        <div style={{ padding: "24px", borderTop: "1px solid #1e293b" }}>
          <div style={{ fontSize: "11px", letterSpacing: "0.1em", color: "#475569", textTransform: "uppercase", marginBottom: "12px" }}>
            Status
          </div>
          {Object.entries(STATUS_CONFIG).map(([key, cfg]) => (
            <div key={key} style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
              <div style={{ width: "10px", height: "10px", borderRadius: "50%", background: cfg.border }} />
              <span style={{ fontSize: "13px", color: "#94a3b8" }}>{cfg.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Main content */}
      <div style={{ flex: 1, padding: "40px 48px", overflowY: "auto" }}>
        <div style={{ maxWidth: "860px" }}>

          {/* Header */}
          <div style={{ marginBottom: "32px" }}>
            <h1 style={{ fontSize: "28px", fontWeight: "700", fontFamily: "'Playfair Display', serif", color: "#0f172a", margin: 0 }}>
              Tour Schedule
            </h1>
            <p style={{ color: "#64748b", marginTop: "4px", fontSize: "14px" }}>
              {new Date().toLocaleDateString("en-US", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}
            </p>
          </div>

          {/* Stats */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "16px", marginBottom: "40px" }}>
            {[
              { label: "Today's Tours", value: totalToday, color: "#3b82f6" },
              { label: "Confirmed", value: totalConfirmed, color: "#22c55e" },
              { label: "Needs Attention", value: totalUnassigned, color: "#ef4444" },
            ].map((stat) => (
              <div key={stat.label} style={{
                background: "#fff", border: "1px solid #e2e8f0", borderRadius: "10px",
                padding: "20px 24px", boxShadow: "0 1px 3px rgba(0,0,0,0.04)"
              }}>
                <div style={{ fontSize: "28px", fontWeight: "700", color: stat.color, fontFamily: "'Playfair Display', serif" }}>
                  {stat.value}
                </div>
                <div style={{ fontSize: "13px", color: "#64748b", marginTop: "2px" }}>{stat.label}</div>
              </div>
            ))}
          </div>

          {/* Tours */}
          {loading ? (
            <div style={{ color: "#94a3b8", fontSize: "15px" }}>Loading tours...</div>
          ) : Object.keys(grouped).length === 0 ? (
            <div style={{ color: "#94a3b8", fontSize: "15px" }}>No upcoming tours found.</div>
          ) : (
            Object.keys(grouped).sort().map((wk) => (
              <div key={wk} style={{ marginBottom: "40px" }}>
                <div style={{ fontSize: "11px", letterSpacing: "0.12em", textTransform: "uppercase", color: "#94a3b8", fontWeight: "600", marginBottom: "16px", paddingBottom: "8px", borderBottom: "1px solid #e2e8f0" }}>
                  {getWeekLabel(wk + "T12:00:00")}
                </div>
                {Object.keys(grouped[wk]).sort().map((dk) => (
                  <div key={dk} style={{ marginBottom: "24px" }}>
                    <div style={{ fontSize: "14px", fontWeight: "600", color: "#334155", marginBottom: "10px" }}>
                      {formatDayHeader(dk + "T12:00:00")}
                    </div>
                    {grouped[wk][dk].map((tour) => (
                      <TourCard key={tour.id} tour={tour} onStatusChange={handleStatusChange} />
                    ))}
                  </div>
                ))}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}