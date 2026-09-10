import { useQuery } from "@tanstack/react-query";
import {
  Camera,
  Clock3,
  Gauge,
  MapPin,
  ShieldCheck,
} from "lucide-react";
import { useEffect } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { api } from "../api";
import { Empty, ErrorState, Loading, Status, formatDate } from "../components";
import { useWorkspace } from "../state";

export function TimelinePage() {
  const { caseId = "" } = useParams();
  const [params] = useSearchParams();
  const { selectedId, setSelectedId } = useWorkspace();
  const query = useQuery({
    queryKey: ["timeline", caseId],
    queryFn: () => api.timeline(caseId),
  });
  useEffect(() => {
    const id = params.get("evidence");
    if (id) setSelectedId(id);
  }, [params, setSelectedId]);
  if (query.isLoading) return <Loading />;
  if (query.error) return <ErrorState message={query.error.message} />;
  const items = query.data?.items ?? [];
  const withGps = items.filter(
    (item) =>
      item.metadata.gps_latitude !== null &&
      item.metadata.gps_longitude !== null,
  ).length;
  const findings = items.reduce((total, item) => total + item.finding_count, 0);
  const speeds = items.map((item) => item.derived_leg?.speed_kmh ?? 0);
  const maxSpeed = Math.max(...speeds, 1);
  return (
    <div className="workspace">
      <div className="workspace-heading">
        <div>
          <p className="eyebrow">CHRONOLOGY</p>
          <h1>Evidence timeline</h1>
          <p>
            Every row explains which timestamp was selected, where it came from,
            and what the next evidence leg means.
          </p>
        </div>
      </div>
      {items.length === 0 ? (
        <Empty
          title="Timeline unavailable"
          body="Add evidence to construct a qualified chronology."
        />
      ) : (
        <>
          <div className="timeline-summary">
            <div>
              <ShieldCheck size={18} />
              <strong>{items.length}</strong>
              <span>evidence events</span>
            </div>
            <div>
              <MapPin size={18} />
              <strong>{withGps}</strong>
              <span>with embedded GPS</span>
            </div>
            <div>
              <Gauge size={18} />
              <strong>{findings}</strong>
              <span>linked findings</span>
            </div>
            <div className="timeline-speed-chart">
              <span>Derived speed profile</span>
              <div>
                {speeds.map((speed, index) => (
                  <i
                    key={index}
                    style={{
                      height: `${Math.max(8, Math.min(100, (speed / maxSpeed) * 100))}%`,
                    }}
                    title={`${speed.toFixed(1)} km/h`}
                  />
                ))}
              </div>
            </div>
          </div>
          <div className="timeline-table-wrap">
            <table className="timeline-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Evidence & selected time</th>
                  <th>Source / confidence</th>
                  <th>
                    <Camera size={14} /> Camera
                  </th>
                  <th>
                    <MapPin size={14} /> GPS
                  </th>
                  <th>Derived leg</th>
                  <th>Review</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item, index) => (
                  <tr
                    key={item.id}
                    className={item.id === selectedId ? "selected" : ""}
                    onClick={() => setSelectedId(item.id)}
                  >
                    <td>
                      <span className="timeline-index-inline">{index + 1}</span>
                    </td>
                    <td>
                      <div className="timeline-evidence-cell">
                        <img
                          src={`/api/v1/evidence/${item.id}/thumbnail`}
                          alt=""
                        />
                        <div>
                          <strong>{item.evidence_id}</strong>
                          <small>{item.original_filename}</small>
                          <time>
                            <Clock3 size={13} />
                            {formatDate(
                              item.metadata.timeline_timestamp_utc ??
                                item.metadata.timeline_timestamp_raw,
                            )}
                          </time>
                        </div>
                      </div>
                    </td>
                    <td>
                      <Status
                        value={item.metadata.timeline_timestamp_confidence}
                      />
                      <small>
                        {item.metadata.timeline_timestamp_source.replaceAll(
                          "_",
                          " ",
                        )}
                      </small>
                      <small>
                        {item.metadata.timeline_timezone_status.replaceAll(
                          "_",
                          " ",
                        )}
                      </small>
                    </td>
                    <td>
                      <strong>{item.metadata.camera_make ?? "—"}</strong>
                      <small>{item.metadata.camera_model ?? "No model"}</small>
                    </td>
                    <td>
                      {item.metadata.gps_latitude !== null ? (
                        <>
                          <strong>
                            {item.metadata.gps_latitude.toFixed(5)},{" "}
                            {item.metadata.gps_longitude?.toFixed(5)}
                          </strong>
                          <small>embedded EXIF</small>
                        </>
                      ) : (
                        <span className="muted">No GPS</span>
                      )}
                    </td>
                    <td>
                      {item.derived_leg ? (
                        <>
                          <strong>
                            {item.derived_leg.distance_km.toFixed(1)} km
                          </strong>
                          <small>
                            {Math.round(item.derived_leg.interval_seconds / 60)}{" "}
                            min ·{" "}
                            {item.derived_leg.speed_kmh === null
                              ? "speed skipped"
                              : `${item.derived_leg.speed_kmh.toFixed(1)} km/h`}
                          </small>
                        </>
                      ) : (
                        <span className="muted">Start point</span>
                      )}
                    </td>
                    <td>
                      <span className="finding-count">
                        {item.finding_count}
                      </span>
                      <Link
                        to={`../evidence?evidence=${item.id}`}
                        onClick={(event) => event.stopPropagation()}
                      >
                        Inspect →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
