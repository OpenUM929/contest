import React, { useState } from "react";
import {
  View, Text, TouchableOpacity, TextInput,
  StyleSheet, ActivityIndicator, KeyboardAvoidingView, Platform,
} from "react-native";
import axios from "axios";

const API_BASE = process.env.EXPO_PUBLIC_API_URL || "http://localhost:8000";

interface LoginScreenProps {
  onLogin: (userId: string, userType: string) => void;
}

export default function LoginScreen({ onLogin }: LoginScreenProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async () => {
    if (!email.trim() || !password) {
      setError("이메일과 비밀번호를 입력하세요.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const { data } = await axios.post(`${API_BASE}/api/auth/login`, {
        email: email.trim(),
        password: password,
      });
      onLogin(data.user_id, data.user_type);
    } catch (e: any) {
      setError(e.response?.data?.detail || "로그인에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <View style={styles.card}>
        <Text style={styles.logo}>이음(以音)</Text>
        <Text style={styles.subtitle}>세대를 잇는 따뜻한 이야기</Text>

        <Text style={styles.label}>이메일</Text>
        <TextInput
          style={styles.input}
          value={email}
          onChangeText={setEmail}
          placeholder="admin@ium.kr"
          placeholderTextColor="#AAA"
          autoCapitalize="none"
          autoCorrect={false}
          keyboardType="email-address"
          returnKeyType="next"
        />

        <Text style={styles.label}>비밀번호</Text>
        <TextInput
          style={styles.input}
          value={password}
          onChangeText={setPassword}
          placeholder="비밀번호 입력"
          placeholderTextColor="#AAA"
          secureTextEntry
          returnKeyType="go"
          onSubmitEditing={handleLogin}
        />

        {error !== "" && (
          <Text style={styles.errorText}>{error}</Text>
        )}

        <TouchableOpacity
          style={[styles.loginBtn, loading && styles.loginBtnDisabled]}
          onPress={handleLogin}
          disabled={loading}
          activeOpacity={0.8}
        >
          {loading ? (
            <ActivityIndicator color="#FFF" size="small" />
          ) : (
            <Text style={styles.loginBtnText}>로그인</Text>
          )}
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#FFFDF7",
    justifyContent: "center",
    alignItems: "center",
    padding: 32,
  },
  card: {
    width: "100%",
    maxWidth: 360,
    backgroundColor: "#FFF8EE",
    borderRadius: 20,
    padding: 32,
    elevation: 4,
  },
  logo: {
    fontSize: 32,
    fontWeight: "bold",
    color: "#4A3728",
    textAlign: "center",
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: "#888",
    textAlign: "center",
    marginBottom: 32,
  },
  label: {
    fontSize: 14,
    color: "#666",
    marginBottom: 8,
  },
  input: {
    width: "100%",
    padding: 14,
    fontSize: 15,
    borderWidth: 2,
    borderColor: "#DDD",
    borderRadius: 12,
    backgroundColor: "#FFF",
    color: "#333",
    marginBottom: 16,
  },
  errorText: {
    color: "#E8572A",
    fontSize: 13,
    marginBottom: 8,
    textAlign: "center",
  },
  loginBtn: {
    backgroundColor: "#E8572A",
    borderRadius: 12,
    padding: 16,
    alignItems: "center",
    marginTop: 8,
  },
  loginBtnDisabled: {
    opacity: 0.4,
  },
  loginBtnText: {
    color: "#FFF",
    fontSize: 18,
    fontWeight: "bold",
  },
});
