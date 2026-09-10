import { useQuery } from "@tanstack/react-query";
import {
  EyeOff,
  Gauge,
  LockKeyhole,
  MapPin,
  Route as RouteIcon,
  Ruler,
  Wind,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { api } from "../api";
import { Button, Empty, ErrorState, Loading } from "../components";
import { useWorkspace } from "../state";

export function MapPage() {
  const { caseId = "" } = useParams();
  const [params] = useSearchParams();
  const { selectedId, setSelectedId } = useWorkspace();
  const [redacted, setRedacted] = useState(true);
  const query = useQuery({
    queryKey: ["map", caseId, redacted],
    queryFn: () => api.map(caseId, redacted),
  });
  useEffect(() => {
    const id = params.get("evidence");
    if (id) setSelectedId(id);
  }, [params, setSelectedId]);
  const points = useMemo(() => query.data?.points ?? [], [query.data?.points]);
  const plotted = useMemo(() => {
    if (!points.length) return [];
    const lats = points.map((p) => p.latitude),
      lons = points.map((p) => p.longitude);
    const minLat = Math.min(...lats),
      maxLat = Math.max(...lats),
      minLon = Math.min(...lons),
      maxLon = Math.max(...lons);
    return points.map((p) => ({
      ...p,
      x: 10 + (80 * (p.longitude - minLon)) / (maxLon - minLon || 1),
      y: 90 - (80 * (p.latitude - minLat)) / (maxLat - minLat || 1),
    }));
  }, [points]);
  const routeKm = useMemo(
    () =>
      plotted.slice(1).reduce((total, p, index) => {
        const a = points[index]!;
        const b = points[index + 1]!;
        const rad = (n: number) => (n * Math.PI) / 180;
        const dLat = rad(b.latitude - a.latitude),
          dLon = rad(b.longitude - a.longitude);
        const h =
          Math.sin(dLat / 2) ** 2 +
          Math.cos(rad(a.latitude)) *
            Math.cos(rad(b.latitude)) *
            Math.sin(dLon / 2) ** 2;
        return total + 6371 * 2 * Math.atan2(Math.sqrt(h), Math.sqrt(1 - h));
      }, 0),
    [points, plotted],
  );
  const outlier = points.length
    ? Math.max(...points.map((p) => p.latitude)) -
        Math.min(...points.map((p) => p.latitude)) >
      10
    : false;
  return (
    <div className="workspace">
      <div className="workspace-heading">
        <div>
          <p className="eyebrow">LOCATION WORKSPACE</p>
          <h1>Map & derived route</h1>
          <p>
            Understand where each frame sits in the route, which points are
            selected, and where an unusual jump occurs.
          </p>
        </div>
        <Button
          variant="secondary"
          icon={redacted ? EyeOff : MapPin}
          onClick={() => setRedacted(!redacted)}
        >
          {redacted ? "Show precise coordinates" : "Redact coordinates"}
        </Button>
      </div>
      <div className="privacy-notice">
        <LockKeyhole size={18} />
        <div>
          <strong>Local map-style view</strong>
          <p>
            This offline map has road, water, grid, legend, compass, scale, and
            route statistics. Coordinates never leave the local application.
          </p>
        </div>
      </div>
      {query.isLoading ? (
        <Loading />
      ) : query.error ? (
        <ErrorState message={query.error.message} />
      ) : !points.length ? (
        <Empty
          title="No GPS metadata is available"
          body="Images with usable coordinates will appear here in selected timeline order."
        />
      ) : (
        <>
          <div className="map-stats">
            <div>
              <RouteIcon size={17} />
              <strong>{points.length}</strong>
              <span>mapped points</span>
            </div>
            <div>
              <Ruler size={17} />
              <strong>{routeKm.toFixed(1)} km</strong>
              <span>route span</span>
            </div>
            <div>
              <Gauge size={17} />
              <strong>{outlier ? "Review jump" : "Consistent"}</strong>
              <span>route signal</span>
            </div>
            <div>
              <Wind size={17} />
              <strong>{redacted ? "Rounded" : "Precise"}</strong>
              <span>coordinate display</span>
            </div>
          </div>
          <div className="map-layout">
            <section
              className="coordinate-canvas polished-map"
              aria-label="Offline map-style route plot"
            >
              <svg
                viewBox="0 0 100 100"
                role="img"
                aria-label={`Map-style route with ${points.length} coordinate markers`}
              >
                <defs>
                  <pattern
                    id="map-grid"
                    width="8"
                    height="8"
                    patternUnits="userSpaceOnUse"
                  >
                    <path
                      d="M 8 0 L 0 0 0 8"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth=".12"
                    />
                  </pattern>
                  <linearGradient id="terrain" x1="0" x2="1" y1="0" y2="1">
                    <stop offset="0" stopColor="var(--surface-2)" />
                    <stop offset="1" stopColor="var(--surface-3)" />
                  </linearGradient>
                </defs>
                <rect width="100" height="100" fill="url(#terrain)" />
                <rect width="100" height="100" fill="url(#map-grid)" />
                <path
                  d="M0 24 C18 10 28 34 45 22 S78 8 100 18 L100 0 L0 0Z"
                  fill="var(--primary-soft)"
                  opacity=".65"
                />
                <path
                  d="M0 78 C17 66 32 88 48 72 S75 58 100 70"
                  fill="none"
                  stroke="var(--line-strong)"
                  strokeWidth="2"
                  opacity=".7"
                />
                <path
                  d="M4 92 C22 72 32 45 58 35 S83 18 96 6"
                  fill="none"
                  stroke="var(--surface)"
                  strokeWidth="4"
                  opacity=".85"
                />
                <path
                  d="M4 92 C22 72 32 45 58 35 S83 18 96 6"
                  fill="none"
                  stroke="var(--line-strong)"
                  strokeWidth=".65"
                />
                <polyline
                  points={plotted.map((p) => `${p.x},${p.y}`).join(" ")}
                  fill="none"
                  stroke="var(--primary)"
                  strokeWidth="1.1"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                {plotted.map((p, index) => (
                  <g
                    key={p.evidence_file_id}
                    onClick={() => setSelectedId(p.evidence_file_id)}
                    className={
                      p.evidence_file_id === selectedId
                        ? "marker selected"
                        : "marker"
                    }
                    tabIndex={0}
                    role="button"
                    aria-label={`Select ${p.evidence_id}`}
                  >
                    <circle
                      cx={p.x}
                      cy={p.y}
                      r={p.evidence_file_id === selectedId ? 3.8 : 2.6}
                    />
                    <text x={p.x} y={p.y + 0.9} textAnchor="middle">
                      {index + 1}
                    </text>
                  </g>
                ))}
                <text x="91" y="10" className="map-compass">
                  N
                </text>
                <path d="M91 13 l-1.5 4 h3z" fill="var(--ink)" />
              </svg>
              <div className="map-overlay map-scale">
                <span>Scale</span>
                <b>────</b>
                <small>10 km</small>
              </div>
              <div className="map-overlay map-key">
                <span className="map-key-dot" /> Evidence route{" "}
                <span className="map-key-warning" /> Review jump
              </div>
            </section>
            <aside className="map-legend">
              <div className="map-legend-head">
                <div>
                  <p className="eyebrow">ROUTE ORDER</p>
                  <strong>{points.length} GPS-linked frames</strong>
                </div>
                <span className="map-legend-badge">
                  {outlier ? "Review" : "Stable"}
                </span>
              </div>
              {points.map((point, index) => (
                <button
                  key={point.evidence_file_id}
                  className={
                    point.evidence_file_id === selectedId ? "selected" : ""
                  }
                  onClick={() => setSelectedId(point.evidence_file_id)}
                >
                  <span>{index + 1}</span>
                  <div>
                    <strong>{point.evidence_id}</strong>
                    <small>
                      {point.latitude.toFixed(redacted ? 2 : 5)},{" "}
                      {point.longitude.toFixed(redacted ? 2 : 5)}
                      {redacted ? " · rounded" : ""}
                    </small>
                  </div>
                </button>
              ))}
              <Link
                className="text-link"
                to={`../evidence?evidence=${selectedId ?? ""}`}
              >
                Inspect selected evidence →
              </Link>
            </aside>
          </div>
        </>
      )}
    </div>
  );
}
