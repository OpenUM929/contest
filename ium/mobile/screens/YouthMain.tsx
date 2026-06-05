import React, { useEffect, useState } from "react";
import {
  View, Text, TouchableOpacity, ScrollView,
  StyleSheet, ActivityIndicator, Alert, Linking,
  Modal, FlatList,
} from "react-native";
import { Audio } from "expo-av";
import { Topic } from "../types/survey";
import { fetchTopic, fetchMySurveys, fetchEssayArchive, fetchEssayDetail, fetchTopicArchive } from "../api/survey";
import YouthSurvey from "../components/YouthSurvey";

export default function YouthMain({ userId }: { userId: string }) {
  const [topic, setTopic] = useState<Topic | null>(null);
  const [aiResponse, setAiResponse] = useState("");
  const [isPlaying, setIsPlaying] = useState(false);
  const soundRef = React.useRef<Audio.Sound | null>(null);

  // 모달 상태
  const [modalType, setModalType] = useState<"my-surveys" | "essay-archive" | "topic-archive" | null>(null);
  const [mySurveys, setMySurveys] = useState<any[]>([]);
  const [essayArchive, setEssayArchive] = useState<any[]>([]);
  const [topicArchive, setTopicArchive] = useState<any[]>([]);
  const [selectedEssay, setSelectedEssay] = useState<any>(null);
  const [loadingModal, setLoadingModal] = useState(false);

  useEffect(() => {
    loadTopic();
    return () => { soundRef.current?.unloadAsync(); };
  }, []);

  const loadTopic = async () => {
    const data = await fetchTopic(userId);
    setTopic(data);
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

  const handleCrisis = (level: string) => {
    Alert.alert(
      "괜찮으신가요?",
      "힘든 감정이 느껴질 때 혼자 참지 않아도 됩니다. 1393 정신건강 위기상담전화로 언제든 연락할 수 있습니다.",
      [
        { text: "괜찮아요", style: "cancel" },
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
              {modalType === "my-surveys" ? "내 기록" :
               modalType === "essay-archive" ? "이번 주 수필" :
               modalType === "topic-archive" ? "공감하기" : ""}
            </Text>
          </View>

          {loadingModal && <ActivityIndicator size="large" color="#7B7BFF" style={{ marginTop: 40 }} />}

          {!loadingModal && modalType === "my-surveys" && (
            <FlatList
              data={mySurveys}
              keyExtractor={(item) => item.topic_id}
              renderItem={({ item }) => (
                <View style={styles.modalCard}>
                  <Text style={styles.modalCardTitle}>{item.topic_title}</Text>
                  {item.responses.map((r: any, idx: number) => (
                    <View key={idx} style={{ marginTop: 8 }}>
                      {r.selected_option_label && (
                        <Text style={styles.modalText}>✓ {r.selected_option_label}</Text>
                      )}
                      {r.narrative_text && (
                        <Text style={styles.modalText}>📝 {r.narrative_text}</Text>
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
                  <Text style={styles.modalCardTitle}>{item.topic_title}</Text>
                  <Text style={styles.modalMeta}>
                    {item.active_week} · {item.contributor_cnt}명의 이야기
                  </Text>
                </TouchableOpacity>
              )}
            />
          )}

          {!loadingModal && modalType === "essay-archive" && selectedEssay && (
            <ScrollView>
              <View style={styles.modalCard}>
                <Text style={[styles.modalCardTitle, { fontSize: 18 }]}>{selectedEssay.title}</Text>
                <Text style={styles.modalText}>{selectedEssay.content}</Text>
              </View>
            </ScrollView>
          )}

          {!loadingModal && modalType === "topic-archive" && (
            <FlatList
              data={topicArchive}
              keyExtractor={(item) => item.topic_id}
              renderItem={({ item }) => (
                <View style={styles.modalCard}>
                  <Text style={styles.modalCardTitle}>{item.title}</Text>
                  <Text style={styles.modalMeta}>
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

      {/* 하단 메뉴: 3개 버튼 */}
      <View style={styles.bottomMenu}>
        <TouchableOpacity style={styles.menuBtn} onPress={openEssayArchive}>
          <Text style={styles.menuText}>📖 이번 주 수필</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.menuBtn} onPress={openMySurveys}>
          <Text style={styles.menuText}>✨ 내 기록</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.menuBtn} onPress={openTopicArchive}>
          <Text style={styles.menuText}>🌐 공감하기</Text>
        </TouchableOpacity>
      </View>

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
  topicSource: { color: "#666", fontSize: 12, marginBottom: 16 },
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
});
