import React, { useEffect, useState } from "react";
import { ActivityIndicator, View } from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import ConsentScreen from "./screens/ConsentScreen";
import ElderlyMain from "./screens/ElderlyMain";
import YouthMain from "./screens/YouthMain";
import LoginScreen from "./screens/LoginScreen";

export default function App() {
  const [ready, setReady] = useState(false);
  const [consented, setConsented] = useState(false);
  const [loggedIn, setLoggedIn] = useState(false);
  const [userId, setUserId] = useState("");
  const [userType, setUserType] = useState<"elder" | "youth">("elder");

  useEffect(() => {
    Promise.all([
      AsyncStorage.getItem("consent_done"),
      AsyncStorage.getItem("temp_user_id"),
      AsyncStorage.getItem("temp_user_type"),
    ]).then(([consent, uid, utype]) => {
      if (consent === "true") setConsented(true);
      if (uid && utype) {
        setUserId(uid);
        setUserType(utype as "elder" | "youth");
        setLoggedIn(true);
      }
    }).finally(() => setReady(true));
  }, []);

  const handleLogin = async (uid: string, utype: string) => {
    await AsyncStorage.setItem("temp_user_id", uid);
    await AsyncStorage.setItem("temp_user_type", utype);
    setUserId(uid);
    setUserType(utype as "elder" | "youth");
    setLoggedIn(true);
  };

  const handleLogout = async () => {
    await AsyncStorage.multiRemove(["temp_user_id", "temp_user_type", "consent_done"]);
    setLoggedIn(false);
    setConsented(false);
    setUserId("");
  };

  const handleConsentComplete = async () => {
    await AsyncStorage.setItem("consent_done", "true");
    setConsented(true);
  };

  if (!ready) {
    return (
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
        <ActivityIndicator size="large" color="#E8572A" />
      </View>
    );
  }

  if (!loggedIn) {
    return <LoginScreen onLogin={handleLogin} />;
  }

  if (!consented) {
    return <ConsentScreen userId={userId} onComplete={handleConsentComplete} />;
  }

  if (userType === "elder") {
    return <ElderlyMain userId={userId} onLogout={handleLogout} />;
  }
  return <YouthMain userId={userId} onLogout={handleLogout} />;
}
