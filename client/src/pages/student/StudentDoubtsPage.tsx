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
  attachment_name?: string | null;
  attachment_url?: string | null;
}

interface Reply {
  id: string;
  author_name: string;
  author_role: string;
  body: string;
  is_verified_answer: boolean;
  created_at: string;
  attachment_name?: string | null;
  attachment_url?: string | null;
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

const SUBJECTS = ["All Subjects", "Mathematics", "Physics", "Chemistry", "Biology", "English", "History", "Geography", "Computer Science"];

export const StudentDoubtsPage: React.FC = () => {
  const { currentUser, token: authToken } = useAuth();
  const [classDoubts, setClassDoubts] = useState<Doubt[]>([]);
  const [myDoubts, setMyDoubts] = useState<Doubt[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"class" | "mine">("class");
  const [selectedDoubt, setSelectedDoubt] = useState<Doubt | null>(null);
  const [replies, setReplies] = useState<Reply[]>([]);
  const [showNewDoubt, setShowNewDoubt] = useState(false);
  const [replyText, setReplyText] = useState("");
  const [filterSubject, setFilterSubject] = useState("All Subjects");
  const [filterStatus, setFilterStatus] = useState("ALL");

  // New doubt modal fields
  const [newTitle, setNewTitle] = useState("");
  const [newBody, setNewBody] = useState("");
  const [newSubject, setNewSubject] = useState("Mathematics");
  const [newVisibility, setNewVisibility] = useState<"CLASS" | "PRIVATE">("CLASS");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [filePreview, setFilePreview] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Reply photo fields
  const [replyFile, setReplyFile] = useState<File | null>(null);
  const [replyPreview, setReplyPreview] = useState<string | null>(null);
  const [submittingReply, setSubmittingReply] = useState(false);
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
    return (currentUser as any)?._tokenResponse?.idToken || (currentUser as any)?.accessToken || "mock-student-token";
  };

  const getAuthHeaders = (includeJson = true) => {
    const h: Record<string, string> = {};
    if (includeJson) h["Content-Type"] = "application/json";
    const tok = getEffectiveToken();
    if (tok) h["Authorization"] = `Bearer ${tok}`;
    return h;
  };

  const fetchDoubts = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/student/doubts`, { headers: getAuthHeaders() });
      if (res.ok) {
        const data = await res.json();
        setClassDoubts(data.data?.class_doubts || []);
        setMyDoubts(data.data?.my_doubts || []);
      } else {
        console.warn("fetchDoubts failed with status:", res.status);
      }
    } catch (e) {
      console.error("fetchDoubts error:", e);
    }
    setLoading(false);
  };

  const fetchDoubtDetail = async (doubt: Doubt) => {
    setSelectedDoubt(doubt);
    try {
      const res = await fetch(`${API_BASE}/student/doubts/${doubt.id}`, { headers: getAuthHeaders() });
      if (res.ok) {
        const data = await res.json();
        setSelectedDoubt(data.data?.doubt || doubt);
        setReplies(data.data?.replies || []);
      }
    } catch (e) {
      console.error("fetchDoubtDetail error:", e);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.type.startsWith("image/")) {
        setUploadError("Please select a valid image file (PNG, JPG, WebP, GIF).");
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        setUploadError("Image size must be less than 10MB.");
        return;
      }
      setUploadError(null);
      setSelectedFile(file);
      const reader = new FileReader();
      reader.onload = () => setFilePreview(reader.result as string);
      reader.readAsDataURL(file);
    }
  };

  const removeSelectedFile = () => {
    setSelectedFile(null);
    setFilePreview(null);
    setUploadError(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
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
      } else {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error?.message || err.detail?.message || "Failed to upload image");
      }
    } catch (err: any) {
      console.error("Upload error:", err);
      setUploadError(err.message || "Failed to upload image.");
      return null;
    }
  };

  const postDoubt = async () => {
    if (!newTitle.trim() || !newBody.trim()) return;
    setSubmitting(true);
    setUploadError(null);
    try {
      let attachment_url: string | undefined;
      let attachment_name: string | undefined;

      if (selectedFile) {
        const uploadRes = await uploadImageFile(selectedFile);
        if (!uploadRes) {
          setSubmitting(false);
          return;
        }
        attachment_url = uploadRes.url;
        attachment_name = uploadRes.filename;
      }

      const userClassId =
        localStorage.getItem("classpulse_class_id") ||
        (currentUser as any)?.class_id ||
        "class-10a";

      const res = await fetch(`${API_BASE}/student/doubts`, {
        method: "POST",
        headers: getAuthHeaders(true),
        body: JSON.stringify({
          class_id: userClassId,
          title: newTitle.trim(),
          body: newBody.trim(),
          subject: newSubject,
          visibility: newVisibility,
          attachment_name,
          attachment_url,
        }),
      });

      if (res.ok) {
        setNewTitle("");
        setNewBody("");
        removeSelectedFile();
        setShowNewDoubt(false);
        await fetchDoubts();
      } else {
        const err = await res.json().catch(() => ({}));
        const errMsg =
          err.error?.message ||
          err.detail?.message ||
          (typeof err.detail === "string" ? err.detail : "") ||
          `Failed to post doubt (${res.status} ${res.statusText})`;
        setUploadError(errMsg);
      }
    } catch (e: any) {
      console.error("postDoubt error:", e);
      setUploadError(e.message || "Error posting doubt.");
    }
    setSubmitting(false);
  };

  const postReply = async () => {
    if (!selectedDoubt || (!replyText.trim() && !replyFile)) return;
    setSubmittingReply(true);
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

      const res = await fetch(`${API_BASE}/student/doubts/${selectedDoubt.id}/replies`, {
        method: "POST",
        headers: getAuthHeaders(true),
        body: JSON.stringify({
          body: replyText.trim() || "See attached photo",
          attachment_name,
          attachment_url,
        }),
      });

      if (res.ok) {
        setReplyText("");
        removeReplyFile();
        await fetchDoubtDetail(selectedDoubt);
      }
    } catch (e) {
      console.error(e);
    }
    setSubmittingReply(false);
  };

  useEffect(() => {
    fetchDoubts();
  }, [currentUser, authToken]);

  const displayList = activeTab === "class" ? classDoubts : myDoubts;
  const filtered = displayList.filter(d => {
    const matchSub = filterSubject === "All Subjects" || d.subject === filterSubject;
    const matchStatus = filterStatus === "ALL" || d.status === filterStatus;
    return matchSub && matchStatus;
  });

  const openCount = classDoubts.filter(d => d.status === "OPEN").length;
  const answeredCount = classDoubts.filter(d => d.status === "ANSWERED").length;

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

  const tabStyle = (active: boolean) => ({
    padding: "8px 20px",
    borderRadius: 8,
    border: "none",
    cursor: "pointer",
    fontWeight: 600,
    fontSize: "0.875rem",
    background: active ? "linear-gradient(135deg, #0891b2, #06b6d4)" : "#f1f5f9",
    color: active ? "white" : "#64748b",
  });

  const btnStyle = (variant: "primary" | "secondary") => ({
    padding: "8px 20px",
    borderRadius: 8,
    border: "none",
    cursor: "pointer",
    fontWeight: 600,
    fontSize: "0.875rem",
    background: variant === "primary" ? "linear-gradient(135deg, #0891b2, #06b6d4)" : "#f1f5f9",
    color: variant === "primary" ? "white" : "#374151",
  });

  return (
    <div style={{ fontFamily: "'Inter', sans-serif" }}>
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: "1.6rem", fontWeight: 800, color: "#0c4a6e", margin: 0 }}>📚 Academic Doubts</h1>
        <p style={{ color: "#64748b", marginTop: 4, fontSize: "0.9rem" }}>
          Ask questions, attach textbook/handwritten photos, and learn from teacher explanations
        </p>
      </div>

      {/* Stats */}
      <div style={{ display: "flex", gap: 16, marginBottom: 24, flexWrap: "wrap" }}>
        {[
          { val: classDoubts.length, label: "Class Doubts", color: "#0891b2" },
          { val: openCount, label: "Open", color: "#f59e0b" },
          { val: answeredCount, label: "Answered", color: "#10b981" },
          { val: myDoubts.length, label: "My Doubts", color: "#6366f1" },
        ].map(s => (
          <div
            key={s.label}
            style={{
              background: "white",
              borderRadius: 12,
              padding: "16px 24px",
              border: "1px solid #bae6fd",
              flex: "1 1 120px",
              borderLeft: `4px solid ${s.color}`,
            }}
          >
            <div style={{ fontSize: "1.6rem", fontWeight: 800, color: "#0c4a6e" }}>{s.val}</div>
            <div style={{ color: "#64748b", fontSize: "0.8rem" }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Toolbar */}
      <div style={{ display: "flex", gap: 12, marginBottom: 20, flexWrap: "wrap", alignItems: "center" }}>
        <button style={tabStyle(activeTab === "class")} onClick={() => setActiveTab("class")}>
          Class Doubts
        </button>
        <button style={tabStyle(activeTab === "mine")} onClick={() => setActiveTab("mine")}>
          My Doubts
        </button>
        <select
          style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid #bae6fd", fontSize: "0.875rem", background: "white" }}
          value={filterSubject}
          onChange={e => setFilterSubject(e.target.value)}
        >
          {SUBJECTS.map(s => <option key={s}>{s}</option>)}
        </select>
        <select
          style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid #bae6fd", fontSize: "0.875rem", background: "white" }}
          value={filterStatus}
          onChange={e => setFilterStatus(e.target.value)}
        >
          <option value="ALL">All Status</option>
          <option value="OPEN">Open</option>
          <option value="ANSWERED">Answered</option>
          <option value="CLOSED">Closed</option>
        </select>
        <button
          style={{ ...btnStyle("primary"), marginLeft: "auto" }}
          onClick={() => {
            setShowNewDoubt(true);
            setUploadError(null);
          }}
        >
          + Ask a Doubt
        </button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: selectedDoubt ? "1fr 1.4fr" : "1fr", gap: 24 }}>
        {/* List */}
        <div>
          {loading && <div style={{ textAlign: "center", padding: 40, color: "#94a3b8" }}>Loading doubts...</div>}
          {!loading && filtered.length === 0 && (
            <div style={{ textAlign: "center", padding: 40, color: "#94a3b8" }}>
              {activeTab === "mine"
                ? "You haven't asked any doubts yet. Click 'Ask a Doubt' to get started!"
                : "No doubts in your class yet."}
            </div>
          )}
          {filtered.map(doubt => (
            <div
              key={doubt.id}
              onClick={() => fetchDoubtDetail(doubt)}
              style={{
                background: "white",
                borderRadius: 12,
                padding: "16px 20px",
                marginBottom: 12,
                border: selectedDoubt?.id === doubt.id ? "2px solid #0891b2" : "1px solid #e0f2fe",
                cursor: "pointer",
                transition: "all 0.2s",
                boxShadow: selectedDoubt?.id === doubt.id ? "0 4px 16px rgba(8,145,178,0.15)" : "none",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", gap: 8, marginBottom: 8 }}>
                <div style={{ fontWeight: 700, color: "#0c4a6e", fontSize: "0.95rem" }}>{doubt.title}</div>
                <span style={statusBadge(doubt.status)}>{STATUS_COLORS[doubt.status]?.label}</span>
              </div>
              <div
                style={{
                  color: "#475569",
                  fontSize: "0.83rem",
                  marginBottom: 8,
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
              >
                {doubt.body}
              </div>

              <div style={{ display: "flex", gap: 12, fontSize: "0.75rem", color: "#94a3b8", alignItems: "center", flexWrap: "wrap" }}>
                {doubt.subject && <span>📖 {doubt.subject}</span>}
                {doubt.attachment_url && (
                  <span
                    style={{
                      background: "#e0f2fe",
                      color: "#0284c7",
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
                <span>👤 {doubt.student_name}</span>
                <span>💬 {doubt.reply_count} replies</span>
                <span style={{ marginLeft: "auto" }}>{formatDate(doubt.created_at)}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Detail panel */}
        {selectedDoubt && (
          <div style={{ background: "white", borderRadius: 12, border: "1px solid #e0f2fe", padding: 24 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
              <div>
                <div style={{ fontWeight: 800, fontSize: "1.1rem", color: "#0c4a6e", marginBottom: 4 }}>
                  {selectedDoubt.title}
                </div>
                <span style={statusBadge(selectedDoubt.status)}>{STATUS_COLORS[selectedDoubt.status]?.label}</span>
              </div>
              <button
                onClick={() => setSelectedDoubt(null)}
                style={{ background: "none", border: "none", cursor: "pointer", color: "#94a3b8", fontSize: "1.2rem" }}
              >
                ✕
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
                📖 Subject: <strong>{selectedDoubt.subject}</strong>
              </div>
            )}

            <div
              style={{
                background: "#f8fafc",
                borderRadius: 8,
                padding: "14px 16px",
                marginBottom: 16,
                fontSize: "0.875rem",
                color: "#374151",
                lineHeight: 1.6,
              }}
            >
              {selectedDoubt.body}
            </div>

            {/* Attached Photo Display */}
            {selectedDoubt.attachment_url && (
              <div
                style={{
                  marginBottom: 20,
                  background: "#f0fdfa",
                  border: "1px solid #99f6e4",
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
                    color: "#0f766e",
                  }}
                >
                  <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    📷 Attached Photo / Diagram: {selectedDoubt.attachment_name || "Attachment"}
                  </span>
                  <span style={{ color: "#0d9488", fontSize: "0.75rem", cursor: "pointer" }}>
                    🔍 Click photo to enlarge
                  </span>
                </div>
                <div
                  onClick={() =>
                    setLightboxImage({
                      url: resolveImageUrl(selectedDoubt.attachment_url),
                      title: selectedDoubt.title,
                    })
                  }
                  style={{
                    cursor: "pointer",
                    borderRadius: 8,
                    overflow: "hidden",
                    border: "1px solid #ccfbf1",
                    background: "#0000000a",
                    display: "flex",
                    justifyContent: "center",
                    alignItems: "center",
                    maxHeight: 260,
                  }}
                >
                  <img
                    src={resolveImageUrl(selectedDoubt.attachment_url)}
                    alt={selectedDoubt.attachment_name || "Doubt photo"}
                    style={{
                      maxWidth: "100%",
                      maxHeight: 260,
                      objectFit: "contain",
                      transition: "transform 0.2s ease",
                    }}
                    onMouseEnter={e => (e.currentTarget.style.transform = "scale(1.02)")}
                    onMouseLeave={e => (e.currentTarget.style.transform = "scale(1)")}
                  />
                </div>
              </div>
            )}

            <div style={{ fontWeight: 700, marginBottom: 12, color: "#0c4a6e" }}>
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
                  <span style={{ fontSize: "0.72rem", color: "#94a3b8" }}>{formatDate(r.created_at)}</span>
                </div>
                <div style={{ fontSize: "0.875rem", color: "#374151", lineHeight: 1.6 }}>{r.body}</div>

                {/* Reply Attached Photo */}
                {r.attachment_url && (
                  <div style={{ marginTop: 10 }}>
                    <div
                      onClick={() =>
                        setLightboxImage({
                          url: resolveImageUrl(r.attachment_url),
                          title: `Reply by ${r.author_name}`,
                        })
                      }
                      style={{
                        display: "inline-block",
                        cursor: "pointer",
                        borderRadius: 6,
                        overflow: "hidden",
                        border: "1px solid #cbd5e1",
                        maxHeight: 160,
                      }}
                    >
                      <img
                        src={resolveImageUrl(r.attachment_url)}
                        alt={r.attachment_name || "Reply photo"}
                        style={{
                          maxHeight: 150,
                          maxWidth: 240,
                          objectFit: "contain",
                          display: "block",
                        }}
                      />
                    </div>
                  </div>
                )}
              </div>
            ))}

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
                    minHeight: 80,
                  }}
                  placeholder="Add a reply or follow-up question..."
                  value={replyText}
                  onChange={e => setReplyText(e.target.value)}
                  rows={3}
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
                      alt="Preview"
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
                        background: "#e0f2fe",
                        color: "#0369a1",
                        border: "1px solid #bae6fd",
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
                      📷 {replyFile ? "Change Photo" : "Attach Photo"}
                    </button>
                  </div>

                  <button
                    style={btnStyle("primary")}
                    onClick={postReply}
                    disabled={submittingReply || (!replyText.trim() && !replyFile)}
                  >
                    {submittingReply ? "Posting..." : "Post Reply"}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* New Doubt Modal */}
      {showNewDoubt && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 200,
            backdropFilter: "blur(2px)",
          }}
        >
          <div
            style={{
              background: "white",
              borderRadius: 16,
              padding: 28,
              width: "92%",
              maxWidth: 580,
              maxHeight: "90vh",
              overflowY: "auto",
              boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
            }}
          >
            <div style={{ fontWeight: 800, fontSize: "1.2rem", marginBottom: 20, color: "#0c4a6e" }}>
              Ask a New Doubt
            </div>

            {uploadError && (
              <div
                style={{
                  background: "#fef2f2",
                  color: "#b91c1c",
                  border: "1px solid #fecaca",
                  borderRadius: 8,
                  padding: "10px 14px",
                  marginBottom: 16,
                  fontSize: "0.85rem",
                }}
              >
                {uploadError}
              </div>
            )}

            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", fontWeight: 600, marginBottom: 6, color: "#374151", fontSize: "0.85rem" }}>
                Subject
              </label>
              <select
                style={{
                  width: "100%",
                  padding: "10px 14px",
                  borderRadius: 8,
                  border: "1px solid #e2e8f0",
                  fontSize: "0.875rem",
                }}
                value={newSubject}
                onChange={e => setNewSubject(e.target.value)}
              >
                {SUBJECTS.slice(1).map(s => <option key={s}>{s}</option>)}
              </select>
            </div>

            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", fontWeight: 600, marginBottom: 6, color: "#374151", fontSize: "0.85rem" }}>
                Question Title
              </label>
              <input
                style={{
                  width: "100%",
                  padding: "10px 14px",
                  borderRadius: 8,
                  border: "1px solid #e2e8f0",
                  fontSize: "0.875rem",
                  boxSizing: "border-box",
                }}
                placeholder="Write a clear, concise title for your doubt..."
                value={newTitle}
                onChange={e => setNewTitle(e.target.value)}
              />
            </div>

            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", fontWeight: 600, marginBottom: 6, color: "#374151", fontSize: "0.85rem" }}>
                Detailed Description
              </label>
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
                placeholder="Explain what part you're stuck on. Context and details help get faster answers!"
                value={newBody}
                onChange={e => setNewBody(e.target.value)}
                rows={4}
              />
            </div>

            {/* Photo / Image Attachment Section */}
            <div style={{ marginBottom: 20 }}>
              <label style={{ display: "block", fontWeight: 600, marginBottom: 6, color: "#374151", fontSize: "0.85rem" }}>
                Attach Photo / Diagram (Optional)
              </label>

              <input
                ref={fileInputRef}
                type="file"
                accept="image/png,image/jpeg,image/webp,image/gif"
                style={{ display: "none" }}
                onChange={handleFileChange}
              />

              {!filePreview ? (
                <div
                  onClick={() => fileInputRef.current?.click()}
                  style={{
                    border: "2px dashed #0284c7",
                    borderRadius: 10,
                    padding: "18px",
                    textAlign: "center",
                    cursor: "pointer",
                    background: "#f0f9ff",
                    transition: "background 0.2s",
                  }}
                  onMouseEnter={e => (e.currentTarget.style.background = "#e0f2fe")}
                  onMouseLeave={e => (e.currentTarget.style.background = "#f0f9ff")}
                >
                  <div style={{ fontSize: "1.8rem", marginBottom: 4 }}>📷</div>
                  <div style={{ fontWeight: 600, color: "#0284c7", fontSize: "0.9rem" }}>
                    Click to attach a photo or diagram
                  </div>
                  <div style={{ color: "#64748b", fontSize: "0.75rem", marginTop: 2 }}>
                    Supports PNG, JPG, WebP, GIF up to 10MB
                  </div>
                </div>
              ) : (
                <div
                  style={{
                    border: "1px solid #bae6fd",
                    borderRadius: 10,
                    padding: 12,
                    background: "#f8fafc",
                    display: "flex",
                    alignItems: "center",
                    gap: 14,
                  }}
                >
                  <img
                    src={filePreview}
                    alt="Selected attachment preview"
                    style={{
                      width: 64,
                      height: 64,
                      objectFit: "cover",
                      borderRadius: 8,
                      border: "1px solid #e2e8f0",
                    }}
                  />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div
                      style={{
                        fontWeight: 600,
                        fontSize: "0.85rem",
                        color: "#0f172a",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {selectedFile?.name}
                    </div>
                    <div style={{ fontSize: "0.75rem", color: "#64748b", marginTop: 2 }}>
                      {selectedFile ? `${(selectedFile.size / 1024).toFixed(1)} KB` : ""}
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={removeSelectedFile}
                    style={{
                      background: "#fee2e2",
                      color: "#dc2626",
                      border: "none",
                      borderRadius: 6,
                      padding: "6px 12px",
                      fontSize: "0.8rem",
                      fontWeight: 600,
                      cursor: "pointer",
                    }}
                  >
                    ✕ Remove
                  </button>
                </div>
              )}
            </div>

            <div style={{ marginBottom: 20 }}>
              <label style={{ display: "block", fontWeight: 600, marginBottom: 8, color: "#374151", fontSize: "0.85rem" }}>
                Visibility
              </label>
              <div style={{ display: "flex", gap: 16 }}>
                {(["CLASS", "PRIVATE"] as const).map(v => (
                  <label
                    key={v}
                    style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer", fontSize: "0.875rem" }}
                  >
                    <input
                      type="radio"
                      name="visibility"
                      checked={newVisibility === v}
                      onChange={() => setNewVisibility(v)}
                    />
                    {v === "CLASS" ? "🌍 Visible to whole class" : "🔒 Private (teachers only)"}
                  </label>
                ))}
              </div>
            </div>

            <div style={{ display: "flex", gap: 12, justifyContent: "flex-end" }}>
              <button
                style={btnStyle("secondary")}
                onClick={() => {
                  setShowNewDoubt(false);
                  removeSelectedFile();
                }}
              >
                Cancel
              </button>
              <button
                style={btnStyle("primary")}
                onClick={postDoubt}
                disabled={submitting || !newTitle.trim() || !newBody.trim()}
              >
                {submitting ? "Uploading & Posting..." : "Post Doubt"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Lightbox Modal for full size photo viewing */}
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

export default StudentDoubtsPage;
