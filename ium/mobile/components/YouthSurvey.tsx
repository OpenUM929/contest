// mobile/components/YouthSurvey.tsx
// Phase 3: 청년용 동적 설문지 렌더링 (choice/narrative/mixed, 칩 UI, 텍스트 입력)

import React, { useState } from "react";
import {
  View, Text, TouchableOpacity, TextInput, ActivityIndicator, StyleSheet,
} from "react-native";
import { ChoiceOption } from "../types/survey";
import { useSurvey } from "../hooks/useSurvey";

interface YouthSurveyProps {
  topic: any;
  userId: string;
  topicId?: string;
  onSendStart?: () => void;
  onAiResponse?: (text: string) => void;
  onCrisis?: (level: string) => void;
}

export default function YouthSurvey({
  topic,
  userId,
  topicId,
  onSendStart,
  onAiResponse,
  onCrisis,
}: YouthSurveyProps) {
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

  const [inputText, setInputText] = useState("");
  const _tid = topicId || (topic?.id as string | undefined);

  const toggleChoice = (option: ChoiceOption) => {
    if (!currentQuestion) return;
    const existing = answers[currentQuestion.id];
    let selectedIds: string[] = [];
    let selectedLabels: string[] = [];

    if (existing?.selectedOptionId) {
      selectedIds = existing.selectedOptionId.split(",").filter(Boolean);
      selectedLabels = (existing.selectedOptionLabel || "").split("|||").filter(Boolean);
    }

    const idx = selectedIds.indexOf(option.id);
    if (idx >= 0) {
      selectedIds.splice(idx, 1);
      selectedLabels.splice(idx, 1);
    } else {
      if (!currentQuestion.allow_multiple && selectedIds.length > 0) {
        selectedIds = [option.id];
        selectedLabels = [option.label];
      } else {
        selectedIds.push(option.id);
        selectedLabels.push(option.label);
      }
    }

    if (selectedIds.length === 0) {
      setAnswer(currentQuestion.id, {
        questionId: currentQuestion.id,
        selectedOptionId: undefined,
        selectedOptionLabel: undefined,
      });
      return;
    }

    setAnswer(currentQuestion.id, {
      questionId: currentQuestion.id,
      selectedOptionId: selectedIds.join(","),
      selectedOptionLabel: selectedLabels.join("|||"),
    });
  };

  const isSelected = (option: ChoiceOption) => {
    if (!currentQuestion) return false;
    const ans = answers[currentQuestion.id];
    if (!ans?.selectedOptionId) return false;
    return ans.selectedOptionId.split(",").includes(option.id);
  };

  const handleNextOrSubmit = async () => {
    if (!currentQuestion || isSubmitting) return;

    if (currentQuestion.type === "narrative") {
      const text = inputText.trim();
      if (!text) return;
      setAnswer(currentQuestion.id, {
        questionId: currentQuestion.id,
        narrativeText: text,
      });
      await submitAnswers(userId, onSendStart, onAiResponse, onCrisis, _tid);
      setInputText("");
      return;
    }

    if (currentQuestion.type === "choice") {
      const ans = answers[currentQuestion.id];
      if (!ans?.selectedOptionId) return;
      const nextIdx = currentIndex + 1;
      if (nextIdx < questions.length) {
        nextQuestion();
      } else {
        await submitAnswers(userId, onSendStart, onAiResponse, onCrisis, _tid);
      }
    }
  };

  const canSubmit = (): boolean => {
    if (!currentQuestion) return false;
    if (currentQuestion.type === "choice") {
      return !!answers[currentQuestion.id]?.selectedOptionId;
    }
    if (currentQuestion.type === "narrative") {
      return inputText.trim().length > 0;
    }
    return false;
  };

  if (!currentQuestion || completed) {
    return (
      <View style={styles.center}>
        {isSubmitting ? <ActivityIndicator size="large" color="#7B7BFF" /> : null}
        {completed ? <Text style={styles.doneText}>답변을 전달했습니다.</Text> : null}
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.questionNumber}>
        질문 {currentIndex + 1} / {questions.length}
      </Text>
      <Text style={styles.questionText}>{currentQuestion.text}</Text>

      {currentQuestion.type === "choice" && currentQuestion.options && (
        <View style={styles.choiceRow}>
          {currentQuestion.options.map((opt) => (
            <TouchableOpacity
              key={opt.id}
              style={[
                styles.choiceChip,
                isSelected(opt) && styles.choiceChipSelected,
              ]}
              onPress={() => toggleChoice(opt)}
              activeOpacity={0.7}
              disabled={isSubmitting}
            >
              <Text
                style={[
                  styles.choiceChipText,
                  isSelected(opt) && styles.choiceChipTextSelected,
                ]}
              >
                {opt.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      )}

      {currentQuestion.type === "narrative" && (
        <TextInput
          style={styles.input}
          placeholder={
            currentQuestion.placeholder || "자유롭게 써주세요  (익명으로 기록됩니다)"
          }
          placeholderTextColor="#666"
          multiline
          value={inputText}
          onChangeText={setInputText}
          editable={!isSubmitting}
        />
      )}

      <TouchableOpacity
        style={[styles.sendBtn, (!canSubmit() || isSubmitting) && styles.sendBtnDisabled]}
        onPress={handleNextOrSubmit}
        disabled={!canSubmit() || isSubmitting}
      >
        {isSubmitting ? (
          <ActivityIndicator color="#FFF" size="small" />
        ) : (
          <Text style={styles.sendText}>
            {currentIndex < questions.length - 1 ? "다음" : "전달하기"}
          </Text>
        )}
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { marginTop: 16 },
  center: { alignItems: "center", marginTop: 40 },
  doneText: { color: "#E8E8FF", fontWeight: "bold", fontSize: 16 },
  questionNumber: { color: "#7B7BFF", fontSize: 13, marginBottom: 8 },
  questionText: {
    color: "#CCC",
    fontSize: 15,
    lineHeight: 24,
    fontWeight: "bold",
    marginBottom: 16,
  },
  choiceRow: { flexDirection: "row", flexWrap: "wrap", gap: 8, marginBottom: 16 },
  choiceChip: {
    backgroundColor: "#0F3460",
    borderRadius: 20,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: "#1A4A7A",
  },
  choiceChipSelected: { backgroundColor: "#7B7BFF", borderColor: "#7B7BFF" },
  choiceChipText: { color: "#AAA", fontSize: 13 },
  choiceChipTextSelected: { color: "#FFF", fontWeight: "bold" },
  input: {
    backgroundColor: "#16213E",
    borderRadius: 16,
    padding: 16,
    color: "#EEE",
    fontSize: 15,
    minHeight: 100,
    textAlignVertical: "top",
    marginBottom: 12,
  },
  sendBtn: {
    backgroundColor: "#7B7BFF",
    borderRadius: 12,
    padding: 14,
    alignItems: "center",
  },
  sendBtnDisabled: { opacity: 0.4 },
  sendText: { color: "#FFF", fontWeight: "bold", fontSize: 15 },
});
