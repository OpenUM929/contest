import React, { useEffect, useState } from "react";
import {
  View, Text, TouchableOpacity, Image, ScrollView,
  StyleSheet, ActivityIndicator, Dimensions, Alert, Linking,
  Modal, FlatList,
} from "react-native";
import * as Speech from "expo-speech";
import { Topic } from "../types/survey";
import { fetchTopic, fetchMySurveys, fetchEssayArchive, fetchEssayDetail, fetchTopicArchive } from "../api/survey";
import ElderlySurvey from "../components/ElderlySurvey";

const { width } = Dimensions.get("window");

export default function ElderlyMain({ userId }: { userId: string }) {
  const [topic, setTopic] = useState<Topic | null>(null);
  const [aiResponse, setAiResponse] = useState("");
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [fontSize, setFontSize] = useState(20);

  // 모달 상태
  const [modalType, setModalType] = useState<"my-surveys" | "essay-archive" | "topic-archive" | null>(null);
  const [mySurveys, setMySurveys] = useState<any[]>([]);
  const [essayArchive, setEssayArchive] = useState<any[]>([]);
  const [topicArchive, setTopicArchive] = useState<any[]>([]);
  const [selectedEssay, setSelectedEssay] = useState<any>(null);
  const [loadingModal, setLoadingModal] = useState(false);

  useEffect(() => {
    loadTopic();
  }, []);

  const loadTopic = async () => {
    const data = await fetchTopic(userId);
    setTopic(data);
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

  const handleCrisis = (level: string) => {
    const isHigh = level === "high";
    Alert.alert(
      "도움이 필요하신가요?",
      isHigh
        ? "힘드실 때는 혼자 참지 마세요. 정신건강 위기상담전화 1393으로 전화하시면 24시간 도움받으실 수 있습니다."
        : "힘드신 마음이 느껴집니다. 언제든 1393에 전화하시면 전문가와 대화할 수 있습니다.",
      [
        { text: "닫기", style: "cancel" },
        {
          text: "1393 전화하기",
          onPress: () => Linking.openURL("tel:1393"),
        },
      ]
    );
  };

  const openMySurveys = async () => {
    setModalType("my-surveys");
    setLoadingModal(true);
    try {
      const data = await fetchMySurveys(userId);
      setMySurveys(data.topics || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingModal(false);
    }
  };

  const openEssayArchive = async () => {
    setModalType("essay-archive");
    setLoadingModal(true);
    try {
      const data = await fetchEssayArchive();
      setEssayArchive(data);
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

  const openTopicArchive = async () => {
    setModalType("topic-archive");
    setLoadingModal(true);
    try {
      const data = await fetchTopicArchive();
      setTopicArchive(data.topics || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingModal(false);
    }
  };

  const renderModal = () => {
    if (!modalType) return null;
    return (
      <Modal animationType="slide" transparent={false} visible={true} onRequestClose={() => { setModalType(null); setSelectedEssay(null); }}>
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={() => { setModalType(null); setSelectedEssay(null); }}>
              <Text style={styles.modalClose}>← 닫기</Text>
            </TouchableOpacity>
            <Text style={styles.modalTitle}>
              {modalType === "my-surveys" ? "내가 나눈 이야기" :
               modalType === "essay-archive" ? "지난 이야기" :
               modalType === "topic-archive" ? "다른 이들의 생각" : ""}
            </Text>
          </View>

          {loadingModal && <ActivityIndicator size="large" color="#E8572A" style={{ marginTop: 40 }} />}

          {!loadingModal && modalType === "my-surveys" && (
            <FlatList
              data={mySurveys}
              keyExtractor={(item) => item.topic_id}
              renderItem={({ item }) => (
                <View style={styles.modalCard}>
                  <Text style={[styles.modalCardTitle, { fontSize }]}>{item.topic_title}</Text>
                  {item.responses.map((r: any, idx: number) => (
                    <View key={idx} style={{ marginTop: 8 }}>
                      {r.selected_option_label && (
                        <Text style={[styles.modalText, { fontSize: fontSize - 2 }]}>✓ {r.selected_option_label}</Text>
                      )}
                      {r.narrative_text && (
                        <Text style={[styles.modalText, { fontSize: fontSize - 2 }]}>📝 {r.narrative_text}</Text>
                      )}
                    </View>
                  ))}
                </View>
              )}
            />
          )}

          {!loadingModal && modalType === "essay-archive" && !selectedEssay && (
            <FlatList
              data={essayArchive}
              keyExtractor={(item) => item.essay_id}
              renderItem={({ item }) => (
                <TouchableOpacity style={styles.modalCard} onPress={() => openEssayDetail(item.essay_id)}>
                  <Text style={[styles.modalCardTitle, { fontSize }]}>{item.topic_title}</Text>
                  <Text style={[styles.modalMeta, { fontSize: fontSize - 4 }]}>
                    {item.active_week} · {item.contributor_cnt}명의 이야기
                  </Text>
                </TouchableOpacity>
              )}
            />
          )}

          {!loadingModal && modalType === "essay-archive" && selectedEssay && (
            <ScrollView>
              <View style={styles.modalCard}>
                <Text style={[styles.modalCardTitle, { fontSize: fontSize + 2 }]}>{selectedEssay.title}</Text>
                <Text style={[styles.modalText, { fontSize, lineHeight: fontSize * 1.6 }]}>{selectedEssay.content}</Text>
                <TouchableOpacity style={styles.ttsBtn} onPress={() => speakText(selectedEssay.content)}>
                  <Text style={styles.ttsBtnText}>🔊 읽어 듣기</Text>
                </TouchableOpacity>
              </View>
            </ScrollView>
          )}

          {!loadingModal && modalType === "topic-archive" && (
            <FlatList
              data={topicArchive}
              keyExtractor={(item) => item.topic_id}
              renderItem={({ item }) => (
                <View style={styles.modalCard}>
                  <Text style={[styles.modalCardTitle, { fontSize }]}>{item.title}</Text>
                  <Text style={[styles.modalMeta, { fontSize: fontSize - 4 }]}>
                    {item.respondents}명 참여 · {item.has_essay ? "수필 있음" : "수필 없음"}
                  </Text>
                </View>
              )}
            />
          )}
        </View>
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

      {/* 하단 메뉴: 3개 버튼 */}
      <View style={styles.bottomMenu}>
        <TouchableOpacity style={styles.menuBtn} onPress={openEssayArchive}>
          <Text style={[styles.menuText, { fontSize: fontSize - 2 }]}>지난 이야기 듣기</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.menuBtn} onPress={openMySurveys}>
          <Text style={[styles.menuText, { fontSize: fontSize - 2 }]}>내가 나눈 이야기</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.menuBtn} onPress={openTopicArchive}>
          <Text style={[styles.menuText, { fontSize: fontSize - 2 }]}>다른 이들의 생각</Text>
        </TouchableOpacity>
      </View>

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
  source: { color: "#AAA", marginBottom: 12 },
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
});
