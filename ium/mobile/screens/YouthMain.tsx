import React, { useEffect, useState } from "react";
import {
  View, Text, TouchableOpacity, ScrollView,
  StyleSheet, ActivityIndicator, Alert, Linking,
  Modal, FlatList, ToastAndroid, Platform,
} from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { Audio } from "expo-av";
import * as Speech from "expo-speech";
import { Topic } from "../types/survey";
import { fetchTopic, fetchAvailableSurveys, fetchTopicById, fetchTopicStatistics, fetchDeliverablesArchive, fetchEssayDetail } from "../api/survey";
import axios from "axios";

const API_BASE = process.env.EXPO_PUBLIC_API_URL || "http://localhost:8000";
import { triggerWelfareContact } from "../api/safety";
import YouthSurvey from "../components/YouthSurvey";

export default function YouthMain({ userId, onLogout }: { userId: string; onLogout?: () => void }) {
  const [topic, setTopic] = useState<Topic | null>(null);
  const [aiResponse, setAiResponse] = useState("");
  const [isPlaying, setIsPlaying] = useState(false);
  const soundRef = React.useRef<Audio.Sound | null>(null);

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
  const [pendingRejoinId, setPendingRejoinId] = useState<string | null>(null);

  useEffect(() => {
    loadTopic();
    return () => { soundRef.current?.unloadAsync(); };
  }, []);

  const loadTopic = async () => {
    const data = await fetchTopic(userId);
    setTopic(data);
    if (data.id) {
      axios.post(`${API_BASE}/chat/topic/${data.id}/acknowledge`, { user_id: userId })
        .catch(() => {});
    }
  };

  const playAudio = async () => {
    if (!topic?.media_url || topic.media_type !== "audio") return;
    if (isPlaying) {
      await soundRef.current?.pauseAsync();
      setIsPlaying(false);
      return;
    }
    const { sound } = await Audio.Sound.createAsync({ uri: topic.media_url });
    soundRef.current = sound;
    await sound.playAsync();
    setIsPlaying(true);
    sound.setOnPlaybackStatusUpdate((s) => {
      if (s.isLoaded && s.didJustFinish) setIsPlaying(false);
    });
  };

  const handleAiResponse = (text: string) => {
    setAiResponse(text);
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

          {loadingModal && <ActivityIndicator size="large" color="#7B7BFF" style={{ marginTop: 40 }} />}

          {/* ── 설문지 관리 ── */}
          {!loadingModal && modalType === "survey-management" && !selectedTopicForSurvey && (
            <FlatList
              data={availableSurveys}
              keyExtractor={(item) => item.topic_id}
              renderItem={({ item }) => (
                <TouchableOpacity style={styles.modalCard} onPress={() => handleSurveyCardPress(item)}>
                  <View style={styles.badgeRow}>
                    <View style={[styles.badge, item.has_responded ? styles.badgeDone : styles.badgeNew]}>
                      <Text style={styles.badgeText}>
                        {item.has_responded ? "작성완료" : "신규"}
                      </Text>
                    </View>
                  </View>
                  <Text style={styles.modalCardTitle}>{item.title}</Text>
                  <Text style={styles.modalMeta}>
                    📅 {item.active_week || "날짜 미정"}
                  </Text>
                </TouchableOpacity>
              )}
            />
          )}

          {/* 설문 재참여: YouthSurvey를 모달 안에 표시 */}
          {!loadingModal && modalType === "survey-management" && selectedTopicForSurvey && (
            <ScrollView>
              <View style={styles.modalCard}>
                <Text style={styles.modalCardTitle}>{selectedTopicForSurvey.title}</Text>
                <YouthSurvey
                  topic={selectedTopicForSurvey}
                  userId={userId}
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
                <Text style={[styles.modalMeta, { textAlign: "center", marginTop: 40, fontSize: 14 }]}>
                  아직 참여한 설문이 없습니다.
                </Text>
              }
              renderItem={({ item }) => (
                <TouchableOpacity style={styles.modalCard} onPress={() => selectStatTopic(item.topic_id)}>
                  <Text style={styles.modalCardTitle}>{item.title}</Text>
                  <Text style={styles.modalMeta}>
                    📅 {item.active_week || ""}
                  </Text>
                </TouchableOpacity>
              )}
            />
          )}

          {!loadingModal && modalType === "statistics" && selectedStatTopic && (
            <ScrollView>
              <Text style={[styles.modalCardTitle, { marginBottom: 8 }]}>
                {selectedStatTopic.topic_title}
              </Text>
              <Text style={[styles.modalMeta, { marginBottom: 16 }]}>
                총 {selectedStatTopic.total_respondents}명 참여
              </Text>
              {selectedStatTopic.my_responses.map((q: any, idx: number) => (
                <View key={idx} style={styles.modalCard}>
                  <Text style={[styles.modalText, { fontWeight: "bold", marginBottom: 8 }]}>
                    {q.question_text}
                  </Text>
                  <Text style={[styles.modalMeta, { marginBottom: 4 }]}>
                    나의 답변: {q.my_answer || "(미응답)"} ✓
                  </Text>
                  {q.question_type === "choice" && q.statistics && (
                    <View style={{ marginTop: 8 }}>
                      {q.statistics.map((stat: any, si: number) => (
                        <View key={si} style={{ flexDirection: "row", alignItems: "center", marginBottom: 4 }}>
                          <View style={{ flex: 1 }}>
                            <Text style={styles.modalText}>{stat.label}</Text>
                          </View>
                          <View style={{ width: 80, height: 10, backgroundColor: "#2D2D4A", borderRadius: 5, marginHorizontal: 8 }}>
                            <View style={{ width: `${stat.percent}%`, height: 10, backgroundColor: "#7B7BFF", borderRadius: 5 }} />
                          </View>
                          <Text style={[styles.modalMeta, { minWidth: 36 }]}>{stat.percent}%</Text>
                        </View>
                      ))}
                    </View>
                  )}
                  {q.question_type === "narrative" && q.sample_responses && (
                    <View style={{ marginTop: 8 }}>
                      <Text style={styles.modalMeta}>
                        총 {q.response_count || 0}명이 답변했어요
                      </Text>
                      {q.sample_responses.slice(0, 5).map((sr: any, si: number) => (
                        <Text key={si} style={[styles.modalText, { marginTop: 4 }]}>
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
                <Text style={[styles.modalMeta, { textAlign: "center", marginTop: 40 }]}>
                  아직 결과물이 없습니다.
                </Text>
              }
              renderItem={({ item }) => (
                <TouchableOpacity style={styles.modalCard} onPress={() => openEssayDetail(item.essay_id)}>
                  <Text style={styles.modalCardTitle}>
                    {item.content_type === "poem" ? "📝 시 " :
                     item.content_type === "novel" ? "📖 소설 " :
                     "📖 수필 "}
                    「{item.topic_title}」
                  </Text>
                  <Text style={styles.modalMeta}>
                    👥 {item.contributor_cnt}명의 이야기 · {item.active_week || ""}
                  </Text>
                </TouchableOpacity>
              )}
            />
          )}

          {!loadingModal && modalType === "deliverables" && selectedEssay && (
            <ScrollView>
              <View style={styles.modalCard}>
                <Text style={[styles.modalCardTitle, { fontSize: 18 }]}>{selectedEssay.title}</Text>
                <Text style={[styles.modalMeta, { marginBottom: 12 }]}>
                  {selectedEssay.content_type === "poem" ? "📝 시" :
                   selectedEssay.content_type === "novel" ? "📖 소설" : "📖 수필"}
                </Text>
                <Text style={styles.modalText}>{selectedEssay.content}</Text>
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
                <Text style={styles.alertTitle}>이전에 작성한 설문입니다</Text>
                <Text style={styles.alertText}>
                  기존 답변 위에 새로운 답변을 추가합니다.
                </Text>
                <View style={styles.alertBtns}>
                  <TouchableOpacity style={styles.alertCancel} onPress={() => { setRejoinAlert(false); setPendingRejoinId(null); }}>
                    <Text style={styles.alertCancelText}>취소</Text>
                  </TouchableOpacity>
                  <TouchableOpacity style={styles.alertConfirm} onPress={confirmRejoin}>
                    <Text style={styles.alertConfirmText}>추가 답변</Text>
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
      <View style={styles.header}>
        <Text style={styles.headerTitle}>이음</Text>
        <View style={styles.anonBadge}>
          <Text style={styles.anonText}>👤 익명</Text>
        </View>
      </View>

      {/* 주제 카드 */}
      <View style={styles.topicCard}>
        <Text style={styles.topicWeek}>이번 주 주제</Text>
        <Text style={styles.topicTitle}>{topic.title}</Text>
        <Text style={styles.topicSource}>[{topic.source || "이음"} 제공]</Text>
        {topic.distributed_by && (
          <Text style={styles.distributedBy}>👤 {topic.distributed_by} 복지사님 준비</Text>
        )}

        {topic.media_type === "audio" && (
          <TouchableOpacity style={styles.playBtn} onPress={playAudio}>
            <Text style={styles.playIcon}>{isPlaying ? "⏸" : "▶"}</Text>
            <Text style={styles.playText}>{isPlaying ? "재생 중..." : "재생하기"}</Text>
          </TouchableOpacity>
        )}

        <YouthSurvey
          topic={topic}
          userId={userId}
          onSendStart={() => setAiResponse("")}
          onAiResponse={handleAiResponse}
          onCrisis={handleCrisis}
        />
      </View>

      {/* AI 응답 */}
      {aiResponse !== "" && (
        <View style={styles.responseCard}>
          <Text style={styles.responseLabel}>이음</Text>
          <Text style={styles.responseText}>{aiResponse}</Text>
        </View>
      )}

      {/* 하단 메뉴: 3개 버튼 (설문지 관리 / 통계 / 결과물 전달) */}
      <View style={styles.bottomMenu}>
        <TouchableOpacity style={styles.menuBtn} onPress={openSurveyManagement}>
          <Text style={styles.menuText}>설문지 관리</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.menuBtn} onPress={openStatistics}>
          <Text style={styles.menuText}>통계 보기</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.menuBtn} onPress={openDeliverables}>
          <Text style={styles.menuText}>결과물 전달</Text>
        </TouchableOpacity>
      </View>

      {/* 계정 전환 */}
      <TouchableOpacity onPress={handleLogout} style={{ marginTop: 16, alignSelf: "center" }}>
        <Text style={{ color: "#666", fontSize: 12, textDecorationLine: "underline" }}>
          🔄 계정 전환
        </Text>
      </TouchableOpacity>

      {renderModal()}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#1A1A2E" },
  content: { padding: 20, paddingBottom: 48 },
  header: {
    flexDirection: "row", justifyContent: "space-between",
    alignItems: "center", marginBottom: 24,
  },
  headerTitle: { fontSize: 22, fontWeight: "bold", color: "#E8E8FF" },
  anonBadge: {
    backgroundColor: "#2D2D4A", borderRadius: 20,
    paddingHorizontal: 14, paddingVertical: 6,
  },
  anonText: { color: "#AAA", fontSize: 13 },
  topicCard: {
    backgroundColor: "#16213E", borderRadius: 16, padding: 20, marginBottom: 20,
  },
  topicWeek: { color: "#7B7BFF", fontSize: 13, marginBottom: 8 },
  topicTitle: { color: "#E8E8FF", fontSize: 18, fontWeight: "bold", marginBottom: 4 },
  topicSource: { color: "#666", fontSize: 12, marginBottom: 4 },
  distributedBy: { color: "#7B7BFF", fontSize: 12, marginBottom: 16, fontWeight: "bold" },
  playBtn: {
    flexDirection: "row", alignItems: "center", backgroundColor: "#0F3460",
    borderRadius: 10, padding: 12, marginBottom: 16, gap: 8,
  },
  playIcon: { fontSize: 20, color: "#7B7BFF" },
  playText: { color: "#AAA", fontSize: 14 },
  responseCard: {
    backgroundColor: "#16213E", borderRadius: 16, padding: 20, marginBottom: 20,
  },
  responseLabel: { color: "#7B7BFF", fontSize: 13, fontWeight: "bold", marginBottom: 8 },
  responseText: { color: "#DDD", fontSize: 15, lineHeight: 24 },
  bottomMenu: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  menuBtn: {
    flex: 1, minWidth: 90, backgroundColor: "#16213E", borderRadius: 12,
    padding: 12, alignItems: "center",
  },
  menuText: { color: "#AAA", fontSize: 13, textAlign: "center" },
  // 모달
  modalContainer: { flex: 1, backgroundColor: "#1A1A2E", padding: 20 },
  modalHeader: { flexDirection: "row", alignItems: "center", marginBottom: 20, gap: 12 },
  modalClose: { color: "#7B7BFF", fontSize: 16, fontWeight: "bold" },
  modalTitle: { fontSize: 20, fontWeight: "bold", color: "#E8E8FF" },
  modalCard: {
    backgroundColor: "#16213E", borderRadius: 12, padding: 16,
    marginBottom: 12, borderWidth: 1, borderColor: "#2D2D4A",
  },
  modalCardTitle: { fontWeight: "bold", color: "#E8E8FF", marginBottom: 4 },
  modalText: { color: "#CCC", marginTop: 2, fontSize: 14 },
  modalMeta: { color: "#666", marginTop: 4, fontSize: 12 },
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
  badgeNew: { backgroundColor: "#7B7BFF" },
  badgeDone: { backgroundColor: "#4CAF50" },
  badgeText: { color: "#FFF", fontWeight: "bold", fontSize: 12 },
  // Alert
  alertOverlay: {
    flex: 1, backgroundColor: "rgba(0,0,0,0.5)",
    justifyContent: "center", alignItems: "center",
  },
  alertBox: {
    backgroundColor: "#16213E", borderRadius: 16, padding: 24,
    marginHorizontal: 32, borderWidth: 1, borderColor: "#2D2D4A", elevation: 8,
  },
  alertTitle: { fontWeight: "bold", color: "#E8E8FF", marginBottom: 8, fontSize: 16 },
  alertText: { color: "#AAA", marginBottom: 20, fontSize: 14 },
  alertBtns: { flexDirection: "row", justifyContent: "flex-end", gap: 12 },
  alertCancel: { paddingHorizontal: 16, paddingVertical: 10 },
  alertCancelText: { color: "#888" },
  alertConfirm: {
    backgroundColor: "#7B7BFF", borderRadius: 10,
    paddingHorizontal: 20, paddingVertical: 10,
  },
  alertConfirmText: { color: "#FFF", fontWeight: "bold" },
});
