/** @jsxImportSource react */
import React, { useEffect, useMemo, useState } from "react";
import { Globe3D, type GlobeMarker } from "@/components/ui/3d-globe";
import countries from "world-countries";
import { fetchGlobalGasolinePrices } from "@/api";
import gasolineCsv from "@/assets/global_gasoline_prices.csv?raw";

type GasRow = { country: string; price: number; measure: string };

// Marker 点在 `3d-globe.tsx` 内渲染；这里给一个透明占位，避免加载真实图片资源
const TRANSPARENT_PIXEL =
  "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==";

function normalizeCountryName(name: string) {
  return name
    .trim()
    .replace(/\s+/g, " ")
    .replace(/\(.*?\)/g, "")
    .replace(/&/g, "and")
    .trim();
}

function parseGasCsv(text: string): GasRow[] {
  const lines = text.split(/\r?\n/).filter(Boolean);
  const header = lines.shift();
  if (!header) return [];
  const cols = header.split(",");
  const idxCountry = cols.indexOf("country");
  const idxPrice = cols.indexOf("current_price");
  const idxMeasure = cols.indexOf("measure");
  if (idxCountry < 0 || idxPrice < 0) return [];

  const rows: GasRow[] = [];
  for (const line of lines) {
    const parts = line.split(",");
    const country = parts[idxCountry]?.trim();
    const rawPrice = parts[idxPrice];
    const measure = parts[idxMeasure] || "";
    const price = Number(rawPrice);
    if (!country || !Number.isFinite(price)) continue;
    // 过滤异常：只展示 USD/Liter；像 Indonesia 那种不带 measure 的跳过
    if (measure && !/USD\/Liter/i.test(measure)) continue;
    if (price <= 0 || price > 10) continue;
    rows.push({ country, price, measure: measure || "USD/Liter" });
  }
  return rows;
}

function findLatLng(countryName: string): { lat: number; lng: number } | null {
  const n = normalizeCountryName(countryName).toLowerCase();
  const alias: Record<string, string> = {
    usa: "united states",
    "united states of america": "united states",
    "burma": "myanmar",
    "ivory coast": "côte d'ivoire",
    "czech republic": "czechia",
    macedonia: "north macedonia",
    swaziland: "eswatini",
    "south korea": "korea",
    "hong kong": "hong kong",
    curacao: "curaçao",
  };
  const key = alias[n] ?? n;
  const hit = (countries as any[]).find((c) => {
    const common = String(c?.name?.common || "").toLowerCase();
    const official = String(c?.name?.official || "").toLowerCase();
    const alts: string[] = Array.isArray(c?.altSpellings) ? c.altSpellings : [];
    return (
      common === key ||
      official === key ||
      alts.some((a) => String(a).toLowerCase() === key)
    );
  });
  const latlng = hit?.latlng;
  if (!Array.isArray(latlng) || latlng.length < 2) return null;
  return { lat: Number(latlng[0]), lng: Number(latlng[1]) };
}

export default function AceternityGlobeReact() {
  const [hoverText, setHoverText] = useState<string>("");
  const [mousePos, setMousePos] = useState<{ x: number; y: number }>({
    x: 0,
    y: 0,
  });
  const [remoteRows, setRemoteRows] = useState<GasRow[] | null>(null);
  const [latestFetchedAt, setLatestFetchedAt] = useState<string>("");

  useEffect(() => {
    let alive = true;
    fetchGlobalGasolinePrices()
      .then((payload) => {
        if (!alive) return;
        const items = Array.isArray(payload?.items) ? payload.items : [];
        const rows: GasRow[] = items
          .map((item: any) => ({
            country: String(item?.country || "").trim(),
            price: Number(item?.current_price),
            measure: String(item?.measure || "USD/Liter").trim(),
          }))
          .filter((item: GasRow) => item.country && Number.isFinite(item.price));
        setRemoteRows(rows);
        setLatestFetchedAt(String(payload?.latest_fetched_at || "").trim());
      })
      .catch(() => {
        if (!alive) return;
        setRemoteRows(null);
        setLatestFetchedAt("");
      });
    return () => {
      alive = false;
    };
  }, []);

  const { markers, priceByLabel } = useMemo(() => {
    const rows = remoteRows?.length ? remoteRows : parseGasCsv(gasolineCsv);
    // 全量展示（约 170 条）；仍按价格排序，点位分布更稳定
    const top = [...rows].sort((a, b) => b.price - a.price);
    const map = new Map<string, string>();
    const mk: GlobeMarker[] = [];
    for (const r of top) {
      const pos = findLatLng(r.country);
      if (!pos) continue;
      const label = r.country;
      map.set(label, `${r.country}：$${r.price.toFixed(3)} / L`);
      mk.push({
        lat: pos.lat,
        lng: pos.lng,
        src: TRANSPARENT_PIXEL,
        label,
      });
    }
    return { markers: mk, priceByLabel: map };
  }, [remoteRows]);

  return (
    <div className="react-globe-panel">
      <div className="react-globe-head">
        <div className="panel-title-row">
          <span className="panel-tag">GLOBE</span>
          <span className="panel-title">全球节点</span>
          <span className="panel-hint">（鼠标悬停即可获得各地区油价）</span>
          {latestFetchedAt ? (
            <span className="panel-hint">数据更新时间：{latestFetchedAt}</span>
          ) : null}
        </div>
      </div>
      <div
        className="react-globe-canvas-wrap"
        style={{ position: "relative" }}
        onMouseMove={(e) => {
          const rect = (e.currentTarget as HTMLDivElement).getBoundingClientRect();
          setMousePos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
        }}
      >
        <Globe3D
          className="react-globe-canvas"
          markers={markers}
          config={{
            radius: 1.35,
            atmosphereColor: "#4da6ff",
            atmosphereIntensity: 1.2,
            atmosphereBlur: 4,
            bumpScale: 2.2,
            autoRotateSpeed: 0.3,
            showAtmosphere: false,
            ambientIntensity: 0.45,
            pointLightIntensity: 2.2,
            showWireframe: false,
            enableZoom: false,
            enablePan: false,
          }}
          onMarkerHover={(m) => {
            const txt = m?.label ? priceByLabel.get(m.label) || "" : "";
            setHoverText(txt);
          }}
        />
        {hoverText ? (
          <div
            style={{
              position: "absolute",
              left: mousePos.x + 12,
              top: mousePos.y + 12,
              padding: "6px 10px",
              borderRadius: 10,
              border: "1px solid rgba(56,189,248,0.28)",
              background: "rgba(2,6,23,0.78)",
              color: "#bae6fd",
              fontSize: 12,
              pointerEvents: "none",
              maxWidth: "calc(100% - 24px)",
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
              transform: "translateZ(0)",
            }}
          >
            {hoverText}
          </div>
        ) : null}
      </div>
    </div>
  );
}
