// src/pages/SettingsPage.tsx
import { useEffect, useState } from "react";
import axios from "axios";
import { getApiKeys, saveApiKeys, Provider } from "../api/settings";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface Worker {
  welfare_id: string;
  name: string;
  region?: string;
}

const PROVIDERS: { id: Provider; label: string; placeholder: string }[] = [
  { id: "claude", label: "Claude (Anthropic)", placeholder: "sk-ant-..." },
  { id: "openai", label: "OpenAI (GPT)", placeholder: "sk-..." },
  { id: "gemini", label: "Google Gemini", placeholder: "AIza..." },
];

type KeyMap = Record<Provider, string>;
type BoolMap = Record<Provider, boolean>;

const emptyKeys: KeyMap = { claude: "", openai: "", gemini: "" };
const emptyBools: BoolMap = { claude: false, openai: false, gemini: false };

export default function SettingsPage() {
  const [workers, setWorkers] = useState<Worker[]>([]);
  const [welfareId, setWelfareId] = useState<string>("");

  const [masked, setMasked] = useState<KeyMap>({ ...emptyKeys }); // 서버에 저장된(마스킹) 값
  const [savedKeys, setSavedKeys] = useState<BoolMap>({ ...emptyBools });
  const [inputs, setInputs] = useState<KeyMap>({ ...emptyKeys }); // 새로 입력하는 값
  const [showKey, setShowKey] = useState<BoolMap>({ ...emptyBools });
  const [activeProvider, setActiveProvider] = useState<string>("");

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<{ type: "ok" | "err"; msg: string } | null>(null);

  // 복지사 목록 로드
  useEffect(() => {
    (async () => {
      try {
        const { data } = await axios.get(`${API}/api/welfare/workers`);
        const list: Worker[] = data.workers ?? [];
        setWorkers(list);
        if (list.length > 0) setWelfareId(list[0].welfare_id);
      } catch {
        setToast({ type: "err", msg: "복지사 목록을 불러오지 못했습니다." });
      }
    })();
  }, []);

  // 선택된 복지사의 키 로드
  useEffect(() => {
    if (!welfareId) return;
    (async () => {
      setLoading(true);
      try {
        const { data } = await getApiKeys(welfareId);
        const m: KeyMap = { claude: data.claude, openai: data.openai, gemini: data.gemini };
        setMasked(m);
        setSavedKeys({ claude: !!data.claude, openai: !!data.openai, gemini: !!data.gemini });
        setActiveProvider(data.active_provider || "");
        setInputs({ ...emptyKeys });
        setShowKey({ ...emptyBools });
      } catch {
        setToast({ type: "err", msg: "API 키를 불러오지 못했습니다." });
      } finally {
        setLoading(false);
      }
    })();
  }, [welfareId]);

  // 저장 후 사용 가능한 제공자 수 (기존 저장 OR 새로 입력)
  const willHaveKey = (p: Provider) => savedKeys[p] || inputs[p].trim().length > 0;
  const availableProviders = PROVIDERS.filter((p) => willHaveKey(p.id)).map((p) => p.id);
  const showRadio = availableProviders.length >= 2;

  const handleSave = async () => {
    if (!welfareId) {
      setToast({ type: "err", msg: "먼저 복지사를 선택하세요." });
      return;
    }
    // active_provider 정합성: 라디오 미표시(키 1개 이하)면 빈 값 → 서버가 자동 설정
    let active = showRadio ? activeProvider : "";
    if (active && !availableProviders.includes(active as Provider)) active = "";

    setSaving(true);
    try {
      const { data } = await saveApiKeys({
        welfare_id: welfareId,
        claude: inputs.claude.trim(), // 빈 값은 서버에서 '변경 없음'으로 처리
        openai: inputs.openai.trim(),
        gemini: inputs.gemini.trim(),
        active_provider: active,
      });
      setActiveProvider(data.active_provider || "");
      setToast({ type: "ok", msg: "저장되었습니다." });
      // 저장된 마스킹 값 갱신을 위해 재조회
      const { data: refreshed } = await getApiKeys(welfareId);
      setMasked({ claude: refreshed.claude, openai: refreshed.openai, gemini: refreshed.gemini });
      setSavedKeys({
        claude: !!refreshed.claude,
        openai: !!refreshed.openai,
        gemini: !!refreshed.gemini,
      });
      setInputs({ ...emptyKeys });
    } catch (e: any) {
      setToast({ type: "err", msg: e?.response?.data?.detail || "저장에 실패했습니다." });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={s.page}>
      <h2 style={s.title}>🔑 API 설정</h2>
      <p style={s.sub}>복지사별로 사용할 AI API 키를 등록합니다. 등록된 키는 서버에 암호화되어 저장됩니다.</p>

      <div style={s.row}>
        <label style={s.label}>복지사</label>
        <select value={welfareId} onChange={(e) => setWelfareId(e.target.value)} style={s.select}>
          {workers.length === 0 && <option value="">복지사 없음</option>}
          {workers.map((w) => (
            <option key={w.welfare_id} value={w.welfare_id}>
              {w.name}
              {w.region ? ` (${w.region})` : ""}
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <p style={{ color: "#888" }}>불러오는 중…</p>
      ) : (
        <>
          {PROVIDERS.map((p) => (
            <div key={p.id} style={s.card}>
              <div style={s.cardHead}>
                <strong>{p.label}</strong>
                {savedKeys[p.id] && <span style={s.badge}>✅ 저장됨</span>}
              </div>
              {savedKeys[p.id] && (
                <div style={s.maskedRow}>현재 저장된 키: <code>{masked[p.id]}</code></div>
              )}
              <div style={s.inputRow}>
                <input
                  type={showKey[p.id] ? "text" : "password"}
                  value={inputs[p.id]}
                  placeholder={savedKeys[p.id] ? "변경하려면 새 키 입력 (비우면 유지)" : p.placeholder}
                  onChange={(e) => setInputs((prev) => ({ ...prev, [p.id]: e.target.value }))}
                  style={s.input}
                />
                <button
                  type="button"
                  onClick={() => setShowKey((prev) => ({ ...prev, [p.id]: !prev[p.id] }))}
                  style={s.eye}
                  title={showKey[p.id] ? "숨기기" : "보기"}
                >
                  {showKey[p.id] ? "🙈" : "👁"}
                </button>
              </div>
            </div>
          ))}

          {showRadio && (
            <div style={s.card}>
              <div style={s.cardHead}>
                <strong>활성 API 선택</strong>
                <span style={{ color: "#888", fontSize: 12 }}>(주제 생성·작품 생성에 사용)</span>
              </div>
              <div style={s.radioRow}>
                {availableProviders.map((id) => (
                  <label key={id} style={s.radioLabel}>
                    <input
                      type="radio"
                      name="active"
                      checked={activeProvider === id}
                      onChange={() => setActiveProvider(id)}
                    />
                    {PROVIDERS.find((p) => p.id === id)?.label}
                  </label>
                ))}
              </div>
            </div>
          )}

          <button onClick={handleSave} disabled={saving} style={s.saveBtn}>
            {saving ? "저장 중…" : "💾 저장"}
          </button>
          <p style={s.note}>※ API 키는 서버에 암호화(Fernet)되어 저장됩니다.</p>
        </>
      )}

      {toast && (
        <div style={{ ...s.toast, background: toast.type === "ok" ? "#2E7D32" : "#C62828" }}>
          {toast.msg}
          <button onClick={() => setToast(null)} style={s.toastClose}>✕</button>
        </div>
      )}
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  page: { maxWidth: 640, margin: "32px auto", padding: "0 24px", fontFamily: "sans-serif", color: "#2A2A2A" },
  title: { fontSize: 24, marginBottom: 4 },
  sub: { color: "#666", fontSize: 14, marginBottom: 24 },
  row: { display: "flex", alignItems: "center", gap: 12, marginBottom: 20 },
  label: { width: 60, fontWeight: "bold", fontSize: 14 },
  select: { flex: 1, padding: "8px 10px", borderRadius: 8, border: "1px solid #ccc", fontSize: 14 },
  card: { border: "1px solid #e2e2e2", borderRadius: 12, padding: 16, marginBottom: 16, background: "#fff" },
  cardHead: { display: "flex", alignItems: "center", gap: 8, marginBottom: 10 },
  badge: { color: "#2E7D32", fontSize: 12, fontWeight: "bold" },
  maskedRow: { fontSize: 13, color: "#777", marginBottom: 8 },
  inputRow: { display: "flex", gap: 8 },
  input: { flex: 1, padding: "10px 12px", borderRadius: 8, border: "1px solid #ccc", fontSize: 14 },
  eye: { padding: "0 12px", borderRadius: 8, border: "1px solid #ccc", background: "#f7f7f7", cursor: "pointer" },
  radioRow: { display: "flex", gap: 20, flexWrap: "wrap" },
  radioLabel: { display: "flex", alignItems: "center", gap: 6, fontSize: 14, cursor: "pointer" },
  saveBtn: {
    width: "100%", padding: "12px", border: "none", borderRadius: 10,
    background: "#E8572A", color: "#fff", fontSize: 16, fontWeight: "bold", cursor: "pointer",
  },
  note: { fontSize: 12, color: "#999", marginTop: 12, textAlign: "center" },
  toast: {
    position: "fixed", bottom: 24, left: "50%", transform: "translateX(-50%)",
    color: "#fff", padding: "12px 20px", borderRadius: 10, fontSize: 14,
    display: "flex", alignItems: "center", gap: 12, boxShadow: "0 4px 12px rgba(0,0,0,0.2)",
  },
  toastClose: { background: "none", border: "none", color: "#fff", cursor: "pointer", fontSize: 14 },
};
