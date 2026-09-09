import React, { useState, useEffect, useRef } from "react";
import { useAuth } from "../../context/AuthContext";

interface Doubt {
  id: string;
  title: string;
  body: string;
  subject: string | null;
  student_name: string;
  student_id: string;
  status: "OPEN" | "ANSWERED" | "CLOSED";
  visibility: "CLASS" | "PRIVATE";
  reply_count: number;
  created_at: string;
  answered_by_name: string | null;
  class_id: string;
  attachment_name?: string | null;
  attachment_url?: string | null;
}

interface Reply {
  id: string;
  doubt_id: string;
  author_name: string;
  author_role: string;
  body: string;
  is_verified_answer: boolean;
  created_at: string;
  attachment_name?: string | null;
  attachment_url?: string | null;
}

interface ClassItem {
  id: string;
  name: string;
  grade: string;
  section: string;
}

const ENV_API_URL = import.meta.env.VITE_API_URL;
const RENDER_FALLBACK_URL = 'https://classpulse-api-yk80.onrender.com';
const isLocalhost = typeof window !== 'undefined' && 
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');
const API_BASE = (ENV_API_URL || (isLocalhost ? 'http://localhost:8000' : RENDER_FALLBACK_URL)) + '/api/v1';

const resolveImageUrl = (url: string | null | undefined): string => {
  if (!url) return "";
  if (url.startsWith("http://") || url.startsWith("https://") || url.startsWith("data:") || url.startsWith("blob:")) {
    return url;
  }
  const baseUrl = API_BASE.replace(/\/api\/v1\/?$/, "");
  return `${baseUrl}${url.startsWith("/") ? "" : "/"}${url}`;
};

const STATUS_COLORS: Record<string, { bg: string; color: string; label: string }> = {
  OPEN:     { bg: "#fef3c7", color: "#d97706", label: "Open" },
  ANSWERED: { bg: "#d1fae5", color: "#059669", label: "Answered" },
  CLOSED:   { bg: "#f1f5f9", color: "#64748b", label: "Closed" },
};

