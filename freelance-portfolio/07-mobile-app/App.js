import React, { useEffect, useState } from "react";
import { SafeAreaView, View, Text, TextInput, TouchableOpacity, FlatList, StyleSheet, Alert } from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { CATEGORIES, addTx, summary, tl } from "./src/logic";

const KEY = "butce:v1";

export default function App() {
  const [list, setList] = useState([]);
  const [amount, setAmount] = useState("");
  const [category, setCategory] = useState(CATEGORIES[0]);
  const [type, setType] = useState("gider");

  useEffect(() => { AsyncStorage.getItem(KEY).then(v => v && setList(JSON.parse(v))); }, []);
  useEffect(() => { AsyncStorage.setItem(KEY, JSON.stringify(list)); }, [list]);

  const s = summary(list);
  const save = () => {
    try { setList(addTx(list, { amount, category, type })); setAmount(""); }
    catch (e) { Alert.alert("Hata", e.message); }
  };

  return (
    <SafeAreaView style={st.c}>
      <Text style={st.h}>Bu Ay</Text>
      <View style={st.row}>
        <Card label="Gelir" value={tl(s.gelir)} color="#2a9d8f" />
        <Card label="Gider" value={tl(s.gider)} color="#e76f51" />
        <Card label="Bakiye" value={tl(s.bakiye)} color="#264653" />
      </View>
      {Object.entries(s.byCat).map(([k, v]) => (
        <View key={k} style={st.barWrap}>
          <Text style={st.barLabel}>{k}</Text>
          <View style={[st.bar, { flex: v / (s.gider || 1) }]} />
          <Text style={st.barVal}>{tl(v)}</Text>
        </View>
      ))}
      <View style={st.row}>
        {["gider", "gelir"].map(t => (
          <TouchableOpacity key={t} onPress={() => setType(t)} style={[st.chip, type === t && st.chipOn]}>
            <Text style={type === t && st.chipOnT}>{t === "gider" ? "Gider" : "Gelir"}</Text>
          </TouchableOpacity>))}
      </View>
      <View style={[st.row, { flexWrap: "wrap" }]}>
        {CATEGORIES.map(c => (
          <TouchableOpacity key={c} onPress={() => setCategory(c)} style={[st.chip, category === c && st.chipOn]}>
            <Text style={category === c && st.chipOnT}>{c}</Text>
          </TouchableOpacity>))}
      </View>
      <View style={st.row}>
        <TextInput style={st.in} keyboardType="decimal-pad" placeholder="Tutar" value={amount} onChangeText={setAmount} />
        <TouchableOpacity style={st.btn} onPress={save}><Text style={{ color: "#fff", fontWeight: "700" }}>Ekle</Text></TouchableOpacity>
      </View>
      <FlatList data={list} keyExtractor={i => i.id} renderItem={({ item }) => (
        <TouchableOpacity onLongPress={() => setList(list.filter(x => x.id !== item.id))} style={st.item}>
          <Text>{item.category}</Text>
          <Text style={{ color: item.type === "gelir" ? "#2a9d8f" : "#e76f51" }}>{item.type === "gelir" ? "+" : "-"}{tl(item.amount)}</Text>
        </TouchableOpacity>)} />
    </SafeAreaView>
  );
}
const Card = ({ label, value, color }) => (
  <View style={[st.card, { backgroundColor: color }]}><Text style={st.cl}>{label}</Text><Text style={st.cv}>{value}</Text></View>
);
const st = StyleSheet.create({
  c: { flex: 1, padding: 16, backgroundColor: "#f7f7f7" }, h: { fontSize: 24, fontWeight: "800", marginVertical: 8 },
  row: { flexDirection: "row", gap: 8, marginVertical: 6 }, card: { flex: 1, borderRadius: 12, padding: 10 },
  cl: { color: "#fff", opacity: .85 }, cv: { color: "#fff", fontWeight: "700" },
  barWrap: { flexDirection: "row", alignItems: "center", gap: 6, marginVertical: 2 }, barLabel: { width: 70 },
  bar: { height: 10, backgroundColor: "#e76f51", borderRadius: 5 }, barVal: { width: 90, textAlign: "right" },
  chip: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 16, backgroundColor: "#e5e5e5" },
  chipOn: { backgroundColor: "#264653" }, chipOnT: { color: "#fff" },
  in: { flex: 1, backgroundColor: "#fff", borderRadius: 10, padding: 10 }, btn: { backgroundColor: "#264653", borderRadius: 10, padding: 12 },
  item: { flexDirection: "row", justifyContent: "space-between", padding: 12, backgroundColor: "#fff", marginVertical: 3, borderRadius: 8 },
});
