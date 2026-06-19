import React, { useState } from "react";
import {
  View, Text, TouchableOpacity, ScrollView,
  StyleSheet, ActivityIndicator, Alert,
} from "react-native";
import axios from "axios";

const API = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";

const CONSENTS = [
  {
    type: "privacy",
    title: "개인정보 처리 방침",
    detail:
      "수집 항목: 대화 내용, 감정 분석 결과\n보유 기간: 서비스 탈퇴 시까지\n제3자 제공: 없음 (복지사만 열람 가능)\n이용 목적: 노인-청년 연결 서비스 제공",
  },
  {
    type: "terms",
    title: "서비스 이용 약관",
    detail:
      "이음(以音)은 고독사 위험 노인과 은둔 청년을 연결하는 AI 기반 사회안전망 서비스입니다.\n서비스 내 대화는 복지사가 검토할 수 있으며, 위기 상황 시 즉시 지원이 이루어질 수 있습니다.",
  },
  {
    type: "ai_usage",
    title: "AI 대화 분석 활용 동의",
    detail:
      "귀하의 대화 내용은 AI 감정 분석에 활용됩니다.\n분석 결과는 수필 생성 및 복지사 모니터링에 사용되며, 개인 식별이 불가능한 형태로 처리됩니다.",
  },
];

interface Props {
  userId: string;
  onComplete: () => void;
}

export default function ConsentScreen({ userId, onComplete }: Props) {
  const [agreed, setAgreed] = useState<Record<string, boolean>>({
    privacy: false,
    terms: false,
    ai_usage: false,
  });
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(false);

  const allAgreed = Object.values(agreed).every(Boolean);

  const toggleAll = () => {
    const next = !allAgreed;
    setAgreed({ privacy: next, terms: next, ai_usage: next });
  };

  const toggleExpand = (type: string) => {
    setExpanded((prev) => ({ ...prev, [type]: !prev[type] }));
  };

  const handleSubmit = async () => {
    if (!allAgreed) return;
    setLoading(true);
    try {
      await axios.post(`${API}/api/auth/consent`, {
        user_id: userId,
        consents: Object.entries(agreed).map(([consent_type, a]) => ({
          consent_type,
          agreed: a,
        })),
      });
      onComplete();
    } catch {
      Alert.alert("오류", "동의 처리 중 문제가 발생했습니다. 다시 시도해 주세요.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>이음(以音) 시작하기</Text>
      <Text style={styles.subtitle}>
        서비스를 이용하려면 아래 약관에 동의해 주세요.
      </Text>

      {/* 전체 동의 */}
      <TouchableOpacity style={styles.allToggle} onPress={toggleAll}>
        <View style={[styles.checkbox, allAgreed && styles.checkboxOn]}>
          {allAgreed && <Text style={styles.checkmark}>✓</Text>}
        </View>
        <Text style={styles.allToggleText}>전체 동의</Text>
      </TouchableOpacity>

      <View style={styles.divider} />

      {/* 개별 동의 항목 */}
      {CONSENTS.map((item) => (
        <View key={item.type} style={styles.consentItem}>
          <View style={styles.consentRow}>
            <TouchableOpacity
              onPress={() =>
                setAgreed((prev) => ({ ...prev, [item.type]: !prev[item.type] }))
              }
            >
              <View style={[styles.checkbox, agreed[item.type] && styles.checkboxOn]}>
                {agreed[item.type] && <Text style={styles.checkmark}>✓</Text>}
              </View>
            </TouchableOpacity>
            <Text style={styles.consentTitle}>[필수] {item.title}</Text>
            <TouchableOpacity onPress={() => toggleExpand(item.type)}>
              <Text style={styles.expandBtn}>
                {expanded[item.type] ? "접기 ▲" : "보기 ▼"}
              </Text>
            </TouchableOpacity>
          </View>
          {expanded[item.type] && (
            <View style={styles.detailBox}>
              <Text style={styles.detailText}>{item.detail}</Text>
            </View>
          )}
        </View>
      ))}

      {/* 시작하기 버튼 */}
      <TouchableOpacity
        style={[styles.startBtn, !allAgreed && styles.startBtnDisabled]}
        onPress={handleSubmit}
        disabled={!allAgreed || loading}
      >
        {loading ? (
          <ActivityIndicator color="#FFF" />
        ) : (
          <Text style={styles.startBtnText}>시작하기</Text>
        )}
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#FFFDF7" },
  content: { padding: 24, paddingBottom: 48 },
  title: {
    fontSize: 26, fontWeight: "bold", color: "#4A3728",
    textAlign: "center", marginBottom: 8,
  },
  subtitle: {
    fontSize: 14, color: "#888", textAlign: "center", marginBottom: 28,
  },
  allToggle: {
    flexDirection: "row", alignItems: "center", gap: 12, marginBottom: 16,
  },
  allToggleText: { fontSize: 16, fontWeight: "bold", color: "#4A3728" },
  divider: { height: 1, backgroundColor: "#E0D8CE", marginBottom: 16 },
  consentItem: { marginBottom: 16 },
  consentRow: {
    flexDirection: "row", alignItems: "center", gap: 10,
  },
  consentTitle: { flex: 1, fontSize: 15, color: "#333" },
  expandBtn: { fontSize: 12, color: "#E8572A", fontWeight: "bold" },
  detailBox: {
    backgroundColor: "#F5F0E8", borderRadius: 8,
    padding: 12, marginTop: 8,
  },
  detailText: { fontSize: 13, color: "#555", lineHeight: 20 },
  checkbox: {
    width: 24, height: 24, borderRadius: 6,
    borderWidth: 2, borderColor: "#C0B4A0",
    justifyContent: "center", alignItems: "center",
  },
  checkboxOn: { backgroundColor: "#E8572A", borderColor: "#E8572A" },
  checkmark: { color: "#FFF", fontSize: 14, fontWeight: "bold" },
  startBtn: {
    backgroundColor: "#E8572A", borderRadius: 14,
    padding: 18, alignItems: "center", marginTop: 24,
  },
  startBtnDisabled: { backgroundColor: "#C0B4A0" },
  startBtnText: { color: "#FFF", fontSize: 17, fontWeight: "bold" },
});
