import { useEffect, useMemo, useRef, useState } from 'react'
import type {
  MetricSample,
  Pagination,
  Patient,
  PatientCreate,
} from '@health-monitoring/api-client'
import {
  Chart as ChartJS,
  Decimation,
  Filler,
  Legend,
  LineElement,
  LinearScale,
  PointElement,
  Tooltip,
  type ChartData,
  type ChartOptions,
} from 'chart.js'
import zoomPlugin from 'chartjs-plugin-zoom'
import { Line } from 'react-chartjs-2'
import { api, apiBaseUrl, getApiErrorMessage } from './api'
import './App.css'

const PATIENT_PAGE_SIZE = 12
const METRIC_PAGE_SIZE = 1000
const HR_SAMPLE_COUNT = 600

ChartJS.register(
  Decimation,
  Filler,
  Legend,
  LineElement,
  LinearScale,
  PointElement,
  Tooltip,
  zoomPlugin,
)

type PatientForm = {
  name: string
  age: string
  weight: string
  profilePicture: string
}

type Notice = {
  kind: 'success' | 'error'
  text: string
}

type PreviewState = {
  status: 'loading' | 'ready' | 'error'
  latestTemperature?: MetricSample
  error?: string
}

type ChartPoint = {
  x: number
  y: number
}

const emptyPatientForm: PatientForm = {
  name: '',
  age: '',
  weight: '',
  profilePicture: '',
}

const emptyPatientPagination: Pagination = {
  total: 0,
  limit: PATIENT_PAGE_SIZE,
  offset: 0,
}

const emptyMetricPagination: Pagination = {
  total: 0,
  limit: METRIC_PAGE_SIZE,
  offset: 0,
}

function toLocalDateTimeInput(date = new Date()): string {
  const copy = new Date(date)
  copy.setSeconds(0, 0)
  const localTime = new Date(copy.getTime() - copy.getTimezoneOffset() * 60000)
  return localTime.toISOString().slice(0, 16)
}

function parseLocalDateTime(value: string, label: string): Date {
  if (!value) {
    throw new Error(`${label} is required.`)
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    throw new Error(`${label} is not a valid date.`)
  }

  return date
}

function optionalLocalDateTime(value: string): Date | undefined {
  if (!value) {
    return undefined
  }

  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? undefined : date
}

