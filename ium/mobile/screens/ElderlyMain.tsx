import React, { useEffect, useState } from "react";
import {
  View, Text, TouchableOpacity, Image, ScrollView,
  StyleSheet, ActivityIndicator, Dimensions, Alert, Linking,
  Modal, FlatList, ToastAndroid, Platform,
} from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import * as Speech from "expo-speech";
import { Topic } from "../types/survey";
import { fetchTopic, fetchAvailableSurveys, fetchTopicById, fetchTopicStatistics, fetchDeliverablesArchive, fetchEssayDetail } from "../api/survey";
import { triggerWelfareContact } from "../api/safety";
import ElderlySurvey from "../components/ElderlySurvey";
import axios from "axios";

const API_BASE = process.env.EXPO_PUBLIC_API_URL || "http://localhost:8000";

const { width } = Dimensions.get("window");

export default function ElderlyMain({ userId, onLogout }: { userId: string; onLogout?: () => void }) {
  const [topic, setTopic] = useState<Topic | null>(null);
  const [aiResponse, setAiResponse] = useState("");
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [fontSize, setFontSize] = useState(20);

  // 모달 상태
  const [modalType, setModalType] = useState<"survey-management" | "statistics" | "deliverables" | null>(null);
  const [availableSurveys, setAvailableSurveys] = useState<any[]>([]);
  const [deliverables, setDeliverables] = useState<any[]>([]);
  const [selectedEssay, setSelectedEssay] = useState<any>(null);
  const [selectedTopicForSurvey, setSelectedTopicForSurvey] = useState<any | null>(null);
  const [surveyAnalytics, setSurveyAnalytics] = useState<any | null>(null);
  const [selectedStatTopic, setSelectedStatTopic] = useState<any>(null);
  const [loadingModal, setLoadingModal] = useState(false);
  const [rejoinAlert, setRejoinAlert] = useState(false);

  useEffect(() => {
    loadTopic();
  }, []);

  const loadTopic = async () => {
    const data = await fetchTopic(userId);
    setTopic(data);
    // 주제 확인 기록 (acknowledge)
    if (data.id) {
      axios.post(`${API_BASE}/chat/topic/${data.id}/acknowledge`, { user_id: userId })
        .catch(() => {});
    }
    const intro = data.ai_question || data.title;
    speakText(`이번 주 이야기입니다. ${data.title}. ${intro}`);
  };

  const speakText = (text: string) => {
    if (!text) return;
    Speech.stop();
    setIsSpeaking(true);
    Speech.speak(text, {
      language: "ko",
      onDone: () => setIsSpeaking(false),
      onError: () => setIsSpeaking(false),
    });
  };

  const handleAiResponse = (text: string) => {
    setAiResponse(text);
    speakText(text);
  };

  const showToast = (message: string) => {
    if (Platform.OS === "android") {
      ToastAndroid.show(message, ToastAndroid.SHORT);
    } else {
      Alert.alert(message, "", [{ text: "확인" }], { cancelable: true });
    }
  };

  const handleLogout = () => {
    Alert.alert(
      "계정 전환",
      "다른 계정으로 전환하시겠습니까?",
      [
        { text: "취소", style: "cancel" },
        { text: "전환", onPress: () => onLogout?.() },
      ]
    );
  };

  const handleCrisis = (level: string) => {
    if (level === "high") {
      Alert.alert(
        "지금 힘드신가요?",
        "전문가와 바로 연결해 드릴게요.",
        [
          { text: "1393 전화하기", onPress: () => Linking.openURL("tel:1393") },
          { text: "닫기", style: "cancel" },
        ]
      );
    } else if (level === "medium") {
      Alert.alert(
        "많이 힘드신가요?",
        "복지사 선생님께 알려드릴게요.",
        [
          { text: "복지사에게 연락하기", onPress: () => triggerWelfareContact(userId) },
          { text: "괜찮아요", style: "cancel" },
        ]
      );
    } else if (level === "low") {
      showToast("오늘 많이 힘드셨군요. 언제든 이야기해주세요.");
    }
  };

  const openSurveyManagement = async () => {
    setModalType("survey-management");
    setSelectedTopicForSurvey(null);
    setLoadingModal(true);
    try {
      const data = await fetchAvailableSurveys(userId);
      setAvailableSurveys(data.surveys || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingModal(false);
    }
  };

  const [pendingRejoinId, setPendingRejoinId] = useState<string | null>(null);

  const handleSurveyCardPress = async (item: any) => {
    if (item.has_responded) {
      setPendingRejoinId(item.topic_id);
      setRejoinAlert(true);
      return;
    }
    await enterSurvey(item.topic_id);
  };

  const enterSurvey = async (topicId: string) => {
    setLoadingModal(true);
    try {
      const topicData = await fetchTopicById(topicId);
      setSelectedTopicForSurvey(topicData);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingModal(false);
    }
  };

  const confirmRejoin = async () => {
    setRejoinAlert(false);
    if (pendingRejoinId) {
      await enterSurvey(pendingRejoinId);
      setPendingRejoinId(null);
    }
  };

  const openDeliverables = async () => {
    setModalType("deliverables");
    setLoadingModal(true);
    try {
      const data = await fetchDeliverablesArchive();
      setDeliverables(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingModal(false);
    }
  };

  const openEssayDetail = async (essayId: string) => {
    setLoadingModal(true);
    try {
      const data = await fetchEssayDetail(essayId);
      setSelectedEssay(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingModal(false);
    }
  };

  const openStatistics = async () => {
    setModalType("statistics");
    setSurveyAnalytics(null);
    setSelectedStatTopic(null);
    setLoadingModal(true);
    try {
      const data = await fetchAvailableSurveys(userId);
      setAvailableSurveys(data.surveys || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingModal(false);
    }
  };

  const selectStatTopic = async (topicId: string) => {
    setLoadingModal(true);
    try {
      const data = await fetchTopicStatistics(topicId, userId);
      setSurveyAnalytics(data);
      setSelectedStatTopic(data);
    } catch (e: any) {
      if (e.response?.status === 403) {
        showToast("이 설문에 먼저 참여해 주세요.");
      } else {
        console.error(e);
      }
    } finally {
      setLoadingModal(false);
    }
  };

  const renderModal = () => {
    if (!modalType) return null;
    return (
      <Modal animationType="slide" transparent={false} visible={true} onRequestClose={() => { setModalType(null); setSelectedEssay(null); setSelectedTopicForSurvey(null); setSurveyAnalytics(null); setSelectedStatTopic(null); }}>
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={() => { setModalType(null); setSelectedEssay(null); setSelectedTopicForSurvey(null); setSurveyAnalytics(null); setSelectedStatTopic(null); }}>
              <Text style={styles.modalClose}>← 닫기</Text>
            </TouchableOpacity>
            <Text style={styles.modalTitle}>
              {modalType === "survey-management" ? "설문지 관리" :
               modalType === "statistics" ? "통계 보기" :
               modalType === "deliverables" ? "결과물 전달" : ""}
            </Text>
          </View>

          {loadingModal && <ActivityIndicator size="large" color="#E8572A" style={{ marginTop: 40 }} />}

          {/* ── 설문지 관리 ── */}
          {!loadingModal && modalType === "survey-management" && !selectedTopicForSurvey && (
            <FlatList
              data={availableSurveys}
              keyExtractor={(item) => item.topic_id}
              renderItem={({ item }) => (
                <TouchableOpacity style={styles.modalCard} onPress={() => handleSurveyCardPress(item)}>
                  <View style={styles.badgeRow}>
                    <View style={[styles.badge, item.has_responded ? styles.badgeDone : styles.badgeNew]}>
                      <Text style={[styles.badgeText, { fontSize: fontSize - 6 }]}>
                        {item.has_responded ? "작성완료" : "신규"}
                      </Text>
                    </View>
                  </View>
                  <Text style={[styles.modalCardTitle, { fontSize }]}>{item.title}</Text>
                  <Text style={[styles.modalMeta, { fontSize: fontSize - 4 }]}>
                    📅 {item.active_week || "날짜 미정"}
                  </Text>
                </TouchableOpacity>
              )}
            />
          )}

          {/* 설문 재참여: ElderlySurvey를 모달 안에 표시 */}
          {!loadingModal && modalType === "survey-management" && selectedTopicForSurvey && (
            <ScrollView>
              <View style={styles.modalCard}>
                <Text style={[styles.modalCardTitle, { fontSize: fontSize + 2 }]}>{selectedTopicForSurvey.title}</Text>
                <ElderlySurvey
                  topic={selectedTopicForSurvey}
                  userId={userId}
                  fontSize={fontSize}
                  topicId={selectedTopicForSurvey.id}
                  onSendStart={() => setAiResponse("")}
                  onAiResponse={handleAiResponse}
                  onCrisis={handleCrisis}
                />
              </View>
            </ScrollView>
          )}

          {/* ── 통계 ── */}
          {!loadingModal && modalType === "statistics" && !selectedStatTopic && (
            <FlatList
              data={availableSurveys.filter((s) => s.has_responded)}
              keyExtractor={(item) => item.topic_id}
              ListEmptyComponent={
                <Text style={[styles.modalMeta, { fontSize, textAlign: "center", marginTop: 40 }]}>
                  아직 참여한 설문이 없습니다.
                </Text>
              }
              renderItem={({ item }) => (
                <TouchableOpacity style={styles.modalCard} onPress={() => selectStatTopic(item.topic_id)}>
                  <Text style={[styles.modalCardTitle, { fontSize }]}>{item.title}</Text>
                  <Text style={[styles.modalMeta, { fontSize: fontSize - 4 }]}>
                    📅 {item.active_week || ""}
                  </Text>
                </TouchableOpacity>
              )}
            />
          )}

          {!loadingModal && modalType === "statistics" && selectedStatTopic && (
            <ScrollView>
              <Text style={[styles.modalCardTitle, { fontSize: fontSize + 2, marginBottom: 8 }]}>
                {selectedStatTopic.topic_title}
              </Text>
              <Text style={[styles.modalMeta, { fontSize: fontSize - 4, marginBottom: 16 }]}>
                총 {selectedStatTopic.total_respondents}명 참여
              </Text>
              {selectedStatTopic.my_responses.map((q: any, idx: number) => (
                <View key={idx} style={styles.modalCard}>
                  <Text style={[styles.modalText, { fontSize, fontWeight: "bold", marginBottom: 8 }]}>
                    {q.question_text}
                  </Text>
                  <Text style={[styles.modalMeta, { fontSize: fontSize - 4, marginBottom: 4 }]}>
                    나의 답변: {q.my_answer || "(미응답)"} ✓
                  </Text>
                  {q.question_type === "choice" && q.statistics && (
                    <View style={{ marginTop: 8 }}>
                      {q.statistics.map((stat: any, si: number) => (
                        <View key={si} style={{ flexDirection: "row", alignItems: "center", marginBottom: 4 }}>
                          <View style={{ flex: 1 }}>
                            <Text style={[styles.modalText, { fontSize: fontSize - 4 }]}>{stat.label}</Text>
                          </View>
                          <View style={{ width: 100, height: 14, backgroundColor: "#EEE", borderRadius: 7, marginHorizontal: 8 }}>
                            <View style={{ width: `${stat.percent}%`, height: 14, backgroundColor: "#E8572A", borderRadius: 7 }} />
                          </View>
                          <Text style={[styles.modalMeta, { fontSize: fontSize - 6, minWidth: 40 }]}>{stat.percent}%</Text>
                        </View>
                      ))}
                    </View>
                  )}
                  {q.question_type === "narrative" && q.sample_responses && (
                    <View style={{ marginTop: 8 }}>
                      <Text style={[styles.modalMeta, { fontSize: fontSize - 4 }]}>
                        총 {q.response_count || 0}명이 답변했어요
                      </Text>
                      {q.sample_responses.slice(0, 5).map((sr: any, si: number) => (
                        <Text key={si} style={[styles.modalText, { fontSize: fontSize - 4, marginTop: 4 }]}>
                          📝 {sr.text?.substring(0, 80)}
                        </Text>
                      ))}
                    </View>
                  )}
                </View>
              ))}
            </ScrollView>
          )}

          {/* ── 결과물 전달 ── */}
          {!loadingModal && modalType === "deliverables" && !selectedEssay && (
            <FlatList
              data={deliverables}
              keyExtractor={(item) => item.essay_id}
              ListEmptyComponent={
                <Text style={[styles.modalMeta, { fontSize, textAlign: "center", marginTop: 40 }]}>
                  아직 결과물이 없습니다.
                </Text>
              }
              renderItem={({ item }) => (
                <TouchableOpacity style={styles.modalCard} onPress={() => openEssayDetail(item.essay_id)}>
                  <Text style={[styles.modalCardTitle, { fontSize }]}>
                    {item.content_type === "poem" ? "📝 시 " :
                     item.content_type === "novel" ? "📖 소설 " :
                     "📖 수필 "}
                    「{item.topic_title}」
                  </Text>
                  <Text style={[styles.modalMeta, { fontSize: fontSize - 4 }]}>
                    👥 {item.contributor_cnt}명의 이야기 · {item.active_week || ""}
                  </Text>
                </TouchableOpacity>
              )}
            />
          )}

          {!loadingModal && modalType === "deliverables" && selectedEssay && (
            <ScrollView>
              <View style={styles.modalCard}>
                <Text style={[styles.modalCardTitle, { fontSize: fontSize + 2 }]}>{selectedEssay.title}</Text>
                <Text style={[styles.modalMeta, { fontSize: fontSize - 4, marginBottom: 12 }]}>
                  {selectedEssay.content_type === "poem" ? "📝 시" :
                   selectedEssay.content_type === "novel" ? "📖 소설" : "📖 수필"}
                </Text>
                <Text style={[styles.modalText, { fontSize, lineHeight: fontSize * 1.6 }]}>{selectedEssay.content}</Text>
                <TouchableOpacity style={styles.ttsBtn} onPress={() => {
                  Speech.stop();
                  Speech.speak(selectedEssay.content, { language: "ko", rate: 0.9 });
                }}>
                  <Text style={styles.ttsBtnText}>🔊 읽어 듣기</Text>
                </TouchableOpacity>
              </View>
            </ScrollView>
          )}
        </View>

        {/* 재참여 확인 Alert */}
        {rejoinAlert && (
          <Modal transparent visible={true} animationType="fade" onRequestClose={() => { setRejoinAlert(false); setPendingRejoinId(null); }}>
            <View style={styles.alertOverlay}>
              <View style={styles.alertBox}>
                <Text style={[styles.alertTitle, { fontSize }]}>이전에 작성한 설문입니다</Text>
                <Text style={[styles.alertText, { fontSize: fontSize - 2 }]}>
                  기존 답변 위에 새로운 답변을 추가합니다.
                </Text>
                <View style={styles.alertBtns}>
                  <TouchableOpacity style={styles.alertCancel} onPress={() => { setRejoinAlert(false); setPendingRejoinId(null); }}>
                    <Text style={[styles.alertCancelText, { fontSize }]}>취소</Text>
                  </TouchableOpacity>
                  <TouchableOpacity style={styles.alertConfirm} onPress={confirmRejoin}>
                    <Text style={[styles.alertConfirmText, { fontSize }]}>추가 답변</Text>
                  </TouchableOpacity>
                </View>
              </View>
            </View>
          </Modal>
        )}
      </Modal>
    );
  };

  if (!topic) return <ActivityIndicator size="large" style={{ flex: 1 }} />;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* 헤더 */}
      <Text style={styles.header}>이음(以音)</Text>

      {/* 주제 카드 */}
      <View style={styles.topicCard}>
        <Text style={[styles.topicLabel, { fontSize }]}>이번 주 이야기</Text>
        {topic.media_url ? (
          <Image source={{ uri: topic.media_url }} style={styles.topicImage} />
        ) : (
          <View style={[styles.topicImage, styles.placeholder]}>
            <Text style={{ color: "#888", fontSize }}>📷 {topic.title}</Text>
          </View>
        )}
        <Text style={[styles.source, { fontSize: fontSize - 4 }]}>
          [{topic.source || "이음"} 제공]
        </Text>
        {topic.distributed_by && (
          <Text style={[styles.distributedBy, { fontSize: fontSize - 4 }]}>
            👤 {topic.distributed_by} 복지사님 준비
          </Text>
        )}

        <ElderlySurvey
          topic={topic}
          userId={userId}
          fontSize={fontSize}
          onSendStart={() => setAiResponse("")}
          onAiResponse={handleAiResponse}
          onCrisis={handleCrisis}
        />
      </View>

      {/* AI 응답 */}
      {aiResponse !== "" && (
        <View style={styles.responseCard}>
          <Text style={[styles.responseLabel, { fontSize: fontSize - 2 }]}>🤖 이음</Text>
          <Text style={[styles.responseText, { fontSize }]}>{aiResponse}</Text>
          {isSpeaking && (
            <Text style={styles.speakingIndicator}>🔊 읽어드리고 있어요...</Text>
          )}
        </View>
      )}

      {/* 하단 메뉴: 3개 버튼 (설문지 관리 / 통계 / 결과물 전달) */}
      <View style={styles.bottomMenu}>
        <TouchableOpacity style={styles.menuBtn} onPress={openSurveyManagement}>
          <Text style={[styles.menuText, { fontSize: fontSize - 2 }]}>설문지 관리</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.menuBtn} onPress={openStatistics}>
          <Text style={[styles.menuText, { fontSize: fontSize - 2 }]}>통계 보기</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.menuBtn} onPress={openDeliverables}>
          <Text style={[styles.menuText, { fontSize: fontSize - 2 }]}>결과물 전달</Text>
        </TouchableOpacity>
      </View>

      {/* 계정 전환 */}
      <TouchableOpacity onPress={handleLogout}>
        <Text style={[styles.switchAccount, { fontSize: fontSize - 4 }]}>
          🔄 계정 전환
        </Text>
      </TouchableOpacity>

      {/* 접근성: 글자 크기 조절 */}
      <View style={styles.accessRow}>
        <Text style={styles.accessLabel}>글자 크기</Text>
        <TouchableOpacity onPress={() => setFontSize((s) => Math.max(16, s - 2))}>
          <Text style={styles.accessBtn}>작게</Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={() => setFontSize((s) => Math.min(30, s + 2))}>
          <Text style={styles.accessBtn}>크게</Text>
        </TouchableOpacity>
      </View>

      {renderModal()}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#FFFDF7" },
  content: { padding: 24, paddingBottom: 48 },
  header: {
    fontSize: 28, fontWeight: "bold", textAlign: "center",
    color: "#4A3728", marginBottom: 24,
  },
  topicCard: {
    backgroundColor: "#FFF8EE", borderRadius: 16, padding: 20,
    marginBottom: 20, elevation: 2,
  },
  topicLabel: { color: "#888", marginBottom: 12 },
  topicImage: { width: "100%", height: 200, borderRadius: 12, marginBottom: 8 },
  placeholder: {
    backgroundColor: "#EEE", justifyContent: "center", alignItems: "center",
  },
  source: { color: "#AAA", marginBottom: 4 },
  distributedBy: { color: "#7B7BFF", marginBottom: 12, fontWeight: "bold" },
  responseCard: {
    backgroundColor: "#EEF7EE", borderRadius: 16, padding: 20, marginBottom: 20,
  },
  responseLabel: { color: "#4CAF50", fontWeight: "bold", marginBottom: 8 },
  responseText: { color: "#222", lineHeight: 32 },
  speakingIndicator: { color: "#4CAF50", marginTop: 8, fontSize: 14 },
  bottomMenu: { flexDirection: "row", flexWrap: "wrap", gap: 8, marginBottom: 16 },
  menuBtn: {
    flex: 1, minWidth: 90, backgroundColor: "#F0EBE3", borderRadius: 12,
    padding: 14, alignItems: "center", marginHorizontal: 2,
  },
  menuText: { color: "#4A3728", textAlign: "center" },
  switchAccount: {
    color: "#888", textAlign: "center", marginBottom: 12, textDecorationLine: "underline",
  },
  accessRow: {
    flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 12,
  },
  accessLabel: { color: "#888", fontSize: 14 },
  accessBtn: {
    color: "#E8572A", fontSize: 14, fontWeight: "bold",
    paddingHorizontal: 12, paddingVertical: 6,
    borderWidth: 1, borderColor: "#E8572A", borderRadius: 8,
  },
  // 모달
  modalContainer: { flex: 1, backgroundColor: "#FFFDF7", padding: 20 },
  modalHeader: { flexDirection: "row", alignItems: "center", marginBottom: 20, gap: 12 },
  modalClose: { color: "#E8572A", fontSize: 16, fontWeight: "bold" },
  modalTitle: { fontSize: 20, fontWeight: "bold", color: "#4A3728" },
  modalCard: {
    backgroundColor: "#FFF8EE", borderRadius: 12, padding: 16,
    marginBottom: 12, elevation: 1,
  },
  modalCardTitle: { fontWeight: "bold", color: "#4A3728", marginBottom: 4 },
  modalText: { color: "#333", marginTop: 2 },
  modalMeta: { color: "#888", marginTop: 4 },
  ttsBtn: {
    backgroundColor: "#E8572A", borderRadius: 10, padding: 12,
    alignItems: "center", marginTop: 16,
  },
  ttsBtnText: { color: "#FFF", fontWeight: "bold", fontSize: 14 },
  // 배지
  badgeRow: { flexDirection: "row", marginBottom: 6 },
  badge: {
    paddingHorizontal: 10, paddingVertical: 3, borderRadius: 10,
  },
  badgeNew: { backgroundColor: "#E8572A" },
  badgeDone: { backgroundColor: "#4CAF50" },
  badgeText: { color: "#FFF", fontWeight: "bold" },
  // Alert
  alertOverlay: {
    flex: 1, backgroundColor: "rgba(0,0,0,0.5)",
    justifyContent: "center", alignItems: "center",
  },
  alertBox: {
    backgroundColor: "#FFF8EE", borderRadius: 16, padding: 24,
    marginHorizontal: 32, elevation: 8,
  },
  alertTitle: { fontWeight: "bold", color: "#4A3728", marginBottom: 8 },
  alertText: { color: "#666", marginBottom: 20 },
  alertBtns: { flexDirection: "row", justifyContent: "flex-end", gap: 12 },
  alertCancel: { paddingHorizontal: 16, paddingVertical: 10 },
  alertCancelText: { color: "#888" },
  alertConfirm: {
    backgroundColor: "#E8572A", borderRadius: 10,
    paddingHorizontal: 20, paddingVertical: 10,
  },
  alertConfirmText: { color: "#FFF", fontWeight: "bold" },
});
