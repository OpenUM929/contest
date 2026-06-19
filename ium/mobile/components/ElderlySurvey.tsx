// mobile/components/ElderlySurvey.tsx
// Phase 3: 노인용 동적 설문지 렌더링 (choice/narrative/mixed, 음성 입력)

import React, { useState, useRef } from "react";
import {
  View, Text, TouchableOpacity, ActivityIndicator, StyleSheet,
} from "react-native";
import { Audio } from "expo-av";
import axios from "axios";
import { ChoiceOption } from "../types/survey";
import { useSurvey } from "../hooks/useSurvey";

const API_BASE = process.env.EXPO_PUBLIC_API_URL || "http://localhost:8000";

interface ElderlySurveyProps {
  topic: any;
  userId: string;
  fontSize: number;
  topicId?: string;
  onSendStart?: () => void;
  onAiResponse?: (text: string) => void;
  onCrisis?: (level: string) => void;
}

export default function ElderlySurvey({
  topic,
  userId,
  fontSize,
  topicId,
  onSendStart,
  onAiResponse,
  onCrisis,
}: ElderlySurveyProps) {
  const {
    questions,
    currentQuestion,
    currentIndex,
    answers,
    isSubmitting,
    completed,
    setAnswer,
    nextQuestion,
    submitAnswers,
  } = useSurvey(topic);

  const [isRecording, setIsRecording] = useState(false);
  const recordingRef = useRef<Audio.Recording | null>(null);

  const _tid = topicId || (topic?.id as string | undefined);

  const handleChoiceSelect = async (option: ChoiceOption) => {
    if (!currentQuestion || isSubmitting) return;

    setAnswer(currentQuestion.id, {
      questionId: currentQuestion.id,
      selectedOptionId: option.id,
      selectedOptionLabel: option.label,
    });

    // mixed이고 다음 질문이 narrative이면 narrative로 이동 (추가 음성 유도)
    const nextIdx = currentIndex + 1;
    if (nextIdx < questions.length && questions[nextIdx].type === "narrative") {
      nextQuestion();
      return;
    }

    // 그 외에는 바로 전송
    await submitAnswers(userId, onSendStart, onAiResponse, onCrisis, _tid);
  };

  const startRecording = async () => {
    await Audio.requestPermissionsAsync();
    await Audio.setAudioModeAsync({ allowsRecordingIOS: true });
    const { recording } = await Audio.Recording.createAsync(
      Audio.RecordingOptionsPresets.HIGH_QUALITY
    );
    recordingRef.current = recording;
    setIsRecording(true);
  };

  const stopRecordingAndSubmit = async () => {
    setIsRecording(false);
    await recordingRef.current?.stopAndUnloadAsync();
    const uri = recordingRef.current?.getURI();
    if (!uri || !currentQuestion) return;

    // STT
    const formData = new FormData();
    formData.append("file", { uri, name: "audio.m4a", type: "audio/m4a" } as any);
    try {
      const sttRes = await axios.post(`${API_BASE}/chat/voice/stt`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      const userText = sttRes.data.text || "";

      setAnswer(currentQuestion.id, {
        questionId: currentQuestion.id,
        narrativeText: userText,
      });

      await submitAnswers(userId, onSendStart, onAiResponse, onCrisis, _tid);
    } catch (e) {
      console.error("STT failed", e);
    }
  };

  if (!currentQuestion || completed) {
    return (
      <View style={styles.center}>
        {isSubmitting ? (
          <ActivityIndicator size="large" color="#E8572A" />
        ) : completed ? (
          <Text style={[styles.doneText, { fontSize }]}>답변을 전달했습니다.</Text>
        ) : null}
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={[styles.questionNumber, { fontSize: fontSize - 4 }]}>
        질문 {currentIndex + 1} / {questions.length}
      </Text>
      <Text style={[styles.questionText, { fontSize }]}>{currentQuestion.text}</Text>

      {currentQuestion.type === "choice" && currentQuestion.options && (
        <View style={styles.choiceContainer}>
          {currentQuestion.options.map((opt) => (
            <TouchableOpacity
              key={opt.id}
              style={styles.choiceBtn}
              onPress={() => handleChoiceSelect(opt)}
              activeOpacity={0.7}
              disabled={isSubmitting}
            >
              <Text style={[styles.choiceText, { fontSize: fontSize - 2 }]}>
                {opt.icon_hint ? `${opt.icon_hint} ` : ""}{opt.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      )}

      {currentQuestion.type === "narrative" && (
        <TouchableOpacity
          style={[styles.micButton, isRecording && styles.micButtonActive]}
          onPressIn={startRecording}
          onPressOut={stopRecordingAndSubmit}
          activeOpacity={0.8}
          disabled={isSubmitting}
        >
          <Text style={styles.micIcon}>{isRecording ? "🔴" : "🎤"}</Text>
          <Text style={[styles.micLabel, { fontSize }]}>
            {isRecording ? "듣고 있어요..." : "누르고 말씀해 주세요"}
          </Text>
        </TouchableOpacity>
      )}

      {isSubmitting && <ActivityIndicator style={{ marginTop: 16 }} color="#E8572A" />}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { marginTop: 16 },
  center: { alignItems: "center", marginTop: 40 },
  doneText: { color: "#4A3728", fontWeight: "bold" },
  questionNumber: { color: "#888", marginBottom: 8 },
  questionText: { color: "#333", lineHeight: 32, fontWeight: "bold", marginBottom: 16 },
  choiceContainer: { gap: 10 },
  choiceBtn: {
    backgroundColor: "#FFF",
    borderRadius: 12,
    padding: 16,
    borderWidth: 2,
    borderColor: "#DDD",
    alignItems: "center",
  },
  choiceText: { color: "#333", fontWeight: "bold" },
  micButton: {
    backgroundColor: "#E8572A",
    borderRadius: 20,
    padding: 24,
    alignItems: "center",
    marginTop: 8,
    elevation: 4,
  },
  micButtonActive: { backgroundColor: "#CC3A0F" },
  micIcon: { fontSize: 48, marginBottom: 8 },
  micLabel: { color: "#FFF", fontWeight: "bold" },
});
