import { useEffect, useState, type ReactNode } from "react";
import axios from "axios";
import {
  Activity,
  AlertTriangle,
  Bell,
  CheckCircle2,
  Droplets,
  Filter,
  Gauge,
  Menu,
  RefreshCw,
  ShieldCheck,
  Thermometer,
  Waves,
  XCircle,
  ChevronRight,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

import "./App.css";

const API_URL = "http://127.0.0.1:8000/api/v1";
const DEVICE_ID = 1;

interface AlertItem {
  id: number;
  type: string;
  severity: string;
  title: string;
  message: string;
  parameter: string | null;
  measured_value: number | null;
  threshold_value: number | null;
  created_at: string;
}

interface DashboardData {
  device: {
    id: number;
    uid: string;
    name: string;
    location: string;
    latitude: number | null;
    longitude: number | null;
    firmware_version: string | null;
    is_online: boolean;
    last_seen_at: string | null;
  };

  water_quality: {
    status: string;
    is_safe: boolean;
    reason: string | null;
    pH: number | null;
    turbidity: number | null;
    tds: number | null;
    temperature: number | null;
    evaluated_at: string | null;
  };

  alerts: {
    active_count: number;
    items: AlertItem[];
  };

  treatment: {
    id: number | null;
    status: string;
    cycle_uid: string | null;
    source_volume_liters: number | null;
    started_at: string | null;
  };

  filter: {
    status: string;
    filter_type: string | null;
    remaining_days: number | null;
    flow_rate_lpm: number | null;
    pressure_drop: number | null;
    replacement_required: boolean;
    replacement_reason: string | null;
  };

  maintenance: {
    id: number;
    type: string;
    description: string;
    status: string;
    scheduled_at: string | null;
    performed_at: string | null;
    next_due_at: string | null;
  } | null;

  telemetry: {
    total_readings: number;
  };
}

interface Reading {
  id: number;
  sensor_id: number;
  device_id: number;
  value: number;
  unit: string;
  recorded_at: string;
  quality_status: string | null;
}

interface HistoryResponse {
  readings: Reading[];
  total: number;
}

type Page =
  | "overview"
  | "water-quality"
  | "filter"
  | "treatment"
  | "alerts"
  | "maintenance";

const emptyData: DashboardData = {
  device: {
    id: 1,
    uid: "SIH26040-001",
    name: "Smart Water Unit 001",
    location: "Jharkhand Rural Test Site",
    latitude: null,
    longitude: null,
    firmware_version: null,
    is_online: false,
    last_seen_at: null,
  },

  water_quality: {
    status: "no_data",
    is_safe: false,
    reason: "Waiting for sensor data",
    pH: null,
    turbidity: null,
    tds: null,
    temperature: null,
    evaluated_at: null,
  },

  alerts: {
    active_count: 0,
    items: [],
  },

  treatment: {
    id: null,
    status: "idle",
    cycle_uid: null,
    source_volume_liters: null,
    started_at: null,
  },

  filter: {
    status: "unknown",
    filter_type: null,
    remaining_days: null,
    flow_rate_lpm: null,
    pressure_drop: null,
    replacement_required: false,
    replacement_reason: null,
  },

  maintenance: null,

  telemetry: {
    total_readings: 0,
  },
};

function App() {
  const [page, setPage] =
    useState<Page>("overview");

  const [data, setData] =
    useState<DashboardData>(emptyData);

  const [history, setHistory] =
    useState<Reading[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [backendError, setBackendError] =
    useState(false);

  const [menuOpen, setMenuOpen] =
    useState(false);

  const [treatmentActionLoading, setTreatmentActionLoading] =
    useState(false);

  const [treatmentError, setTreatmentError] =
    useState<string | null>(null);

  const startTreatment = async (
    sourceVolume: number,
  ) => {
    try {
      setTreatmentActionLoading(true);
      setTreatmentError(null);

      await axios.post(
        `${API_URL}/treatment/devices/${DEVICE_ID}/start`,
        {
          source_volume_liters: sourceVolume,
        },
      );

      await loadDashboard();
    } catch (error: any) {
      console.error("Start treatment error:", error);
      setTreatmentError(
        error?.response?.data?.detail ||
          "Unable to start treatment cycle.",
      );
    } finally {
      setTreatmentActionLoading(false);
    }
  };

  const completeTreatment = async (
    cycleId: number,
    purifiedVolume: number,
  ) => {
    try {
      setTreatmentActionLoading(true);
      setTreatmentError(null);

      await axios.post(
        `${API_URL}/treatment/cycles/${cycleId}/complete`,
        null,
        {
          params: {
            purified_volume_liters: purifiedVolume,
          },
        },
      );

      await loadDashboard();
    } catch (error: any) {
      console.error("Complete treatment error:", error);
      setTreatmentError(
        error?.response?.data?.detail ||
          "Unable to complete treatment cycle.",
      );
    } finally {
      setTreatmentActionLoading(false);
    }
  };

  const failTreatment = async (
    cycleId: number,
    reason: string,
  ) => {
    try {
      setTreatmentActionLoading(true);
      setTreatmentError(null);

      await axios.post(
        `${API_URL}/treatment/cycles/${cycleId}/fail`,
        null,
        {
          params: {
            failure_reason: reason,
          },
        },
      );

      await loadDashboard();
    } catch (error: any) {
      console.error("Fail treatment error:", error);
      setTreatmentError(
        error?.response?.data?.detail ||
          "Unable to fail treatment cycle.",
      );
    } finally {
      setTreatmentActionLoading(false);
    }
  };

  const loadDashboard = async () => {
    try {
      setLoading(true);

      const response =
        await axios.get<DashboardData>(
          `${API_URL}/dashboard/devices/${DEVICE_ID}`,
        );

      setData(response.data);
      setBackendError(false);
    } catch (error) {
      console.error(
        "Dashboard API error:",
        error,
      );

      setBackendError(true);
    } finally {
      setLoading(false);
    }
  };

  const loadHistory = async () => {
    try {
      const response =
        await axios.get<HistoryResponse>(
          `${API_URL}/telemetry/devices/${DEVICE_ID}/history`,
          {
            params: {
              limit: 100,
            },
          },
        );

      setHistory(response.data.readings);
    } catch (error) {
      console.error(
        "Telemetry history error:",
        error,
      );
    }
  };

  const refreshAll = async () => {
    await Promise.all([
      loadDashboard(),
      loadHistory(),
    ]);
  };

  useEffect(() => {
    refreshAll();

    const timer =
      window.setInterval(
        refreshAll,
        10000,
      );

    return () =>
      window.clearInterval(timer);
  }, []);

  const navigate = (nextPage: Page) => {
    setPage(nextPage);
    setMenuOpen(false);
  };

  return (
    <div className="app-shell">

      {menuOpen && (
        <div
          className="mobile-overlay"
          onClick={() =>
            setMenuOpen(false)
          }
        />
      )}

      <aside
        className={`sidebar ${
          menuOpen
            ? "sidebar-open"
            : ""
        }`}
      >

        <div className="brand">

          <div className="brand-icon">
            <Droplets size={24} />
          </div>

          <div>
            <div className="brand-name">
              SmartWater
            </div>

            <div className="brand-subtitle">
              SIH26040
            </div>
          </div>

        </div>

        <div className="sidebar-section-title">
          MONITORING
        </div>

        <nav className="navigation">

          <NavItem
            icon={<Activity size={18} />}
            label="Overview"
            active={
              page === "overview"
            }
            onClick={() =>
              navigate("overview")
            }
          />

          <NavItem
            icon={<Waves size={18} />}
            label="Water Quality"
            active={
              page === "water-quality"
            }
            onClick={() =>
              navigate(
                "water-quality",
              )
            }
          />

          <NavItem
            icon={<Filter size={18} />}
            label="Filter Health"
            active={
              page === "filter"
            }
            onClick={() =>
              navigate("filter")
            }
          />

          <NavItem
            icon={<Gauge size={18} />}
            label="Treatment"
            active={
              page === "treatment"
            }
            onClick={() =>
              navigate("treatment")
            }
          />

          <NavItem
            icon={<Bell size={18} />}
            label="Alerts"
            active={
              page === "alerts"
            }
            badge={
              data.alerts.active_count
            }
            onClick={() =>
              navigate("alerts")
            }
          />

          <NavItem
            icon={
              <RefreshCw size={18} />
            }
            label="Maintenance"
            active={
              page === "maintenance"
            }
            onClick={() =>
              navigate(
                "maintenance",
              )
            }
          />

        </nav>

        <div className="sidebar-device">

          <div className="sidebar-device-label">
            CONNECTED DEVICE
          </div>

          <div className="sidebar-device-name">
            {data.device.uid}
          </div>

          <div className="connection-status">

            <span
              className={`status-dot ${
                data.device.is_online
                  ? "online"
                  : "offline"
              }`}
            />

            {data.device.is_online
              ? "System Online"
              : "System Offline"}

          </div>

        </div>

      </aside>

      <main className="main-content">

        <header className="topbar">

          <div className="header-left">

            <button
              className="mobile-menu-button"
              onClick={() =>
                setMenuOpen(true)
              }
            >
              <Menu size={21} />
            </button>

            <div>

              <div className="eyebrow">
                SMART WATER PURIFICATION
              </div>

              <h1>
                {getPageTitle(page)}
              </h1>

            </div>

          </div>

          <div className="header-right">

            <div className="live-indicator">

              <span
                className={`status-dot ${
                  data.device.is_online
                    ? "online"
                    : "offline"
                }`}
              />

              {data.device.is_online
                ? "LIVE"
                : "OFFLINE"}

            </div>

            <button
              className="refresh-button"
              onClick={refreshAll}
            >
              <RefreshCw
                size={17}
                className={
                  loading
                    ? "spin"
                    : ""
                }
              />
            </button>

          </div>

        </header>

        <div className="dashboard">

          {backendError && (
            <div className="warning-banner">

              <AlertTriangle
                size={18}
              />

              <div>
                <strong>
                  Backend connection unavailable
                </strong>

                <span>
                  Start FastAPI on port
                  8000 to receive live
                  sensor data.
                </span>
              </div>

            </div>
          )}

          {page === "overview" && (
            <OverviewPage
              data={data}
              navigate={navigate}
            />
          )}

          {page ===
            "water-quality" && (
            <WaterQualityPage
              data={data}
              history={history}
            />
          )}

          {page === "filter" && (
            <FilterPage
              data={data}
            />
          )}

          {page === "treatment" && (
            <TreatmentPage
              data={data}
              onStart={startTreatment}
              onComplete={completeTreatment}
              onFail={failTreatment}
              actionLoading={treatmentActionLoading}
              error={treatmentError}
            />
          )}

          {page === "alerts" && (
            <AlertsPage
              data={data}
            />
          )}

          {page ===
            "maintenance" && (
            <MaintenancePage
              data={data}
            />
          )}

        </div>

      </main>

    </div>
  );
}


/* ============================================================
   OVERVIEW
============================================================ */

function OverviewPage({
  data,
  navigate,
}: {
  data: DashboardData;
  navigate: (page: Page) => void;
}) {
  const quality =
    data.water_quality;

  return (
    <>

      <section className="device-header">

        <div>

          <div className="section-label">
            DEVICE
          </div>

          <h2>
            {data.device.name}
          </h2>

          <p>
            {data.device.location}
          </p>

        </div>

        <div className="device-meta">

          <div>
            <span>DEVICE ID</span>

            <strong>
              {data.device.uid}
            </strong>
          </div>

          <div>
            <span>TELEMETRY</span>

            <strong>
              {data.telemetry.total_readings}
            </strong>
          </div>

        </div>

      </section>

      <section className="quality-grid">

        <div
          className={`quality-card ${
            quality.is_safe
              ? "safe"
              : "unsafe"
          }`}
        >

          <div className="quality-card-top">

            <div>

              <div className="section-label">
                WATER QUALITY
              </div>

              <div className="quality-title">

                {quality.is_safe ? (
                  <CheckCircle2
                    size={30}
                  />
                ) : (
                  <XCircle
                    size={30}
                  />
                )}

                <h2>
                  {quality.status ===
                  "insufficient_data"
                    ? "Insufficient Data"
                    : quality.is_safe
                      ? "Water is Safe"
                      : "Water is Unsafe"}
                </h2>

              </div>

            </div>

            <div
              className={`quality-badge ${
                quality.is_safe
                  ? "safe"
                  : "unsafe"
              }`}
            >
              {quality.is_safe
                ? "SAFE"
                : "ACTION REQUIRED"}
            </div>

          </div>

          <p className="quality-reason">
            {quality.reason ||
              "No quality evaluation available."}
          </p>

          <div className="sensor-grid">

            <SensorCard
              icon={<Waves size={18} />}
              label="pH"
              value={quality.pH}
              unit=""
              range="Safe: 6.5 – 8.5"
              safe={
                quality.pH !== null &&
                quality.pH >= 6.5 &&
                quality.pH <= 8.5
              }
            />

            <SensorCard
              icon={
                <Droplets size={18} />
              }
              label="Turbidity"
              value={quality.turbidity}
              unit="NTU"
              range="Maximum 5 NTU"
              safe={
                quality.turbidity !== null &&
                quality.turbidity <= 5
              }
            />

            <SensorCard
              icon={<Gauge size={18} />}
              label="TDS"
              value={quality.tds}
              unit="ppm"
              range="Maximum 500 ppm"
              safe={
                quality.tds !== null &&
                quality.tds <= 500
              }
            />

            <SensorCard
              icon={
                <Thermometer
                  size={18}
                />
              }
              label="Temperature"
              value={quality.temperature}
              unit="°C"
              range="Live sensor"
              safe={
                quality.temperature !==
                null
              }
            />

          </div>

        </div>

        <div className="panel">

          <div className="panel-heading">

            <div>

              <div className="section-label">
                SYSTEM
              </div>

              <h3>
                Device Status
              </h3>

            </div>

            <Activity
              size={20}
              className="muted-icon"
            />

          </div>

          <div className="status-list">

            <StatusRow
              label="Connection"
              value={
                data.device.is_online
                  ? "Online"
                  : "Offline"
              }
              positive={
                data.device.is_online
              }
            />

            <StatusRow
              label="Location"
              value={
                data.device.location
              }
            />

            <StatusRow
              label="Firmware"
              value={
                data.device
                  .firmware_version ||
                "Not reported"
              }
            />

            <StatusRow
              label="Readings"
              value={`${data.telemetry.total_readings} total`}
            />

            <StatusRow
              label="Last Seen"
              value={
                formatDate(
                  data.device
                    .last_seen_at,
                )
              }
            />

          </div>

        </div>

      </section>

      <section className="three-column">

        <ClickableInfoPanel
          icon={
            <ShieldCheck size={21} />
          }
          label="WATER SAFETY"
          value={
            quality.is_safe
              ? "Protected"
              : "At Risk"
          }
          description={
            quality.is_safe
              ? "All configured parameters are within safe limits."
              : quality.reason ||
                "Water requires attention."
          }
          type={
            quality.is_safe
              ? "success"
              : "danger"
          }
          onClick={() =>
            navigate(
              "water-quality",
            )
          }
        />

        <ClickableInfoPanel
          icon={
            <Filter size={21} />
          }
          label="FILTER HEALTH"
          value={
            data.filter.status ===
            "unknown"
              ? "Not Configured"
              : data.filter.status
          }
          description={
            data.filter
              .remaining_days !== null
              ? `${data.filter.remaining_days} days estimated remaining`
              : "Filter health data unavailable."
          }
          type={
            data.filter
              .replacement_required
              ? "danger"
              : "neutral"
          }
          onClick={() =>
            navigate("filter")
          }
        />

        <ClickableInfoPanel
          icon={
            <Gauge size={21} />
          }
          label="TREATMENT"
          value={capitalize(
            data.treatment.status,
          )}
          description={
            data.treatment.cycle_uid
              ? `Cycle ${data.treatment.cycle_uid}`
              : "No active treatment cycle."
          }
          type="neutral"
          onClick={() =>
            navigate("treatment")
          }
        />

      </section>

            <section className="analytics-section">
        <div className="panel analytics-panel">
          <div className="panel-heading">
            <div>
              <div className="section-label">
                SMART ANALYTICS
              </div>

              <h3>
                System Health Overview
              </h3>
            </div>

            <ShieldCheck
              size={20}
              className="muted-icon"
            />
          </div>

          <div className="analytics-grid">
            <AnalyticsCard
              icon={<ShieldCheck size={20} />}
              label="WATER QUALITY SCORE"
              value={`${calculateWaterScore(data)}%`}
              description={
                quality.is_safe
                  ? "All monitored parameters are within configured limits."
                  : "One or more monitored parameters require attention."
              }
              type={
                quality.is_safe
                  ? "success"
                  : "danger"
              }
            />

            <AnalyticsCard
              icon={<CheckCircle2 size={20} />}
              label="SAFE PARAMETERS"
              value={`${getSafeParameterCount(data)} / 4`}
              description="pH, turbidity, TDS and temperature monitoring."
              type={
                getSafeParameterCount(data) === 4
                  ? "success"
                  : "danger"
              }
            />

            <AnalyticsCard
              icon={<AlertTriangle size={20} />}
              label="RISK LEVEL"
              value={getRiskLevel(data)}
              description={
                data.alerts.active_count > 0
                  ? `${data.alerts.active_count} active safety event${
                      data.alerts.active_count > 1
                        ? "s"
                        : ""
                    } detected.`
                  : "No active safety events detected."
              }
              type={
                data.alerts.active_count > 0
                  ? "danger"
                  : "success"
              }
            />

            <AnalyticsCard
              icon={<Activity size={20} />}
              label="TELEMETRY HEALTH"
              value={
                data.device.is_online
                  ? "ONLINE"
                  : "OFFLINE"
              }
              description={
                data.device.is_online
                  ? `${data.telemetry.total_readings} readings received from the device.`
                  : "Device is not currently reporting telemetry."
              }
              type={
                data.device.is_online
                  ? "success"
                  : "danger"
              }
            />
          </div>

          <div className="analytics-summary">
            <div className="analytics-summary-icon">
              {quality.is_safe ? (
                <CheckCircle2 size={21} />
              ) : (
                <AlertTriangle size={21} />
              )}
            </div>

            <div>
              <strong>
                {getSystemInsight(data)}
              </strong>

              <p>
                SmartWater continuously evaluates sensor
                telemetry, treatment status, filter condition
                and safety events for device{" "}
                {data.device.uid}.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="lower-grid">

        <div className="panel">

          <div className="panel-heading">

            <div>

              <div className="section-label">
                SAFETY EVENTS
              </div>

              <h3>
                Active Alerts
              </h3>

            </div>

            <div className="alert-count">
              {data.alerts.active_count}
            </div>

          </div>

          {data.alerts.items.length ===
          0 ? (
            <div className="empty-state">

              <CheckCircle2
                size={30}
              />

              <strong>
                No active alerts
              </strong>

              <span>
                System is operating
                normally.
              </span>

            </div>
          ) : (
            <div className="alert-list">

              {data.alerts.items.map(
                (alert) => (
                  <AlertRow
                    key={alert.id}
                    alert={alert}
                  />
                ),
              )}

            </div>
          )}

        </div>

        <div className="panel">

          <div className="panel-heading">

            <div>

              <div className="section-label">
                PURIFICATION
              </div>

              <h3>
                Treatment Cycle
              </h3>

            </div>

            <Droplets
              size={20}
              className="muted-icon"
            />

          </div>

          <div className="treatment-box">

            <div className="treatment-status">

              <span
                className={`status-dot ${
                  data.treatment.status ===
                  "started"
                    ? "online"
                    : "neutral"
                }`}
              />

              <strong>
                {capitalize(
                  data.treatment.status,
                )}
              </strong>

            </div>

            {data.treatment.cycle_uid ? (
              <>
                <div className="cycle-id">
                  {
                    data.treatment
                      .cycle_uid
                  }
                </div>

                <div className="cycle-detail">
                  Started{" "}
                  {formatDate(
                    data.treatment
                      .started_at,
                  )}
                </div>
              </>
            ) : (
              <div className="cycle-detail">
                No active treatment
                cycle.
              </div>
            )}

          </div>

          <div className="maintenance-mini">

            <div className="maintenance-icon">
              <RefreshCw
                size={17}
              />
            </div>

            <div>

              <span>
                LAST MAINTENANCE
              </span>

              <strong>
                {data.maintenance
                  ?.description ||
                  "No maintenance record"}
              </strong>

            </div>

          </div>

        </div>

      </section>

    </>
  );
}


/* ============================================================
   WATER QUALITY PAGE
============================================================ */

function WaterQualityPage({
  data,
  history,
}: {
  data: DashboardData;
  history: Reading[];
}) {
  const quality =
    data.water_quality;

  const chartData = buildChartData(
    history,
  );

  return (
    <>

      <section className="page-intro">

        <div>

          <div className="section-label">
            LIVE ANALYTICS
          </div>

          <h2>
            Water Quality Analysis
          </h2>

          <p>
            Real sensor telemetry from{" "}
            {data.device.uid}
          </p>

        </div>

        <div className="live-pill">

          <span className="status-dot online" />

          AUTO REFRESH

        </div>

      </section>

      <section className="quality-summary-grid">

        <QualityMetric
          label="pH"
          value={quality.pH}
          unit=""
          safe={
            quality.pH !== null &&
            quality.pH >= 6.5 &&
            quality.pH <= 8.5
          }
          limit="6.5 – 8.5"
        />

        <QualityMetric
          label="Turbidity"
          value={quality.turbidity}
          unit="NTU"
          safe={
            quality.turbidity !== null &&
            quality.turbidity <= 5
          }
          limit="≤ 5 NTU"
        />

        <QualityMetric
          label="TDS"
          value={quality.tds}
          unit="ppm"
          safe={
            quality.tds !== null &&
            quality.tds <= 500
          }
          limit="≤ 500 ppm"
        />

        <QualityMetric
          label="Temperature"
          value={
            quality.temperature
          }
          unit="°C"
          safe={
            quality.temperature !==
            null
          }
          limit="Live"
        />

      </section>

      <section className="chart-grid">

        <TelemetryChart
          title="pH Trend"
          data={chartData}
          dataKey="pH"
          unit="pH"
          domain={[6, 9]}
          safeMin={6.5}
          safeMax={8.5}
        />

        <TelemetryChart
          title="Turbidity Trend"
          data={chartData}
          dataKey="turbidity"
          unit="NTU"
          domain={[0, "auto"]}
          safeMax={5}
        />

        <TelemetryChart
          title="TDS Trend"
          data={chartData}
          dataKey="tds"
          unit="ppm"
          domain={[0, "auto"]}
          safeMax={500}
        />

        <TelemetryChart
          title="Temperature Trend"
          data={chartData}
          dataKey="temperature"
          unit="°C"
          domain={["auto", "auto"]}
        />

      </section>

      <section className="panel quality-explanation">

        <div className="panel-heading">

          <div>

            <div className="section-label">
              QUALITY ASSESSMENT
            </div>

            <h3>
              Current Evaluation
            </h3>

          </div>

          {quality.is_safe ? (
            <CheckCircle2
              className="success-icon"
              size={22}
            />
          ) : (
            <AlertTriangle
              className="danger-icon"
              size={22}
            />
          )}

        </div>

        <div className="assessment-box">

          <div
            className={`assessment-status ${
              quality.is_safe
                ? "success"
                : "danger"
            }`}
          >
            {quality.is_safe
              ? "SAFE"
              : "UNSAFE"}
          </div>

          <div>

            <strong>
              {quality.reason ||
                "No evaluation available"}
            </strong>

            <p>
              Evaluated{" "}
              {formatDate(
                quality.evaluated_at,
              )}
            </p>

          </div>

        </div>

      </section>

    </>
  );
}


/* ============================================================
   CHART
============================================================ */

function TelemetryChart({
  title,
  data,
  dataKey,
  unit,
  domain,
  safeMin,
  safeMax,
}: {
  title: string;
  data: ChartPoint[];
  dataKey: keyof ChartPoint;
  unit: string;
  domain: [number | string, number | string];
  safeMin?: number;
  safeMax?: number;
}) {
  return (
    <div className="panel chart-panel">

      <div className="panel-heading">

        <div>

          <div className="section-label">
            TELEMETRY
          </div>

          <h3>
            {title}
          </h3>

        </div>

        <Activity
          size={18}
          className="muted-icon"
        />

      </div>

      {data.length === 0 ? (
        <div className="chart-empty">
          No telemetry history available.
        </div>
      ) : (
        <div className="chart-wrapper">

          <ResponsiveContainer
            width="100%"
            height={250}
          >

            <LineChart
              data={data}
              margin={{
                top: 5,
                right: 12,
                left: -20,
                bottom: 5,
              }}
            >

              <CartesianGrid
                strokeDasharray="3 3"
                stroke="rgba(255,255,255,0.06)"
              />

              <XAxis
                dataKey="time"
                stroke="#52647b"
                tick={{
                  fontSize: 9,
                }}
              />

              <YAxis
                domain={domain}
                stroke="#52647b"
                tick={{
                  fontSize: 9,
                }}
              />

              <Tooltip
                contentStyle={{
                  background:
                    "#0b1728",
                  border:
                    "1px solid rgba(255,255,255,0.1)",
                  borderRadius: 10,
                  color: "#e2e8f0",
                  fontSize: 11,
                }}
                formatter={(value) => [
                  `${Number(value).toFixed(2)} ${unit}`,
                  title,
                ]}
              />

              <Line
                type="monotone"
                dataKey={dataKey}
                stroke="#22d3ee"
                strokeWidth={2}
                dot={false}
                activeDot={{
                  r: 4,
                }}
                connectNulls
              />

            </LineChart>

          </ResponsiveContainer>

        </div>
      )}

      <div className="chart-limit">

        {safeMin !== undefined && (
          <span>
            Minimum safe: {safeMin}
          </span>
        )}

        {safeMax !== undefined && (
          <span>
            Maximum safe: {safeMax}
          </span>
        )}

      </div>

    </div>
  );
}


/* ============================================================
   OTHER PAGES
============================================================ */

function FilterPage({
  data,
}: {
  data: DashboardData;
}) {
  const filter = data.filter;

  const remainingDays = filter.remaining_days;
  const filterHealthy =
    filter.status !== "unknown" &&
    !filter.replacement_required;

  const lifePercent =
    remainingDays !== null
      ? Math.max(0, Math.min(100, (remainingDays / 180) * 100))
      : 0;

  const maintenanceMessage = filter.replacement_required
    ? filter.replacement_reason ||
      "Filter replacement or service is required."
    : remainingDays !== null && remainingDays <= 30
      ? "Filter service is approaching. Plan maintenance soon."
      : "No immediate replacement required. Continue monitoring filter performance.";

  const maintenanceType = filter.replacement_required
    ? "danger"
    : remainingDays !== null && remainingDays <= 30
      ? "warning"
      : "success";

  return (
    <>
      <PageIntro
        label="FILTRATION SYSTEM"
        title="Filter Health"
        description={`Filter condition for ${data.device.uid}`}
      />

      <section className="three-column filter-summary-grid">
        <InfoPanel
          icon={<Filter size={21} />}
          label="HEALTH STATUS"
          value={
            filter.status === "unknown"
              ? "Not Configured"
              : capitalize(filter.status)
          }
          description={
            filter.replacement_required
              ? filter.replacement_reason || "Replacement required."
              : "No replacement warning reported."
          }
          type={filter.replacement_required ? "danger" : "success"}
        />

        <InfoPanel
          icon={<Activity size={21} />}
          label="FLOW RATE"
          value={
            filter.flow_rate_lpm !== null
              ? `${filter.flow_rate_lpm} L/min`
              : "--"
          }
          description="Current reported flow rate."
          type="neutral"
        />

        <InfoPanel
          icon={<Gauge size={21} />}
          label="PRESSURE DROP"
          value={
            filter.pressure_drop !== null
              ? `${filter.pressure_drop}`
              : "--"
          }
          description="Current reported pressure drop."
          type="neutral"
        />
      </section>

      <section className="filter-health-main-grid">
        <section className="panel filter-life-panel">
          <div className="panel-heading">
            <div>
              <span className="panel-eyebrow">PREDICTIVE MONITORING</span>
              <h3>Filter Life</h3>
            </div>
            <Filter size={20} />
          </div>

          <div className="filter-life-content">
            <div className="filter-life-number">
              {remainingDays !== null ? remainingDays : "--"}
              <span>{remainingDays !== null ? "days" : ""}</span>
            </div>

            <p className="filter-life-caption">
              Estimated remaining service life
            </p>

            <div className="filter-life-track">
              <div
                className={`filter-life-fill ${
                  lifePercent <= 20 ? "danger" : lifePercent <= 45 ? "warning" : ""
                }`}
                style={{ width: `${lifePercent}%` }}
              />
            </div>

            <div className="filter-life-scale">
              <span>0 days</span>
              <span>90 days</span>
              <span>180 days</span>
            </div>

            <div className="filter-condition-row">
              <span>Current condition</span>
              <strong className={filterHealthy ? "healthy-text" : "danger-text"}>
                {filter.status === "unknown"
                  ? "Not Configured"
                  : capitalize(filter.status)}
              </strong>
            </div>
          </div>
        </section>

        <section className="panel filter-performance-panel">
          <div className="panel-heading">
            <div>
              <span className="panel-eyebrow">PERFORMANCE</span>
              <h3>Filter Monitoring</h3>
            </div>
            <Activity size={20} />
          </div>

          <div className="filter-performance-list">
            <StatusRow
              label="Flow Rate"
              value={
                filter.flow_rate_lpm !== null
                  ? `${filter.flow_rate_lpm} L/min`
                  : "--"
              }
            />
            <StatusRow
              label="Pressure Drop"
              value={
                filter.pressure_drop !== null
                  ? `${filter.pressure_drop}`
                  : "--"
              }
            />
            <StatusRow
              label="Replacement"
              value={filter.replacement_required ? "Required" : "Not Required"}
            />
            <StatusRow
              label="Monitoring"
              value={filter.status === "unknown" ? "Inactive" : "Active"}
            />
          </div>
        </section>
      </section>

      <section className={`panel filter-recommendation ${maintenanceType}`}>
        <div className="filter-recommendation-icon">
          {filter.replacement_required ? (
            <AlertTriangle size={21} />
          ) : (
            <CheckCircle2 size={21} />
          )}
        </div>

        <div className="filter-recommendation-content">
          <span className="panel-eyebrow">MAINTENANCE RECOMMENDATION</span>
          <h3>
            {filter.replacement_required
              ? "Filter service required"
              : remainingDays !== null && remainingDays <= 30
                ? "Filter service approaching"
                : "Filter operating normally"}
          </h3>
          <p>{maintenanceMessage}</p>
        </div>

        <div className="filter-monitoring-badge">
          {filter.status === "unknown" ? "NOT CONFIGURED" : "MONITORING ACTIVE"}
        </div>
      </section>
    </>
  );
}

function TreatmentPage({
  data,
  onStart,
  onComplete,
  onFail,
  actionLoading,
  error,
}: {
  data: DashboardData;
  onStart: (sourceVolume: number) => Promise<void>;
  onComplete: (
    cycleId: number,
    purifiedVolume: number,
  ) => Promise<void>;
  onFail: (
    cycleId: number,
    reason: string,
  ) => Promise<void>;
  actionLoading: boolean;
  error: string | null;
}) {
  const treatment = data.treatment;

  const [sourceVolume, setSourceVolume] =
    useState("100");

  const [purifiedVolume, setPurifiedVolume] =
    useState("90");

  const [failureReason, setFailureReason] =
    useState(
      "Treatment cycle failed during purification",
    );

  const active = treatment.status === "started";

  return (
    <>
      <PageIntro
        label="PURIFICATION CONTROL"
        title="Treatment"
        description="Control and monitor the water purification cycle."
      />

      {error && (
        <div className="treatment-error">
          <AlertTriangle size={17} />
          <span>{error}</span>
        </div>
      )}

      {!active ? (
        <section className="treatment-control-grid">
          <div className="panel treatment-main-card">
            <div className="panel-heading">
              <div>
                <div className="section-label">
                  CURRENT STATUS
                </div>
                <h3>Treatment Ready</h3>
              </div>

              <div className="treatment-idle-badge">
                IDLE
              </div>
            </div>

            <div className="treatment-start-area">
              <div className="treatment-large-icon">
                <Droplets size={38} />
              </div>

              <h2>Start Purification</h2>

              <p>
                Begin a new treatment cycle for the
                connected SmartWater unit.
              </p>

              <label className="treatment-input-label">
                SOURCE WATER VOLUME
              </label>

              <div className="treatment-input-wrap">
                <input
                  type="number"
                  min="1"
                  value={sourceVolume}
                  onChange={(event) =>
                    setSourceVolume(event.target.value)
                  }
                />
                <span>LITERS</span>
              </div>

              <button
                className="primary-treatment-button"
                disabled={
                  actionLoading ||
                  Number(sourceVolume) <= 0
                }
                onClick={() =>
                  onStart(Number(sourceVolume))
                }
              >
                {actionLoading ? (
                  <>
                    <RefreshCw
                      size={17}
                      className="spin"
                    />
                    STARTING...
                  </>
                ) : (
                  <>
                    <Droplets size={17} />
                    START TREATMENT
                  </>
                )}
              </button>
            </div>
          </div>

          <div className="panel">
            <div className="panel-heading">
              <div>
                <div className="section-label">
                  PROCESS
                </div>
                <h3>Treatment Workflow</h3>
              </div>

              <Activity
                size={20}
                className="muted-icon"
              />
            </div>

            <div className="workflow">
              <WorkflowStep
                number="01"
                title="Source Water"
                description="Measure and register incoming water volume."
                active
              />

              <WorkflowStep
                number="02"
                title="Purification"
                description="Water passes through the treatment system."
              />

              <WorkflowStep
                number="03"
                title="Quality Check"
                description="Sensor readings verify the treated water."
              />

              <WorkflowStep
                number="04"
                title="Complete"
                description="Store the final treatment result."
              />
            </div>
          </div>
        </section>
      ) : (
        <section className="treatment-control-grid">
          <div className="panel treatment-running-card">
            <div className="panel-heading">
              <div>
                <div className="section-label">
                  TREATMENT IN PROGRESS
                </div>
                <h3>Purification Active</h3>
              </div>

              <div className="treatment-running-badge">
                <span className="status-dot online" />
                RUNNING
              </div>
            </div>

            <div className="running-cycle">
              <div className="running-icon">
                <Droplets size={32} />
              </div>

              <div>
                <span>CYCLE ID</span>
                <strong>
                  {treatment.cycle_uid || "--"}
                </strong>
              </div>
            </div>

            <div className="cycle-stats">
              <div>
                <span>SOURCE VOLUME</span>
                <strong>
                  {treatment.source_volume_liters ??
                    "--"}{" "}
                  L
                </strong>
              </div>

              <div>
                <span>STARTED</span>
                <strong>
                  {formatDate(treatment.started_at)}
                </strong>
              </div>

              <div>
                <span>DEVICE</span>
                <strong>{data.device.uid}</strong>
              </div>
            </div>

            <div className="treatment-complete-area">
              <label className="treatment-input-label">
                PURIFIED WATER VOLUME
              </label>

              <div className="treatment-input-wrap">
                <input
                  type="number"
                  min="0"
                  value={purifiedVolume}
                  onChange={(event) =>
                    setPurifiedVolume(
                      event.target.value,
                    )
                  }
                />
                <span>LITERS</span>
              </div>

              <label
                className="treatment-input-label"
                style={{ marginTop: "14px" }}
              >
                FAILURE REASON
              </label>

              <div className="treatment-input-wrap">
                <input
                  type="text"
                  value={failureReason}
                  onChange={(event) =>
                    setFailureReason(
                      event.target.value,
                    )
                  }
                />
              </div>

              <div className="treatment-actions">
                <button
                  className="complete-treatment-button"
                  disabled={
                    actionLoading ||
                    treatment.id === null ||
                    Number(purifiedVolume) < 0
                  }
                  onClick={() => {
                    if (treatment.id !== null) {
                      onComplete(
                        treatment.id,
                        Number(purifiedVolume),
                      );
                    }
                  }}
                >
                  {actionLoading ? (
                    <>
                      <RefreshCw
                        size={16}
                        className="spin"
                      />
                      PROCESSING...
                    </>
                  ) : (
                    <>
                      <CheckCircle2 size={16} />
                      COMPLETE
                    </>
                  )}
                </button>

                <button
                  className="fail-treatment-button"
                  disabled={
                    actionLoading ||
                    treatment.id === null ||
                    !failureReason.trim()
                  }
                  onClick={() => {
                    if (treatment.id !== null) {
                      onFail(
                        treatment.id,
                        failureReason.trim(),
                      );
                    }
                  }}
                >
                  <XCircle size={16} />
                  FAIL CYCLE
                </button>
              </div>

              {treatment.id === null && (
                <div className="treatment-error">
                  <AlertTriangle size={15} />
                  <span>
                    Treatment cycle ID is not available
                    from the dashboard response yet.
                  </span>
                </div>
              )}
            </div>
          </div>

          <div className="panel">
            <div className="panel-heading">
              <div>
                <div className="section-label">
                  CYCLE MONITOR
                </div>
                <h3>Current Process</h3>
              </div>

              <Activity
                size={20}
                className="muted-icon"
              />
            </div>

            <div className="workflow">
              <WorkflowStep
                number="01"
                title="Source Water"
                description="Water volume registered."
                active
                complete
              />

              <WorkflowStep
                number="02"
                title="Purification"
                description="Treatment cycle is currently running."
                active
              />

              <WorkflowStep
                number="03"
                title="Quality Check"
                description="Awaiting treatment completion."
              />

              <WorkflowStep
                number="04"
                title="Complete"
                description="Final output will be recorded."
              />
            </div>
          </div>
        </section>
      )}
    </>
  );
}


function WorkflowStep({
  number,
  title,
  description,
  active = false,
  complete = false,
}: {
  number: string;
  title: string;
  description: string;
  active?: boolean;
  complete?: boolean;
}) {
  return (
    <div
      className={`workflow-step ${
        active ? "active" : ""
      } ${complete ? "complete" : ""}`}
    >
      <div className="workflow-number">
        {complete ? (
          <CheckCircle2 size={16} />
        ) : (
          number
        )}
      </div>

      <div>
        <strong>{title}</strong>
        <p>{description}</p>
      </div>
    </div>
  );
}

function AlertsPage({
  data,
}: {
  data: DashboardData;
}) {
  const [alerts, setAlerts] = useState(
    data.alerts.items,
  );

  const [activeCount, setActiveCount] =
    useState(
      data.alerts.active_count,
    );

  const handleResolved = (
    alertId: number,
  ) => {
    setAlerts((current) =>
      current.filter(
        (alert) => alert.id !== alertId,
      ),
    );

    setActiveCount((count) =>
      Math.max(0, count - 1),
    );
  };

  return (
    <>
      <PageIntro
        label="SAFETY EVENTS"
        title="Alerts"
        description="Current unresolved water-system alerts."
      />

      <section className="panel">
        <div className="panel-heading">
          <div>
            <div className="section-label">
              ACTIVE ALERTS
            </div>

            <h3>
              {activeCount} active
            </h3>
          </div>

          <Bell
            size={20}
            className="muted-icon"
          />
        </div>

        {alerts.length === 0 ? (
          <div className="empty-state">
            <CheckCircle2
              size={30}
            />

            <strong>
              No active alerts
            </strong>

            <span>
              The system is operating normally.
            </span>
          </div>
        ) : (
          <div className="alert-list">
            {alerts.map((alert) => (
              <AlertRow
                key={alert.id}
                alert={alert}
                onResolved={
                  handleResolved
                }
              />
            ))}
          </div>
        )}
      </section>
    </>
  );
}


function MaintenancePage({
  data,
}: {
  data: DashboardData;
}) {
  return (
    <>

      <PageIntro
        label="SERVICE MANAGEMENT"
        title="Maintenance"
        description="Maintenance history and service status."
      />

      <section className="panel">

        <div className="panel-heading">

          <div>

            <div className="section-label">
              LATEST RECORD
            </div>

            <h3>
              Maintenance
            </h3>

          </div>

          <RefreshCw
            size={20}
            className="muted-icon"
          />

        </div>

        {data.maintenance ? (
          <div className="maintenance-detail">

            <StatusRow
              label="Type"
              value={
                data.maintenance.type
              }
            />

            <StatusRow
              label="Description"
              value={
                data.maintenance
                  .description
              }
            />

            <StatusRow
              label="Status"
              value={
                data.maintenance.status
              }
              positive={
                data.maintenance
                  .status ===
                "completed"
              }
            />

            <StatusRow
              label="Performed"
              value={formatDate(
                data.maintenance
                  .performed_at,
              )}
            />

            <StatusRow
              label="Next Due"
              value={formatDate(
                data.maintenance
                  .next_due_at,
              )}
            />

          </div>
        ) : (
          <div className="empty-state">
            <RefreshCw size={30} />

            <strong>
              No maintenance records
            </strong>

            <span>
              No service record is currently available.
            </span>
          </div>
        )}

      </section>

    </>
  );
}


/* ============================================================
   COMPONENTS
============================================================ */

function NavItem({
  icon,
  label,
  active = false,
  badge,
  onClick,
}: {
  icon: ReactNode;
  label: string;
  active?: boolean;
  badge?: number;
  onClick: () => void;
}) {
  return (
    <button
      className={`nav-item ${
        active ? "active" : ""
      }`}
      onClick={onClick}
    >
      {icon}

      <span>
        {label}
      </span>

      {badge !== undefined &&
        badge > 0 && (
          <span className="nav-badge">
            {badge}
          </span>
        )}

    </button>
  );
}


function SensorCard({
  icon,
  label,
  value,
  unit,
  range,
  safe,
}: {
  icon: ReactNode;
  label: string;
  value: number | null;
  unit: string;
  range: string;
  safe: boolean;
}) {
  return (
    <div className="sensor-card">

      <div className="sensor-top">

        <div className="sensor-icon">
          {icon}
        </div>

        {value !== null &&
          (safe ? (
            <CheckCircle2
              size={15}
              className="success-icon"
            />
          ) : (
            <AlertTriangle
              size={15}
              className="danger-icon"
            />
          ))}

      </div>

      <div className="sensor-label">
        {label}
      </div>

      <div className="sensor-value">

        {value !== null
          ? value
          : "--"}

        {unit && (
          <small>
            {unit}
          </small>
        )}

      </div>

      <div className="sensor-range">
        {range}
      </div>

    </div>
  );
}


function StatusRow({
  label,
  value,
  positive,
}: {
  label: string;
  value: string;
  positive?: boolean;
}) {
  return (
    <div className="status-row">

      <span>
        {label}
      </span>

      <strong
        className={
          positive
            ? "positive"
            : ""
        }
      >
        {value}
      </strong>

    </div>
  );
}



function AnalyticsCard({
  icon,
  label,
  value,
  description,
  type,
}: {
  icon: ReactNode;
  label: string;
  value: string;
  description: string;
  type: "success" | "danger" | "neutral";
}) {
  return (
    <div className={`analytics-card ${type}`}>
      <div className="analytics-card-top">
        <div className="analytics-icon">
          {icon}
        </div>

        <span className={`analytics-status ${type}`}>
          {type === "success"
            ? "NORMAL"
            : type === "danger"
              ? "ATTENTION"
              : "MONITORING"}
        </span>
      </div>

      <div className="analytics-label">
        {label}
      </div>

      <div className="analytics-value">
        {value}
      </div>

      <div className="analytics-description">
        {description}
      </div>
    </div>
  );
}


function InfoPanel({
  icon,
  label,
  value,
  description,
  type,
}: {
  icon: ReactNode;
  label: string;
  value: string;
  description: string;
  type:
    | "success"
    | "danger"
    | "neutral";
}) {
  return (
    <div className="info-panel">

      <div className="info-panel-top">

        <div className="info-icon">
          {icon}
        </div>

        <span
          className={`info-status ${type}`}
        >
          {type === "success"
            ? "NORMAL"
            : type === "danger"
              ? "ATTENTION"
              : "MONITORING"}
        </span>

      </div>

      <div className="info-label">
        {label}
      </div>

      <div className="info-value">
        {value}
      </div>

      <div className="info-description">
        {description}
      </div>

    </div>
  );
}


function ClickableInfoPanel({
  icon,
  label,
  value,
  description,
  type,
  onClick,
}: {
  icon: ReactNode;
  label: string;
  value: string;
  description: string;
  type:
    | "success"
    | "danger"
    | "neutral";
  onClick: () => void;
}) {
  return (
    <button
      className="clickable-info-panel"
      onClick={onClick}
    >

      <InfoPanel
        icon={icon}
        label={label}
        value={value}
        description={description}
        type={type}
      />

      <ChevronRight
        size={16}
        className="panel-arrow"
      />

    </button>
  );
}


function QualityMetric({
  label,
  value,
  unit,
  safe,
  limit,
}: {
  label: string;
  value: number | null;
  unit: string;
  safe: boolean;
  limit: string;
}) {
  return (
    <div className="quality-metric">

      <div className="metric-top">

        <span>
          {label}
        </span>

        {value !== null &&
          (safe ? (
            <CheckCircle2
              size={16}
              className="success-icon"
            />
          ) : (
            <AlertTriangle
              size={16}
              className="danger-icon"
            />
          ))}

      </div>

      <div className="metric-value">

        {value !== null
          ? value
          : "--"}

        {unit && (
          <small>
            {unit}
          </small>
        )}

      </div>

      <div className="metric-limit">
        Safe limit: {limit}
      </div>

    </div>
  );
}


function AlertRow({
  alert,
  onResolved,
}: {
  alert: AlertItem;
  onResolved?: (alertId: number) => void;
}) {
  const [resolving, setResolving] = useState(false);
  const [error, setError] = useState("");

  const handleResolve = async () => {
    if (resolving) return;

    setResolving(true);
    setError("");

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/api/v1/alerts/${alert.id}/resolve`,
        {
          method: "PATCH",
        },
      );

      if (!response.ok) {
        throw new Error(
          `Failed to resolve alert (${response.status})`,
        );
      }

      onResolved?.(alert.id);
    } catch (err) {
      console.error(err);

      setError(
        "Unable to resolve this alert. Please try again.",
      );
    } finally {
      setResolving(false);
    }
  };

  return (
    <div className="alert-row">
      <div className="alert-icon">
        <AlertTriangle size={18} />
      </div>

      <div className="alert-content">
        <div className="alert-title-row">
          <strong>
            {alert.title}
          </strong>

          <span
            className={`severity ${alert.severity}`}
          >
            {alert.severity}
          </span>
        </div>

        <p>
          {alert.message}
        </p>

        {alert.measured_value !== null && (
          <div className="alert-measurement">
            Measured:{" "}
            <strong>
              {alert.measured_value}
            </strong>

            {alert.threshold_value !== null && (
              <>
                {" "}· Limit:{" "}
                <strong>
                  {alert.threshold_value}
                </strong>
              </>
            )}
          </div>
        )}

        {error && (
          <div className="alert-error">
            {error}
          </div>
        )}

        <button
          type="button"
          className="resolve-alert-button"
          onClick={handleResolve}
          disabled={resolving}
        >
          <CheckCircle2 size={15} />

          {resolving
            ? "Resolving..."
            : "Resolve Alert"}
        </button>
      </div>
    </div>
  );
}

function PageIntro({
  label,
  title,
  description,
}: {
  label: string;
  title: string;
  description: string;
}) {
  return (
    <section className="page-intro">

      <div>

        <div className="section-label">
          {label}
        </div>

        <h2>
          {title}
        </h2>

        <p>
          {description}
        </p>

      </div>

      <div className="live-pill">

        <span className="status-dot online" />

        LIVE

      </div>

    </section>
  );
}


/* ============================================================
   DATA HELPERS
============================================================ */

interface ChartPoint {
  time: string;
  pH: number | null;
  turbidity: number | null;
  tds: number | null;
  temperature: number | null;
}

function buildChartData(
  readings: Reading[],
): ChartPoint[] {
  const ordered = [
    ...readings,
  ].reverse();

  const grouped =
    new Map<
      string,
      ChartPoint
    >();

  for (const reading of ordered) {

    const time =
      formatChartTime(
        reading.recorded_at,
      );

    if (!grouped.has(time)) {
      grouped.set(time, {
        time,
        pH: null,
        turbidity: null,
        tds: null,
        temperature: null,
      });
    }

    const point =
      grouped.get(time)!;

    const type =
      getSensorType(
        reading,
      );

    if (type === "ph") {
      point.pH =
        reading.value;
    }

    if (
      type ===
      "turbidity"
    ) {
      point.turbidity =
        reading.value;
    }

    if (type === "tds") {
      point.tds =
        reading.value;
    }

    if (
      type ===
      "temperature"
    ) {
      point.temperature =
        reading.value;
    }
  }

  return Array.from(
    grouped.values(),
  ).slice(-30);
}


function getSensorType(
  reading: Reading,
) {
  const unit =
    reading.unit
      .toLowerCase();

  if (
    unit === "ph"
  ) {
    return "ph";
  }

  if (
    unit === "ntu"
  ) {
    return "turbidity";
  }

  if (
    unit === "ppm"
  ) {
    return "tds";
  }

  if (
    unit === "c" ||
    unit === "°c"
  ) {
    return "temperature";
  }

  return "";
}


function formatChartTime(
  value: string,
) {
  const date =
    new Date(value);

  return date.toLocaleTimeString(
    "en-IN",
    {
      hour: "2-digit",
      minute: "2-digit",
    },
  );
}


function getPageTitle(
  page: Page,
) {
  switch (page) {
    case "overview":
      return "Monitoring Dashboard";

    case "water-quality":
      return "Water Quality";

    case "filter":
      return "Filter Health";

    case "treatment":
      return "Treatment";

    case "alerts":
      return "Alerts";

    case "maintenance":
      return "Maintenance";

    default:
      return "SmartWater";
  }
}



function getSafeParameterCount(
  data: DashboardData,
) {
  const quality = data.water_quality;

  let count = 0;

  if (
    quality.pH !== null &&
    quality.pH >= 6.5 &&
    quality.pH <= 8.5
  ) {
    count++;
  }

  if (
    quality.turbidity !== null &&
    quality.turbidity <= 5
  ) {
    count++;
  }

  if (
    quality.tds !== null &&
    quality.tds <= 500
  ) {
    count++;
  }

  if (quality.temperature !== null) {
    count++;
  }

  return count;
}


function calculateWaterScore(
  data: DashboardData,
) {
  const quality = data.water_quality;

  let score = 0;
  let available = 0;

  if (quality.pH !== null) {
    available++;

    if (
      quality.pH >= 6.5 &&
      quality.pH <= 8.5
    ) {
      score++;
    }
  }

  if (quality.turbidity !== null) {
    available++;

    if (quality.turbidity <= 5) {
      score++;
    }
  }

  if (quality.tds !== null) {
    available++;

    if (quality.tds <= 500) {
      score++;
    }
  }

  if (quality.temperature !== null) {
    available++;
    score++;
  }

  if (available === 0) {
    return 0;
  }

  return Math.round(
    (score / available) * 100,
  );
}


function getRiskLevel(
  data: DashboardData,
) {
  if (
    data.alerts.active_count === 0 &&
    data.water_quality.is_safe
  ) {
    return "LOW";
  }

  const criticalAlert =
    data.alerts.items.some(
      (alert) =>
        alert.severity.toLowerCase() ===
        "critical",
    );

  if (criticalAlert) {
    return "HIGH";
  }

  return "MEDIUM";
}


function getSystemInsight(
  data: DashboardData,
) {
  if (!data.device.is_online) {
    return "Device telemetry is currently offline.";
  }

  if (data.alerts.active_count > 0) {
    return "System attention required: active water-safety events are being monitored.";
  }

  if (data.filter.replacement_required) {
    return "Filter maintenance is required to maintain purification performance.";
  }

  if (data.treatment.status === "started") {
    return "Purification cycle is currently active and being monitored.";
  }

  if (data.water_quality.is_safe) {
    return "System is operating normally with water quality within configured limits.";
  }

  return "Water quality requires attention based on the latest sensor evaluation.";
}


function capitalize(
  value: string,
) {
  if (!value) {
    return "--";
  }

  return (
    value.charAt(0).toUpperCase() +
    value.slice(1)
  );
}


function formatDate(
  value: string | null,
) {
  if (!value) {
    return "Not available";
  }

  const date =
    new Date(value);

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return "Not available";
  }

  return date.toLocaleString(
    "en-IN",
    {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    },
  );
}


export default App;