function formatDateTime(value: Date | string): string {
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) {
    return 'Invalid date'
  }

  const pad = (part: number, size = 2) => String(part).padStart(size, '0')
  return [
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`,
    `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`,
  ].join(' ')
}

function formatMetricValue(value: number, unit: string): string {
  const precision = unit === 'bpm' ? 0 : 1
  return `${value.toFixed(precision)} ${unit}`
}

function formatChartTick(timestamp: number): string {
  const date = new Date(timestamp)
  if (Number.isNaN(date.getTime())) {
    return ''
  }

  const pad = (part: number) => String(part).padStart(2, '0')
  return `${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function shortId(id: string): string {
  return id.slice(0, 8)
}

function compactNumber(value: number, maximumFractionDigits = 1): string {
  if (!Number.isFinite(value)) {
    return '-'
  }

  return new Intl.NumberFormat('en-US', {
    maximumFractionDigits,
  }).format(value)
}

function cleanDisplayText(value: string): string {
  return value.replace(/\p{C}/gu, '').replace(/\s+/g, ' ').trim()
}

function displayPatientName(patient: Patient): string {
  const cleaned = cleanDisplayText(patient.name)
  const characters = Array.from(cleaned)
  const readableCharacters = characters.filter((character) =>
    /[\p{L}\p{N}\s.'-]/u.test(character),
  )
  const readableRatio =
    characters.length === 0 ? 0 : readableCharacters.length / characters.length

  if (!cleaned || readableRatio < 0.75) {
    return `Patient ${shortId(patient.id)}`
  }

  return cleaned.length > 36 ? `${cleaned.slice(0, 33)}...` : cleaned
}

function PatientArtwork({
  patient,
  size = 'normal',
}: {
  patient: Patient
  size?: 'normal' | 'large'
}) {
  const name = displayPatientName(patient)

  return (
    <span className={`avatar ${size}`}>
      {patient.profilePicture ? <img src={patient.profilePicture} alt="" /> : name.slice(0, 1)}
    </span>
  )
}

function patientToForm(patient: Patient): PatientForm {
  return {
    name: patient.name,
    age: String(patient.age),
    weight: String(patient.weight),
    profilePicture: patient.profilePicture ?? '',
  }
}

function buildPatientPayload(form: PatientForm): PatientCreate {
  const age = Number(form.age)
  const weight = Number(form.weight)
  const name = form.name.trim()
  const profilePicture = form.profilePicture.trim()

  if (!name) {
    throw new Error('Name is required.')
  }

  if (!Number.isInteger(age)) {
    throw new Error('Age must be an integer.')
  }

  if (!Number.isFinite(weight)) {
    throw new Error('Weight must be a number.')
  }

  const payload: PatientCreate = { name, age, weight }
  if (profilePicture) {
    payload.profilePicture = profilePicture
  }

  return payload
}

function paginationText(pagination: Pagination): string {
  if (pagination.total === 0) {
    return '0 of 0'
  }

  const first = pagination.offset + 1
  const last = Math.min(pagination.offset + pagination.limit, pagination.total)
  return `${first}-${last} of ${pagination.total}`
}

function generateHeartRateSamples(base: number): number[] {
  if (!Number.isFinite(base)) {
    throw new Error('Base heart rate must be a number.')
  }

  return Array.from({ length: HR_SAMPLE_COUNT }, (_, index) => {
    const wave = Math.sin(index / 18) * 6 + Math.sin(index / 7) * 2
    const value = Math.min(220, Math.max(30, base + wave))
    return Number(value.toFixed(1))
  })
}

function toChartData(samples: MetricSample[], precision: number): ChartPoint[] {
  return samples
    .map((sample) => {
      const timestamp = sample.timestamp.getTime()
      if (Number.isNaN(timestamp)) {
        return undefined
      }

      return {
        x: timestamp,
        y: Number(sample.value.toFixed(precision)),
      }
    })
    .filter((point): point is ChartPoint => point !== undefined)
}

function MetricChart({
  color,
  data,
  emptyLabel,
  label,
  unit,
}: {
  color: string
  data: ChartPoint[]
  emptyLabel: string
  label: string
  unit: string
}) {
  const chartRef = useRef<ChartJS<'line', ChartPoint[]> | null>(null)

  function resetZoom() {
    chartRef.current?.resetZoom()
  }

  const chartData: ChartData<'line', ChartPoint[]> = {
    datasets: [
      {
        backgroundColor: `${color}22`,
        borderColor: color,
        borderWidth: 2,
        data,
        fill: true,
        label,
        pointHitRadius: 12,
        pointHoverRadius: 4,
        pointRadius: 0,
        tension: 0.25,
      },
    ],
  }
  const chartOptions: ChartOptions<'line'> = {
    animation: false,
    interaction: {
      intersect: false,
      mode: 'nearest',
    },
    maintainAspectRatio: false,
    normalized: true,
    parsing: false,
    plugins: {
      decimation: {
        algorithm: 'lttb',
        enabled: true,
        samples: 700,
      },
      legend: {
        display: false,
      },
      tooltip: {
        backgroundColor: '#f8fafc',
        borderColor: '#334155',
        borderWidth: 1,
        callbacks: {
          label: (item) => formatMetricValue(Number(item.parsed.y), unit),
          title: (items) => {
            const timestamp = Number(items[0]?.parsed.x)
            return Number.isFinite(timestamp) ? formatDateTime(new Date(timestamp)) : ''
          },
        },
        displayColors: false,
        titleColor: '#0f172a',
        bodyColor: '#0f172a',
      },
      zoom: {
        limits: {
          x: {
            min: 'original',
            max: 'original',
          },
        },
        pan: {
          enabled: true,
          mode: 'x',
          modifierKey: 'shift',
        },
        zoom: {
          drag: {
            backgroundColor: `${color}22`,
            borderColor: color,
            borderWidth: 1,
            enabled: true,
          },
          mode: 'x',
          pinch: {
            enabled: true,
          },
          wheel: {
            enabled: true,
            speed: 0.08,
          },
        },
      },
    },
    responsive: true,
    scales: {
      x: {
        grid: {
          color: 'rgba(148, 163, 184, 0.18)',
        },
        ticks: {
          color: '#94a3b8',
          maxTicksLimit: 8,
          callback: (value) => formatChartTick(Number(value)),
        },
        type: 'linear',
      },
      y: {
        grid: {
          color: 'rgba(148, 163, 184, 0.14)',
        },
        ticks: {
          color: '#94a3b8',
        },
      },
    },
  }

  return (
    <section className="chart-panel">
      <div className="section-title-row">
        <div>
          <p className="eyebrow">Timeseries</p>
          <h3>{label}</h3>
        </div>
        <div className="chart-actions">
          <span>{data.length.toLocaleString('en-US')} points</span>
          <button
            type="button"
            className="secondary-button compact-button"
            onClick={resetZoom}
            disabled={data.length === 0}
          >
            Reset zoom
          </button>
        </div>
      </div>

      {data.length === 0 ? (
        <div className="empty-state chart-empty">{emptyLabel}</div>
      ) : (
        <div className="chart-frame" onDoubleClick={resetZoom}>
          <Line ref={chartRef} data={chartData} options={chartOptions} />
        </div>
      )}
    </section>
  )
}

function MetricRows({
  emptyLabel,
  samples,
  unit,
}: {
  emptyLabel: string
  samples: MetricSample[]
  unit: string
}) {
  if (samples.length === 0) {
    return <div className="empty-state compact">{emptyLabel}</div>
  }

  return (
    <div className="metric-table">
      {samples.slice(-8).map((sample) => (
        <div className="metric-row" key={`${sample.timestamp.toISOString()}-${sample.value}`}>
          <span>{formatDateTime(sample.timestamp)}</span>
          <strong>{formatMetricValue(sample.value, unit)}</strong>
        </div>
      ))}
    </div>
  )
}

function App() {
  const [health, setHealth] = useState('checking')
  const [patients, setPatients] = useState<Patient[]>([])
  const [activePatient, setActivePatient] = useState<Patient | null>(null)
  const [patientForm, setPatientForm] = useState<PatientForm>(emptyPatientForm)
  const [patientPagination, setPatientPagination] = useState<Pagination>(
    emptyPatientPagination,
  )
  const [patientOffset, setPatientOffset] = useState(0)
  const [expandedPreviews, setExpandedPreviews] = useState<Set<string>>(new Set())
  const [previews, setPreviews] = useState<Record<string, PreviewState>>({})
  const [notice, setNotice] = useState<Notice | null>(null)
  const [busy, setBusy] = useState<string | null>(null)

  const [historyStart, setHistoryStart] = useState('')
  const [historyEnd, setHistoryEnd] = useState('')
  const [temperatureHistory, setTemperatureHistory] = useState<MetricSample[]>([])
  const [heartRateHistory, setHeartRateHistory] = useState<MetricSample[]>([])
  const [temperaturePagination, setTemperaturePagination] = useState<Pagination>(
    emptyMetricPagination,
  )
  const [heartRatePagination, setHeartRatePagination] = useState<Pagination>(
    emptyMetricPagination,
  )

  const [temperatureTime, setTemperatureTime] = useState(toLocalDateTimeInput())
  const [temperatureValue, setTemperatureValue] = useState('36.8')
  const [heartRateStart, setHeartRateStart] = useState(toLocalDateTimeInput())
  const [heartRateBase, setHeartRateBase] = useState('72')

  const selectedPatientId = activePatient?.id ?? ''
  const patientHasPrevious = patientOffset > 0
  const patientHasNext =
    patientOffset + patientPagination.limit < patientPagination.total
  const metricTotal = Math.max(
    temperaturePagination.total,
    heartRatePagination.total,
  )
  const isBusy = busy !== null

  const temperatureChartData = useMemo(
    () => toChartData(temperatureHistory, 1),
    [temperatureHistory],
  )
  const heartRateChartData = useMemo(
    () => toChartData(heartRateHistory, 0),
    [heartRateHistory],
  )

  useEffect(() => {
    void refreshHealth()
    void loadPatients(0).catch(async (error) => {
      setNotice({ kind: 'error', text: await getApiErrorMessage(error) })
    })
    // The app should load its first registry page once when it mounts.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function refreshHealth() {
    try {
      const response = await api.system.getHealth()
      setHealth(`${response.service} ${response.version} - ${response.status}`)
    } catch {
      setHealth('API unreachable')
    }
  }

  async function run(
    action: string,
    task: () => Promise<void>,
    successMessage?: string,
  ) {
    setBusy(action)
    setNotice(null)

    try {
      await task()
      if (successMessage) {
        setNotice({ kind: 'success', text: successMessage })
      }
    } catch (error) {
      setNotice({ kind: 'error', text: await getApiErrorMessage(error) })
    } finally {
      setBusy(null)
    }
  }

  async function loadPatients(nextOffset = patientOffset, preferredId?: string) {
    const response = await api.patients.listPatients({
      limit: PATIENT_PAGE_SIZE,
      offset: nextOffset,
    })

    setPatients(response.data)
    setPatientPagination(response.pagination)
    setPatientOffset(nextOffset)

    if (preferredId) {
      const preferredPatient = response.data.find((patient) => patient.id === preferredId)
      if (preferredPatient) {
        openPatient(preferredPatient)
      }
      return
    }

    if (activePatient) {
      const refreshedPatient = response.data.find(
        (patient) => patient.id === activePatient.id,
      )
      if (refreshedPatient) {
        setActivePatient(refreshedPatient)
        setPatientForm(patientToForm(refreshedPatient))
      }
    }
  }

  async function loadMetricHistory(patientId = selectedPatientId) {
    if (!patientId) {
      return
    }

    const startTime = optionalLocalDateTime(historyStart)
    const endTime = optionalLocalDateTime(historyEnd)

    const [temperatureResponse, heartRateResponse] = await Promise.all([
      loadAllMetricPages((offset) =>
        api.metrics.getTemperatureHistory({
          patientId,
          startTime,
          endTime,
          limit: METRIC_PAGE_SIZE,
          offset,
        }),
      ),
      loadAllMetricPages((offset) =>
        api.metrics.getHeartRateHistory({
          patientId,
          startTime,
          endTime,
          limit: METRIC_PAGE_SIZE,
          offset,
        }),
      ),
    ])

    setTemperatureHistory(temperatureResponse.data)
    setHeartRateHistory(heartRateResponse.data)
    setTemperaturePagination(temperatureResponse.pagination)
    setHeartRatePagination(heartRateResponse.pagination)
  }

  async function loadAllMetricPages(
    fetchPage: (offset: number) => Promise<{ data: MetricSample[]; pagination: Pagination }>,
  ): Promise<{ data: MetricSample[]; pagination: Pagination }> {
    const data: MetricSample[] = []
    let offset = 0
    let total: number | undefined

    while (total === undefined || offset < total) {
      const response = await fetchPage(offset)
      data.push(...response.data)
      total = response.pagination.total
      offset += response.pagination.limit
    }

    return {
      data,
      pagination: {
        total: total ?? 0,
        limit: data.length || METRIC_PAGE_SIZE,
        offset: 0,
      },
    }
  }

  async function loadPatientPreview(patientId: string) {
    setPreviews((current) => ({
      ...current,
      [patientId]: { status: 'loading', latestTemperature: current[patientId]?.latestTemperature },
    }))

    try {
      const firstPage = await api.metrics.getTemperatureHistory({
        patientId,
        limit: 1,
        offset: 0,
      })
      const total = firstPage.pagination.total
      let latestTemperature = firstPage.data[0]

      if (total > 1) {
        const lastPage = await api.metrics.getTemperatureHistory({
          patientId,
          limit: 1,
          offset: total - 1,
        })
        latestTemperature = lastPage.data[0]
      }

      setPreviews((current) => ({
        ...current,
        [patientId]: { status: 'ready', latestTemperature },
      }))
    } catch (error) {
      const message = await getApiErrorMessage(error)
      setPreviews((current) => ({
        ...current,
        [patientId]: { status: 'error', error: message },
      }))
    }
  }

  function requireSelectedPatient(): string {
    if (!selectedPatientId) {
      throw new Error('Select a patient first.')
    }

    return selectedPatientId
  }

  function clearMetricHistory() {
    setTemperatureHistory([])
    setHeartRateHistory([])
    setTemperaturePagination(emptyMetricPagination)
    setHeartRatePagination(emptyMetricPagination)
  }

  function updatePatientForm(field: keyof PatientForm, value: string) {
    setPatientForm((current) => ({ ...current, [field]: value }))
  }

  async function createPatient() {
    const created = await api.patients.createPatient({
      patientCreate: buildPatientPayload(patientForm),
    })

    await loadPatients(0, created.id)
  }

  async function updatePatient() {
    const patientId = requireSelectedPatient()
    const updated = await api.patients.updatePatient({
      patientId,
      patientUpdate: buildPatientPayload(patientForm),
    })

    setActivePatient(updated)
    await loadPatients(patientOffset, updated.id)
  }

  async function deletePatient() {
    const patientId = requireSelectedPatient()
    await api.patients.deletePatient({ patientId })

    const nextOffset =
      patients.length === 1 ? Math.max(0, patientOffset - PATIENT_PAGE_SIZE) : patientOffset

    closePatient()
    await loadPatients(nextOffset)
  }

  async function ingestTemperature() {
    const patientId = requireSelectedPatient()
    const timestamp = parseLocalDateTime(temperatureTime, 'Temperature timestamp')
    timestamp.setSeconds(0, 0)

    const value = Number(temperatureValue)
    if (!Number.isFinite(value)) {
      throw new Error('Temperature must be a number.')
    }

    await api.metrics.ingestTemperatureMinute({
      patientId,
      temperatureMinute: { timestamp, value },
    })
    await Promise.all([
      loadMetricHistory(patientId),
      expandedPreviews.has(patientId) ? loadPatientPreview(patientId) : Promise.resolve(),
    ])
  }

  async function ingestHeartRate() {
    const patientId = requireSelectedPatient()
    const startTimestamp = parseLocalDateTime(
      heartRateStart,
      'Heart rate start timestamp',
    )
    const samples = generateHeartRateSamples(Number(heartRateBase))

    await api.metrics.ingestHeartRateBatch({
      patientId,
      heartRateBatch: { startTimestamp, samples },
    })
    await loadMetricHistory(patientId)
  }

  function openPatient(patient: Patient) {
    setActivePatient(patient)
    setPatientForm(patientToForm(patient))
    void run('metrics', () => loadMetricHistory(patient.id))
  }

  function closePatient() {
    setActivePatient(null)
    setPatientForm(emptyPatientForm)
    clearMetricHistory()
  }

  function clearPatientForm() {
    setPatientForm(emptyPatientForm)
  }

  function togglePreview(patientId: string) {
    const willExpand = !expandedPreviews.has(patientId)
    setExpandedPreviews((current) => {
      const next = new Set(current)
      if (next.has(patientId)) {
        next.delete(patientId)
      } else {
        next.add(patientId)
      }
      return next
    })

    if (willExpand && previews[patientId]?.status !== 'ready') {
      void loadPatientPreview(patientId)
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Contract-first demo</p>
          <h1>Health Monitoring System</h1>
        </div>
        <div className="topbar-meta">
          <span className="api-target">{apiBaseUrl}</span>
          <button type="button" className="status-pill" onClick={() => void refreshHealth()}>
            {health}
          </button>
        </div>
      </header>

      {notice && <div className={`notice ${notice.kind}`}>{notice.text}</div>}

      {activePatient ? (
        <section className="patient-detail-page">
          <div className="detail-hero">
            <button type="button" className="back-button" onClick={closePatient}>
              Back
            </button>
            <PatientArtwork patient={activePatient} size="large" />
            <div className="detail-title">
              <p className="eyebrow">Patient detail</p>
              <h2>{displayPatientName(activePatient)}</h2>
              <span>{activePatient.id}</span>
            </div>
            <div className="vitals-strip">
              <div>
                <span>Age</span>
                <strong>{activePatient.age}</strong>
              </div>
              <div>
                <span>Weight</span>
                <strong>{compactNumber(activePatient.weight)} kg</strong>
              </div>
              <div>
                <span>Updated</span>
                <strong>{formatDateTime(activePatient.updatedAt)}</strong>
              </div>
            </div>
          </div>

          <div className="detail-grid">
            <section className="profile-panel">
              <div className="section-title-row">
                <div>
                  <p className="eyebrow">Profile</p>
                  <h3>Editable data</h3>
                </div>
              </div>

              <form className="form-grid" onSubmit={(event) => event.preventDefault()}>
                <label>
                  Name
                  <input
                    type="text"
                    value={patientForm.name}
                    onChange={(event) => updatePatientForm('name', event.target.value)}
                    required
                  />
                </label>
                <label>
                  Age
                  <input
                    type="number"
                    min="0"
                    step="1"
                    value={patientForm.age}
                    onChange={(event) => updatePatientForm('age', event.target.value)}
                    required
                  />
                </label>
                <label>
                  Weight
                  <input
                    type="number"
                    min="0"
                    step="0.1"
                    value={patientForm.weight}
                    onChange={(event) => updatePatientForm('weight', event.target.value)}
                    required
                  />
                </label>
                <label className="wide">
                  Profile URL
                  <input
                    type="url"
                    value={patientForm.profilePicture}
                    onChange={(event) =>
                      updatePatientForm('profilePicture', event.target.value)
                    }
                    placeholder="https://example.com/photo.jpg"
                  />
                </label>
              </form>

              <div className="button-row">
                <button
                  type="button"
                  onClick={() =>
                    void run('update-patient', updatePatient, 'Patient updated.')
                  }
                  disabled={isBusy}
                >
                  Save
                </button>
                <button
                  type="button"
                  className="danger-button"
                  onClick={() =>
                    void run('delete-patient', deletePatient, 'Patient deleted.')
                  }
                  disabled={isBusy}
                >
                  Delete
                </button>
              </div>
            </section>

            <section className="capture-panel">
              <div className="section-title-row">
                <div>
                  <p className="eyebrow">Capture</p>
                  <h3>New samples</h3>
                </div>
              </div>

              <div className="capture-grid">
                <div className="capture-block">
                  <h4>Temperature</h4>
                  <label>
                    Minute
                    <input
                      type="datetime-local"
                      value={temperatureTime}
                      onChange={(event) => setTemperatureTime(event.target.value)}
                      required
                    />
                  </label>
                  <label>
                    Celsius
                    <input
                      type="number"
                      min="34"
                      max="42"
                      step="0.1"
                      value={temperatureValue}
                      onChange={(event) => setTemperatureValue(event.target.value)}
                      required
                    />
                  </label>
                  <button
                    type="button"
                    onClick={() =>
                      void run(
                        'temperature',
                        ingestTemperature,
                        'Temperature sample stored.',
                      )
                    }
                    disabled={isBusy}
                  >
                    Store temperature
                  </button>
                </div>

                <div className="capture-block">
                  <h4>Heart rate</h4>
                  <label>
                    Start
                    <input
                      type="datetime-local"
                      value={heartRateStart}
                      onChange={(event) => setHeartRateStart(event.target.value)}
                      required
                    />
                  </label>
                  <label>
                    Base bpm
                    <input
                      type="number"
                      min="30"
                      max="220"
                      step="1"
                      value={heartRateBase}
                      onChange={(event) => setHeartRateBase(event.target.value)}
                      required
                    />
                  </label>
                  <button
                    type="button"
                    onClick={() =>
                      void run('heart-rate', ingestHeartRate, 'Heart rate batch stored.')
                    }
                    disabled={isBusy}
                  >
                    Store 600 samples
                  </button>
                </div>
              </div>
            </section>
          </div>

          <section className="timeline-panel">
            <div className="section-title-row">
              <div>
                <p className="eyebrow">Signals</p>
                <h3>Timeseries overview</h3>
              </div>
              <div className="pager">
                <span>{paginationText(temperaturePagination)} temp</span>
                <span>{paginationText(heartRatePagination)} HR</span>
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() =>
                    void run(
                      'metrics',
                      () => loadMetricHistory(selectedPatientId),
                      'Full timeseries refreshed.',
                    )
                  }
                  disabled={isBusy}
                >
                  Refresh
                </button>
              </div>
            </div>

            <div className="history-controls">
              <label>
                Start
                <input
                  type="datetime-local"
                  value={historyStart}
                  onChange={(event) => setHistoryStart(event.target.value)}
                />
              </label>
              <label>
                End
                <input
                  type="datetime-local"
                  value={historyEnd}
                  onChange={(event) => setHistoryEnd(event.target.value)}
                />
              </label>
              <div className="history-summary">
                <span>Loaded complete range</span>
                <strong>{metricTotal.toLocaleString('en-US')} samples</strong>
              </div>
            </div>

            <div className="charts-grid">
              <MetricChart
                color="#2563eb"
                data={temperatureChartData}
                emptyLabel="No temperature samples"
                label="Temperature"
                unit="C"
              />
              <MetricChart
                color="#10b981"
                data={heartRateChartData}
                emptyLabel="No heart rate samples"
                label="Heart rate"
                unit="bpm"
              />
            </div>

            <div className="latest-grid">
              <section>
                <h4>Recent temperature samples</h4>
                <MetricRows
                  emptyLabel="No temperature samples"
                  samples={temperatureHistory}
                  unit="C"
                />
              </section>
              <section>
                <h4>Recent heart rate samples</h4>
                <MetricRows
                  emptyLabel="No heart rate samples"
                  samples={heartRateHistory}
                  unit="bpm"
                />
              </section>
            </div>
          </section>
        </section>
      ) : (
        <section className="home-grid">
          <section className="registry-panel">
            <div className="section-title-row registry-header">
              <div>
                <p className="eyebrow">Patients</p>
                <h2>Registry</h2>
              </div>
              <div className="pager">
                <span>{paginationText(patientPagination)}</span>
                <button
                  type="button"
                  onClick={() =>
                    void run(
                      'patients-page',
                      () => loadPatients(Math.max(0, patientOffset - PATIENT_PAGE_SIZE)),
                    )
                  }
                  disabled={!patientHasPrevious || isBusy}
                >
                  Previous
                </button>
                <button
                  type="button"
                  onClick={() =>
                    void run(
                      'patients-page',
                      () => loadPatients(patientOffset + PATIENT_PAGE_SIZE),
                    )
                  }
                  disabled={!patientHasNext || isBusy}
                >
                  Next
                </button>
              </div>
            </div>

            <div className="patient-card-list">
              {patients.length === 0 ? (
                <div className="empty-state large">No patients yet</div>
              ) : (
                patients.map((patient) => {
                  const preview = previews[patient.id]
                  const isExpanded = expandedPreviews.has(patient.id)

                  return (
                    <article className="patient-card" key={patient.id}>
                      <button
                        type="button"
                        className="patient-card-main"
                        onClick={() => openPatient(patient)}
                      >
                        <PatientArtwork patient={patient} />
                        <span className="patient-identity">
                          <strong title={patient.name}>{displayPatientName(patient)}</strong>
                          
                        </span>
                        <span className="patient-stats">
                          {patient.age} y
                          <br />
                          {compactNumber(patient.weight)} kg
                        </span>
                      </button>

                      <div className="patient-card-actions">
                        <span>Updated {formatDateTime(patient.updatedAt)}</span>
                        <button
                          type="button"
                          className="ghost-button"
                          onClick={() => togglePreview(patient.id)}
                        >
                          {isExpanded ? 'Hide preview' : 'Show preview'}
                        </button>
                      </div>

                      {isExpanded && (
                        <div className="patient-preview">
                          {preview?.status === 'loading' && <span>Loading preview...</span>}
                          {preview?.status === 'error' && (
                            <span className="preview-error">{preview.error}</span>
                          )}
                          {preview?.status === 'ready' && preview.latestTemperature && (
                            <>
                              <div>
                                <span>Latest temperature</span>
                                <strong>
                                  {formatMetricValue(preview.latestTemperature.value, 'C')}
                                </strong>
                              </div>
                              <div>
                                <span>Measured at</span>
                                <strong>{formatDateTime(preview.latestTemperature.timestamp)}</strong>
                              </div>
                            </>
                          )}
                          {preview?.status === 'ready' && !preview.latestTemperature && (
                            <span>No temperature samples</span>
                          )}
                        </div>
                      )}
                    </article>
                  )
                })
              )}
            </div>
          </section>

          <aside className="create-panel">
            <div className="section-title-row">
              <div>
                <p className="eyebrow">New patient</p>
                <h2>Create profile</h2>
              </div>
            </div>

            <form className="stacked-form" onSubmit={(event) => event.preventDefault()}>
              <label>
                Name
                <input
                  type="text"
                  value={patientForm.name}
                  onChange={(event) => updatePatientForm('name', event.target.value)}
                  placeholder="Mario Rossi"
                  required
                />
              </label>
              <label>
                Age
                <input
                  type="number"
                  min="0"
                  step="1"
                  value={patientForm.age}
                  onChange={(event) => updatePatientForm('age', event.target.value)}
                  required
                />
              </label>
              <label>
                Weight
                <input
                  type="number"
                  min="0"
                  step="0.1"
                  value={patientForm.weight}
                  onChange={(event) => updatePatientForm('weight', event.target.value)}
                  required
                />
              </label>
              <label>
                Profile URL
                <input
                  type="url"
                  value={patientForm.profilePicture}
                  onChange={(event) =>
                    updatePatientForm('profilePicture', event.target.value)
                  }
                  placeholder="https://example.com/photo.jpg"
                />
              </label>
            </form>

            <div className="button-row">
              <button
                type="button"
                onClick={() => void run('create-patient', createPatient, 'Patient created.')}
                disabled={isBusy}
              >
                Create patient
              </button>
              <button
                type="button"
                className="ghost-button"
                onClick={clearPatientForm}
                disabled={isBusy}
              >
                Clear
              </button>
            </div>
          </aside>
        </section>
      )}
    </main>
  )
}

export default App