export const TeacherDoubtsPage: React.FC = () => {
  const { currentUser, token: authToken, schoolId } = useAuth();
  const [classes, setClasses] = useState<ClassItem[]>([]);
  const [selectedClass, setSelectedClass] = useState<string>("");
  const [doubts, setDoubts] = useState<Doubt[]>([]);
  const [selectedDoubt, setSelectedDoubt] = useState<Doubt | null>(null);
  const [replies, setReplies] = useState<Reply[]>([]);
  const [loading, setLoading] = useState(false);
  const [replyText, setReplyText] = useState("");
  const [filterStatus, setFilterStatus] = useState("ALL");
  const [submitting, setSubmitting] = useState(false);

  // Photo attachment state for teacher's reply
  const [replyFile, setReplyFile] = useState<File | null>(null);
  const [replyPreview, setReplyPreview] = useState<string | null>(null);
  const replyFileInputRef = useRef<HTMLInputElement | null>(null);

  // Lightbox modal state
  const [lightboxImage, setLightboxImage] = useState<{ url: string; title: string } | null>(null);

  const getEffectiveToken = (): string => {
    if (authToken) return authToken;
    const saved = localStorage.getItem("classpulse_demo_user");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (parsed.token) return parsed.token;
      } catch {}
    }
    return (currentUser as any)?._tokenResponse?.idToken || (currentUser as any)?.accessToken || "mock-teacher-token";
  };

  const getAuthHeaders = (includeJson = true) => {
    const h: Record<string, string> = {};
    if (includeJson) h["Content-Type"] = "application/json";
    const tok = getEffectiveToken();
    if (tok) h["Authorization"] = `Bearer ${tok}`;
    return h;
  };

  useEffect(() => {
    if (!schoolId) return;
    fetch(`${API_BASE}/classes?school_id=${schoolId}`, { headers: getAuthHeaders() })
      .then(r => r.json())
      .then(d => {
        const cls: ClassItem[] = (d.data || []).map((c: any) => ({
          id: c.id,
          name: c.name || `Class ${c.grade}-${c.section}`,
          grade: c.grade,
          section: c.section,
        }));
        setClasses(cls);
        if (cls.length > 0) setSelectedClass(cls[0].id);
      })
      .catch(console.error);
  }, [schoolId, currentUser, authToken]);

  useEffect(() => {
    if (!selectedClass) return;
    setLoading(true);
    let url = `${API_BASE}/doubts?class_id=${selectedClass}`;
    if (filterStatus !== "ALL") url += `&status=${filterStatus}`;
    fetch(url, { headers: getAuthHeaders() })
      .then(r => r.json())
      .then(d => {
        setDoubts(d.data || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [selectedClass, filterStatus, currentUser, authToken]);

  const fetchDoubtDetail = async (doubt: Doubt) => {
    setSelectedDoubt(doubt);
    try {
      const res = await fetch(`${API_BASE}/doubts/${doubt.id}`, { headers: getAuthHeaders() });
      if (res.ok) {
        const data = await res.json();
        setSelectedDoubt(data.data?.doubt || doubt);
        setReplies(data.data?.replies || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleReplyFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.type.startsWith("image/")) {
        alert("Please select a valid image file.");
        return;
      }
      setReplyFile(file);
      const reader = new FileReader();
      reader.onload = () => setReplyPreview(reader.result as string);
      reader.readAsDataURL(file);
    }
  };

  const removeReplyFile = () => {
    setReplyFile(null);
    setReplyPreview(null);
    if (replyFileInputRef.current) replyFileInputRef.current.value = "";
  };

  const uploadImageFile = async (file: File): Promise<{ url: string; filename: string } | null> => {
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch(`${API_BASE}/uploads/image`, {
        method: "POST",
        headers: getAuthHeaders(false),
        body: formData,
      });
      if (res.ok) {
        const data = await res.json();
        return {
          url: data.data?.url || "",
          filename: data.data?.filename || file.name,
        };
      }
      return null;
    } catch (err) {
      console.error("Upload error:", err);
      return null;
    }
  };

  const postReply = async () => {
    if (!selectedDoubt || (!replyText.trim() && !replyFile)) return;
    setSubmitting(true);
    try {
      let attachment_url: string | undefined;
      let attachment_name: string | undefined;

      if (replyFile) {
        const uploadRes = await uploadImageFile(replyFile);
        if (uploadRes) {
          attachment_url = uploadRes.url;
          attachment_name = uploadRes.filename;
        }
      }

      const res = await fetch(`${API_BASE}/doubts/${selectedDoubt.id}/replies`, {
        method: "POST",
        headers: getAuthHeaders(true),
        body: JSON.stringify({
          body: replyText.trim() || "See attached solution photo/diagram",
          attachment_name,
          attachment_url,
        }),
      });

      if (res.ok) {
        setReplyText("");
        removeReplyFile();
        await fetchDoubtDetail(selectedDoubt);
        const listRes = await fetch(`${API_BASE}/doubts?class_id=${selectedClass}`, { headers: getAuthHeaders() });
        if (listRes.ok) {
          const d = await listRes.json();
          setDoubts(d.data || []);
        }
      }
    } catch (e) {
      console.error(e);
    }
    setSubmitting(false);
  };

  const markAnswered = async (replyId: string) => {
    if (!selectedDoubt) return;
    const res = await fetch(`${API_BASE}/doubts/${selectedDoubt.id}/mark-answered?reply_id=${replyId}`, {
      method: "POST",
      headers: getAuthHeaders(),
    });
    if (res.ok) {
      const data = await res.json();
      setSelectedDoubt(data.data || selectedDoubt);
      await fetchDoubtDetail(selectedDoubt);
    }
  };

  const closeDoubt = async (doubtId: string) => {
    const res = await fetch(`${API_BASE}/doubts/${doubtId}/close`, { method: "POST", headers: getAuthHeaders() });
    if (res.ok) {
      if (selectedDoubt?.id === doubtId) {
        const data = await res.json();
        setSelectedDoubt(data.data || selectedDoubt);
      }
      const listRes = await fetch(`${API_BASE}/doubts?class_id=${selectedClass}`, { headers: getAuthHeaders() });
      if (listRes.ok) {
        const d = await listRes.json();
        setDoubts(d.data || []);
      }
    }
  };

  const deleteDoubt = async (doubtId: string) => {
    if (!window.confirm("Delete this doubt and all its replies?")) return;
    await fetch(`${API_BASE}/doubts/${doubtId}`, { method: "DELETE", headers: getAuthHeaders() });
    if (selectedDoubt?.id === doubtId) setSelectedDoubt(null);
    setDoubts(prev => prev.filter(d => d.id !== doubtId));
  };

  const openCount = doubts.filter(d => d.status === "OPEN").length;
  const answeredCount = doubts.filter(d => d.status === "ANSWERED").length;
  const filtered = doubts.filter(d => filterStatus === "ALL" || d.status === filterStatus);

  const formatDate = (iso: string) => {
    try {
      const d = new Date(iso);
      return d.toLocaleDateString("en-IN", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
    } catch {
      return iso;
    }
  };

  const statusBadge = (status: string) => {
    const c = STATUS_COLORS[status] || STATUS_COLORS.OPEN;
    return { background: c.bg, color: c.color, padding: "2px 10px", borderRadius: 20, fontSize: "0.72rem", fontWeight: 700 };
  };

  const btnStyle = (variant: "primary" | "secondary" | "danger") => ({
    padding: "7px 16px",
    borderRadius: 8,
    border: "none",
    cursor: "pointer",
    fontWeight: 600,
    fontSize: "0.8rem",
    background:
      variant === "primary"
        ? "linear-gradient(135deg, #6366f1, #a855f7)"
        : variant === "danger"
        ? "#fee2e2"
        : "#f1f5f9",
    color: variant === "primary" ? "white" : variant === "danger" ? "#dc2626" : "#374151",
  });

  return (
    <div style={{ fontFamily: "'Inter', sans-serif" }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: "1.6rem", fontWeight: 800, color: "#0f172a", margin: 0 }}>📚 Student Doubts</h1>
        <p style={{ color: "#64748b", marginTop: 4, fontSize: "0.9rem" }}>
          Review student questions, view textbook/problem photos, and provide verified answers
        </p>
      </div>

      {/* Stats */}
      <div style={{ display: "flex", gap: 16, marginBottom: 24, flexWrap: "wrap" }}>
        {[
          { val: doubts.length, label: "Total Doubts", color: "#6366f1" },
          { val: openCount, label: "Pending Answer", color: "#f59e0b" },
          { val: answeredCount, label: "Answered", color: "#10b981" },
          {
            val: doubts.length > 0 ? Math.round((answeredCount / doubts.length) * 100) + "%" : "0%",
            label: "Answer Rate",
            color: "#0891b2",
          },
        ].map(s => (
          <div
            key={s.label}
            style={{
              background: "white",
              borderRadius: 12,
              padding: "16px 24px",
              border: "1px solid #e2e8f0",
              flex: "1 1 120px",
              borderLeft: `4px solid ${s.color}`,
            }}
          >
            <div style={{ fontSize: "1.6rem", fontWeight: 800, color: "#0f172a" }}>{s.val}</div>
            <div style={{ color: "#64748b", fontSize: "0.8rem" }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Toolbar */}
      <div style={{ display: "flex", gap: 12, marginBottom: 20, flexWrap: "wrap", alignItems: "center" }}>
        <select
          style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid #e2e8f0", fontSize: "0.875rem", background: "white" }}
          value={selectedClass}
          onChange={e => {
            setSelectedClass(e.target.value);
            setSelectedDoubt(null);
          }}
        >
          {classes.map(c => (
            <option key={c.id} value={c.id}>
              {c.name || `Class ${c.grade}-${c.section}`}
            </option>
          ))}
        </select>
        <select
          style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid #e2e8f0", fontSize: "0.875rem", background: "white" }}
          value={filterStatus}
          onChange={e => setFilterStatus(e.target.value)}
        >
          <option value="ALL">All Status</option>
          <option value="OPEN">Open</option>
          <option value="ANSWERED">Answered</option>
          <option value="CLOSED">Closed</option>
        </select>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: selectedDoubt ? "1fr 1.5fr" : "1fr", gap: 24 }}>
        {/* List */}
        <div>
          {loading && <div style={{ textAlign: "center", padding: 32, color: "#94a3b8" }}>Loading doubts...</div>}
          {!loading && filtered.length === 0 && (
            <div style={{ textAlign: "center", padding: 40, color: "#94a3b8" }}>No doubts found for this class.</div>
          )}
          {filtered.map(d => (
            <div
              key={d.id}
              onClick={() => fetchDoubtDetail(d)}
              style={{
                background: "white",
                borderRadius: 12,
                padding: "14px 18px",
                marginBottom: 10,
                border: selectedDoubt?.id === d.id ? "2px solid #6366f1" : "1px solid #e2e8f0",
                cursor: "pointer",
                transition: "all 0.2s",
                boxShadow: selectedDoubt?.id === d.id ? "0 4px 14px rgba(99,102,241,0.15)" : "none",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", gap: 8, marginBottom: 6 }}>
                <div style={{ fontWeight: 700, color: "#0f172a", fontSize: "0.95rem" }}>{d.title}</div>
                <span style={statusBadge(d.status)}>{STATUS_COLORS[d.status]?.label}</span>
              </div>
              <div
                style={{
                  color: "#475569",
                  fontSize: "0.83rem",
                  marginBottom: 8,
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                }}
              >
                {d.body}
              </div>
              <div style={{ display: "flex", gap: 12, fontSize: "0.75rem", color: "#94a3b8", alignItems: "center", flexWrap: "wrap" }}>
                {d.subject && <span>📖 {d.subject}</span>}
                {d.attachment_url && (
                  <span
                    style={{
                      background: "#ede9fe",
                      color: "#6d28d9",
                      padding: "2px 8px",
                      borderRadius: 12,
                      fontWeight: 600,
                      display: "inline-flex",
                      alignItems: "center",
                      gap: 4,
                    }}
                  >
                    📷 Photo
                  </span>
                )}
                <span>👤 {d.student_name}</span>
                <span>💬 {d.reply_count}</span>
                <span style={{ marginLeft: "auto" }}>{formatDate(d.created_at)}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Detail panel */}
        {selectedDoubt && (
          <div style={{ background: "white", borderRadius: 12, border: "1px solid #e2e8f0", padding: 24 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
              <div>
                <div style={{ fontWeight: 800, fontSize: "1.1rem", color: "#0f172a", marginBottom: 6 }}>
                  {selectedDoubt.title}
                </div>
                <span style={statusBadge(selectedDoubt.status)}>{STATUS_COLORS[selectedDoubt.status]?.label}</span>
              </div>
              <button
                onClick={() => setSelectedDoubt(null)}
                style={{ background: "none", border: "none", cursor: "pointer", color: "#94a3b8", fontSize: "1.1rem" }}
              >
                ✕
              </button>
            </div>

            <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
              {selectedDoubt.status !== "CLOSED" && (
                <button style={btnStyle("secondary")} onClick={() => closeDoubt(selectedDoubt.id)}>
                  Close Doubt
                </button>
              )}
              <button style={btnStyle("danger")} onClick={() => deleteDoubt(selectedDoubt.id)}>
                Delete
              </button>
            </div>

            {selectedDoubt.subject && (
              <div
                style={{
                  background: "#f0f9ff",
                  borderRadius: 8,
                  padding: "8px 14px",
                  marginBottom: 12,
                  fontSize: "0.85rem",
                  color: "#0369a1",
                }}
              >
                📖 {selectedDoubt.subject}
              </div>
            )}

            <div
              style={{
                background: "#f8fafc",
                borderRadius: 8,
                padding: "12px 16px",
                marginBottom: 16,
                fontSize: "0.875rem",
                color: "#374151",
                lineHeight: 1.6,
              }}
            >
              {selectedDoubt.body}
            </div>

            {/* Attached Photo from Student */}
            {selectedDoubt.attachment_url && (
              <div
                style={{
                  marginBottom: 20,
                  background: "#fdf4ff",
                  border: "1px solid #f0abfc",
                  borderRadius: 12,
                  padding: 14,
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: 10,
                    fontSize: "0.82rem",
                    fontWeight: 700,
                    color: "#86198f",
                  }}
                >
                  <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    📷 Student Question Photo: {selectedDoubt.attachment_name || "Attachment"}
                  </span>
                  <span style={{ color: "#a21caf", fontSize: "0.75rem", cursor: "pointer" }}>
                    🔍 Click photo to enlarge
                  </span>
                </div>
                <div
                  onClick={() =>
                    setLightboxImage({
                      url: resolveImageUrl(selectedDoubt.attachment_url),
                      title: `${selectedDoubt.student_name}'s question: ${selectedDoubt.title}`,
                    })
                  }
                  style={{
                    cursor: "pointer",
                    borderRadius: 8,
                    overflow: "hidden",
                    border: "1px solid #fae8ff",
                    background: "#00000008",
                    display: "flex",
                    justifyContent: "center",
                    alignItems: "center",
                    maxHeight: 280,
                  }}
                >
                  <img
                    src={resolveImageUrl(selectedDoubt.attachment_url)}
                    alt={selectedDoubt.attachment_name || "Question photo"}
                    style={{
                      maxWidth: "100%",
                      maxHeight: 280,
                      objectFit: "contain",
                      transition: "transform 0.2s ease",
                    }}
                    onMouseEnter={e => (e.currentTarget.style.transform = "scale(1.02)")}
                    onMouseLeave={e => (e.currentTarget.style.transform = "scale(1)")}
                  />
                </div>
              </div>
            )}

            <div style={{ fontWeight: 700, marginBottom: 12, color: "#0f172a" }}>
              Replies ({replies.length})
            </div>

            {replies.map(r => (
              <div
                key={r.id}
                style={{
                  background: r.is_verified_answer ? "#f0fdf4" : "#f8fafc",
                  border: r.is_verified_answer ? "1px solid #86efac" : "1px solid #e2e8f0",
                  borderRadius: 10,
                  padding: "12px 16px",
                  marginBottom: 12,
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                  <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                    <span
                      style={{
                        fontWeight: 700,
                        fontSize: "0.85rem",
                        color: r.author_role === "TEACHER" ? "#7c3aed" : "#0f172a",
                      }}
                    >
                      {r.author_name}
                    </span>
                    <span
                      style={{
                        fontSize: "0.7rem",
                        background: r.author_role === "TEACHER" ? "#ede9fe" : "#f1f5f9",
                        color: r.author_role === "TEACHER" ? "#7c3aed" : "#64748b",
                        padding: "1px 8px",
                        borderRadius: 20,
                        fontWeight: 600,
                      }}
                    >
                      {r.author_role}
                    </span>
                    {r.is_verified_answer && (
                      <span
                        style={{
                          fontSize: "0.7rem",
                          background: "#dcfce7",
                          color: "#059669",
                          padding: "1px 8px",
                          borderRadius: 20,
                          fontWeight: 700,
                        }}
                      >
                        ✓ Verified Answer
                      </span>
                    )}
                  </div>
                  {!r.is_verified_answer && selectedDoubt.status !== "CLOSED" && (
                    <button style={btnStyle("primary")} onClick={() => markAnswered(r.id)}>
                      ✓ Mark as Answer
                    </button>
                  )}
                </div>
                <div style={{ fontSize: "0.875rem", color: "#374151", lineHeight: 1.6 }}>{r.body}</div>

                {/* Reply Attached Photo */}
                {r.attachment_url && (
                  <div style={{ marginTop: 10 }}>
                    <div
                      onClick={() =>
                        setLightboxImage({
                          url: resolveImageUrl(r.attachment_url),
                          title: `Solution by ${r.author_name}`,
                        })
                      }
                      style={{
                        display: "inline-block",
                        cursor: "pointer",
                        borderRadius: 6,
                        overflow: "hidden",
                        border: "1px solid #cbd5e1",
                        maxHeight: 180,
                      }}
                    >
                      <img
                        src={resolveImageUrl(r.attachment_url)}
                        alt={r.attachment_name || "Solution photo"}
                        style={{
                          maxHeight: 160,
                          maxWidth: 280,
                          objectFit: "contain",
                          display: "block",
                        }}
                      />
                    </div>
                  </div>
                )}
              </div>
            ))}

            {/* Reply input for Teacher */}
            {selectedDoubt.status !== "CLOSED" && (
              <div style={{ marginTop: 16, borderTop: "1px solid #e2e8f0", paddingTop: 16 }}>
                <textarea
                  style={{
                    width: "100%",
                    padding: "10px 14px",
                    borderRadius: 8,
                    border: "1px solid #e2e8f0",
                    fontSize: "0.875rem",
                    boxSizing: "border-box",
                    resize: "vertical",
                    minHeight: 90,
                  }}
                  placeholder="Write your explanation or step-by-step answer..."
                  value={replyText}
                  onChange={e => setReplyText(e.target.value)}
                  rows={4}
                />

                {/* Reply photo attachment preview */}
                {replyPreview && (
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 10,
                      marginTop: 8,
                      background: "#f1f5f9",
                      padding: "6px 12px",
                      borderRadius: 8,
                      width: "fit-content",
                    }}
                  >
                    <img
                      src={replyPreview}
                      alt="Solution preview"
                      style={{ width: 36, height: 36, objectFit: "cover", borderRadius: 4 }}
                    />
                    <span style={{ fontSize: "0.8rem", color: "#334155" }}>{replyFile?.name}</span>
                    <button
                      onClick={removeReplyFile}
                      style={{
                        background: "none",
                        border: "none",
                        color: "#ef4444",
                        cursor: "pointer",
                        fontWeight: 700,
                      }}
                    >
                      ✕
                    </button>
                  </div>
                )}

                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginTop: 10,
                  }}
                >
                  <div>
                    <input
                      ref={replyFileInputRef}
                      type="file"
                      accept="image/*"
                      style={{ display: "none" }}
                      onChange={handleReplyFileChange}
                    />
                    <button
                      type="button"
                      onClick={() => replyFileInputRef.current?.click()}
                      style={{
                        background: "#ede9fe",
                        color: "#6d28d9",
                        border: "1px solid #ddd6fe",
                        borderRadius: 6,
                        padding: "6px 12px",
                        fontSize: "0.8rem",
                        fontWeight: 600,
                        cursor: "pointer",
                        display: "inline-flex",
                        alignItems: "center",
                        gap: 6,
                      }}
                    >
                      📷 {replyFile ? "Change Solution Photo" : "Attach Solution Diagram / Photo"}
                    </button>
                  </div>

                  <button
                    style={btnStyle("primary")}
                    onClick={postReply}
                    disabled={submitting || (!replyText.trim() && !replyFile)}
                  >
                    {submitting ? "Posting..." : "Post Reply"}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Lightbox Modal */}
      {lightboxImage && (
        <div
          onClick={() => setLightboxImage(null)}
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(15, 23, 42, 0.9)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 999,
            padding: 24,
            cursor: "zoom-out",
            backdropFilter: "blur(4px)",
          }}
        >
          <div
            onClick={e => e.stopPropagation()}
            style={{
              position: "relative",
              maxWidth: "92vw",
              maxHeight: "90vh",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              cursor: "default",
            }}
          >
            <button
              onClick={() => setLightboxImage(null)}
              style={{
                position: "absolute",
                top: -40,
                right: 0,
                background: "rgba(255,255,255,0.2)",
                color: "white",
                border: "none",
                borderRadius: "50%",
                width: 36,
                height: 36,
                fontSize: "1.2rem",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              ✕
            </button>
            <img
              src={lightboxImage.url}
              alt={lightboxImage.title}
              style={{
                maxWidth: "100%",
                maxHeight: "82vh",
                objectFit: "contain",
                borderRadius: 8,
                boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.5)",
              }}
            />
            <div
              style={{
                marginTop: 12,
                color: "white",
                fontSize: "0.9rem",
                fontWeight: 600,
                textAlign: "center",
                display: "flex",
                gap: 16,
                alignItems: "center",
              }}
            >
              <span>{lightboxImage.title}</span>
              <a
                href={lightboxImage.url}
                target="_blank"
                rel="noreferrer"
                style={{ color: "#38bdf8", textDecoration: "none", fontSize: "0.8rem" }}
              >
                ↗ Open original
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TeacherDoubtsPage;
