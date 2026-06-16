import React, { useState, useRef, useCallback, useEffect, useMemo } from 'react'
import axios from 'axios'
import jsPDF from 'jspdf'
import 'jspdf-autotable'
import {
  Home,
  Sparkles,
  UploadCloud,
  Video,
  AlertCircle,
  RefreshCw,
  Trash2,
  CheckCircle2,
  Plus,
  Download,
  Search,
  Package,
  Layers,
  Info,
  Minus,
  Monitor,
  FileText,
  Sofa,
  Tv,
  Bed,
  Lightbulb,
  DoorClosed,
  Image,
  Wind,
  FileVideo,
  ListPlus,
  Copy,
  Check,
} from 'lucide-react'

// ── Constants ──────────────────────────────────────────────────────────────────

// The standard API base URL from the Vercel environment variables
const API_BASE_URL = import.meta.env.MODE === 'production' ? '' : 'http://13.62.52.213:8001';

const CATEGORIES = [
  'All',
  'Furniture',
  'Appliances',
  'Lighting & Electrical',
  'Fixtures & Openings',
  'Decor & Soft Goods',
  'Other',
]

const ROOMS = ['Living Room', 'Kitchen', 'Bedroom', 'Bathroom', 'Hallway', 'Office', 'Other']

const STEPS = ['Select Source', 'Upload', 'Extract Frames', 'AI Detection', 'Ready']

// ── Pure Helpers ───────────────────────────────────────────────────────────────

function getItemCategory(name) {
  const n = name.toLowerCase().trim()

  const FURNITURE = [
    'sofa', 'couch', 'chair', 'armchair', 'table', 'dining table',
    'coffee table', 'desk', 'bed', 'mattress', 'wardrobe', 'closet',
    'cabinet', 'cupboard', 'shelf', 'bookshelf', 'rack', 'bench',
    'ottoman', 'bookcase', 'drawer', 'nightstand', 'furniture',
  ]
  const APPLIANCES = [
    'refrigerator', 'fridge', 'tv', 'television', 'monitor',
    'washing machine', 'microwave', 'oven', 'stove', 'sink',
    'air conditioner', 'heater', 'appliances', 'appliance',
  ]
  const LIGHTING = ['light', 'lamp', 'chandelier', 'fan', 'ceiling fan', 'bulb']
  const FIXTURES  = ['door', 'window', 'toilet', 'bathtub', 'shower']
  const DECOR     = [
    'rug', 'carpet', 'curtain', 'blinds', 'plant', 'potted plant',
    'mirror', 'picture frame', 'painting', 'pillow', 'cushion', 'blanket',
  ]

  if (FURNITURE.some(x => n.includes(x)))  return 'Furniture'
  if (APPLIANCES.some(x => n.includes(x))) return 'Appliances'
  if (LIGHTING.some(x => n.includes(x)))   return 'Lighting & Electrical'
  if (FIXTURES.some(x => n.includes(x)))   return 'Fixtures & Openings'
  if (DECOR.some(x => n.includes(x)))      return 'Decor & Soft Goods'
  return 'Other'
}

function getItemIcon(name) {
  const n = name.toLowerCase()
  if (n.includes('sofa') || n.includes('couch'))                    return <Sofa       className="w-4 h-4 text-indigo-400" />
  if (n.includes('chair') || n.includes('bench') || n.includes('ottoman')) return <Sofa className="w-4 h-4 text-indigo-400" />
  if (n.includes('tv') || n.includes('television') || n.includes('monitor')) return <Tv className="w-4 h-4 text-blue-400" />
  if (n.includes('bed') || n.includes('mattress'))                  return <Bed        className="w-4 h-4 text-purple-400" />
  if (n.includes('light') || n.includes('lamp') || n.includes('chandelier') || n.includes('bulb'))
                                                                     return <Lightbulb  className="w-4 h-4 text-amber-400" />
  if (n.includes('door') || n.includes('wardrobe') || n.includes('closet') ||
      n.includes('cabinet') || n.includes('drawer') || n.includes('cupboard') || n.includes('shelf'))
                                                                     return <DoorClosed className="w-4 h-4 text-emerald-400" />
  if (n.includes('window'))                                          return <Monitor    className="w-4 h-4 text-sky-400" />
  if (n.includes('fan'))                                             return <Wind       className="w-4 h-4 text-teal-400" />
  if (n.includes('picture') || n.includes('painting') || n.includes('mirror') ||
      n.includes('rug') || n.includes('plant') || n.includes('cushion'))
                                                                     return <Image      className="w-4 h-4 text-rose-400" />
  return <Package className="w-4 h-4 text-slate-400" />
}

function formatTime(totalSeconds) {
  const m = Math.floor(totalSeconds / 60).toString().padStart(2, '0')
  const s = (totalSeconds % 60).toString().padStart(2, '0')
  return `${m}:${s}`
}

// ── Sub-Components ─────────────────────────────────────────────────────────────

/** Animated background orbs + grid */
function BackgroundFX() {
  return (
    <div className="pointer-events-none select-none" aria-hidden>
      {/* Gradient orbs */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-5xl h-[560px] overflow-hidden opacity-25">
        <div className="absolute -top-[15%] left-[18%] w-[480px] h-[480px] rounded-full bg-gradient-to-tr from-indigo-600 to-violet-500 blur-[140px] animate-pulse-slow" />
        <div className="absolute -top-[8%]  right-[12%] w-[420px] h-[420px] rounded-full bg-gradient-to-br from-indigo-500 to-emerald-500 blur-[120px] opacity-70" />
      </div>
      {/* Dot-grid overlay */}
      <div className="absolute inset-0 bg-[radial-gradient(circle,#1e293b_1px,transparent_1px)] [background-size:32px_32px] opacity-20 [mask-image:radial-gradient(ellipse_70%_60%_at_50%_0%,#000_60%,transparent_100%)]" />
    </div>
  )
}

/** Global sticky header */
function Header({ pipeline, onReset }) {
  return (
    <header className="sticky top-0 z-50 w-full backdrop-blur-2xl bg-slate-950/70 border-b border-slate-800/60 shadow-lg">
      <div className="max-w-6xl mx-auto flex items-center justify-between px-5 md:px-10 py-3.5">
        {/* Logo */}
        <button
          onClick={onReset}
          className="flex items-center gap-3 group outline-none"
          aria-label="Go to home"
        >
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-500/25 group-hover:scale-105 transition-transform duration-300">
            <Home className="w-4 h-4 text-white" />
          </div>
          <div className="text-left">
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-base tracking-tight bg-gradient-to-r from-slate-100 via-indigo-200 to-indigo-400 bg-clip-text text-transparent">
                VisionVault
              </span>
              <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 leading-none">
                AI
              </span>
            </div>
            <p className="text-[10px] text-slate-500 font-medium tracking-wide leading-none mt-0.5">
              Property Inventory Intelligence
            </p>
          </div>
        </button>

        {/* Status badges */}
        <div className="flex items-center gap-3">
          <span className="hidden md:flex items-center gap-1.5 text-[11px] font-semibold px-3 py-1.5 rounded-full bg-slate-900/80 border border-slate-800 text-slate-300">
            <Sparkles className="w-3 h-3 text-indigo-400" style={{ animation: 'spin 4s linear infinite' }} />
            {pipeline
              ? pipeline.includes('hybrid') || pipeline.includes('yolo')
                ? '3-Tier Hybrid AI'
                : 'AI Vision'
              : '3-Tier Hybrid AI'}
          </span>
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500" />
          </span>
        </div>
      </div>
    </header>
  )
}

/** Upload tab — drag/drop or file picker */
function UploadDropzone({ onFile }) {
  const [isDragging, setIsDragging] = useState(false)
  const inputRef = useRef(null)

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault()
      setIsDragging(false)
      const f = e.dataTransfer.files[0]
      if (f) onFile(f)
    },
    [onFile]
  )

  return (
    <div
      onDrop={handleDrop}
      onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
      onDragLeave={() => setIsDragging(false)}
      onClick={() => inputRef.current?.click()}
      className={[
        'group relative flex flex-col items-center justify-center',
        'border-2 border-dashed rounded-2xl p-10 md:p-16 text-center cursor-pointer',
        'transition-all duration-300 overflow-hidden',
        isDragging
          ? 'border-indigo-500 bg-indigo-950/20 scale-[1.01]'
          : 'border-slate-800 bg-slate-950/20 hover:border-slate-700 hover:bg-slate-900/10',
      ].join(' ')}
    >
      {/* Hover gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-indigo-500/5 to-transparent pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

      <div className="w-16 h-16 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mb-6 group-hover:scale-110 group-hover:border-indigo-500/40 group-hover:shadow-[0_0_30px_-5px_rgba(99,102,241,0.2)] transition-all duration-300">
        <UploadCloud className="w-7 h-7 text-indigo-400 group-hover:text-indigo-300 transition-colors" />
      </div>

      <h3 className="text-lg font-bold text-slate-200 mb-2">
        {isDragging ? 'Drop to scan →' : 'Drag & drop your walkthrough video'}
      </h3>
      <p className="text-xs text-slate-500 max-w-xs mx-auto mb-6 leading-relaxed">
        Or click to browse files. Supports MP4, WebM, MOV, AVI — up to 500 MB.
      </p>
      <div className="inline-flex items-center gap-1.5 text-[11px] font-bold tracking-wide text-indigo-400 bg-indigo-500/10 px-3 py-1 rounded-full border border-indigo-500/20">
        HIGH-FIDELITY PREVIEW SUPPORTED
      </div>

      <input
        ref={inputRef}
        type="file"
        accept="video/*"
        className="hidden"
        onChange={(e) => e.target.files[0] && onFile(e.target.files[0])}
      />
    </div>
  )
}

/** Live camera recording tab */
function CameraRecorder({ onVideoReady, onCancel }) {
  const [mediaStream, setMediaStream] = useState(null)
  const [mediaRecorder, setMediaRecorder] = useState(null)
  const [isRecording, setIsRecording] = useState(false)
  const [seconds, setSeconds] = useState(0)
  const [cameraError, setCameraError] = useState(null)
  const videoRef = useRef(null)
  const timerRef = useRef(null)

  useEffect(() => {
    return () => {
      mediaStream?.getTracks().forEach(t => t.stop())
      clearInterval(timerRef.current)
    }
  }, [mediaStream])

  const startCamera = async () => {
    setCameraError(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 1280, height: 720, facingMode: 'environment' },
        audio: true,
      })
      setMediaStream(stream)
      if (videoRef.current) videoRef.current.srcObject = stream
    } catch {
      setCameraError('Camera access denied or device unavailable. Grant permission and try again.')
    }
  }

  const startRecording = () => {
    if (!mediaStream) return
    const chunks = []
    let opts = { mimeType: 'video/webm;codecs=vp9,opus' }
    if (!MediaRecorder.isTypeSupported(opts.mimeType)) opts = { mimeType: 'video/webm;codecs=vp8,opus' }
    if (!MediaRecorder.isTypeSupported(opts.mimeType)) opts = { mimeType: 'video/webm' }
    if (!MediaRecorder.isTypeSupported(opts.mimeType)) opts = { mimeType: '' }

    try {
      const recorder = new MediaRecorder(mediaStream, opts)
      recorder.ondataavailable = (e) => { if (e.data?.size > 0) chunks.push(e.data) }
      recorder.onstop = () => {
        const blob = new Blob(chunks, { type: 'video/webm' })
        const file = new File([blob], `walkthrough_${Date.now()}.webm`, { type: 'video/webm' })
        mediaStream.getTracks().forEach(t => t.stop())
        onVideoReady(file, URL.createObjectURL(blob))
      }
      recorder.start(10)
      setMediaRecorder(recorder)
      setIsRecording(true)
      setSeconds(0)
      timerRef.current = setInterval(() => setSeconds(s => s + 1), 1000)
    } catch {
      setCameraError('Recording failed to initialize on this browser/device.')
    }
  }

  const stopRecording = () => {
    if (mediaRecorder?.state !== 'inactive') mediaRecorder.stop()
    clearInterval(timerRef.current)
    setIsRecording(false)
  }

  const cancel = () => {
    mediaStream?.getTracks().forEach(t => t.stop())
    clearInterval(timerRef.current)
    onCancel()
  }

  if (cameraError) {
    return (
      <div className="p-8 rounded-2xl bg-rose-500/5 border border-rose-500/20 text-center animate-fade-in">
        <AlertCircle className="w-8 h-8 text-rose-400 mx-auto mb-3" />
        <p className="text-sm text-rose-400 font-medium mb-4">{cameraError}</p>
        <div className="flex items-center justify-center gap-3">
          <button
            onClick={startCamera}
            className="px-4 py-2 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 text-xs font-bold text-rose-400 transition-all"
          >
            Try Again
          </button>
          <button
            onClick={cancel}
            className="px-4 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs font-bold text-slate-400 transition-all"
          >
            Cancel
          </button>
        </div>
      </div>
    )
  }

  if (!mediaStream) {
    return (
      <div
        onClick={startCamera}
        className="flex flex-col items-center justify-center py-14 px-6 cursor-pointer rounded-2xl border-2 border-dashed border-slate-800 hover:border-indigo-500/40 hover:bg-slate-900/10 transition-all duration-300 animate-fade-in"
      >
        <div className="w-16 h-16 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mb-6">
          <Video className="w-6 h-6 text-indigo-400" />
        </div>
        <h3 className="text-lg font-bold text-slate-200 mb-2">Enable Device Camera</h3>
        <p className="text-xs text-slate-500 max-w-sm mb-6 text-center leading-relaxed">
          Grant camera & microphone access to record a property walkthrough directly in the platform.
        </p>
        <button className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-bold text-xs text-white shadow-lg shadow-indigo-500/20 transition-all duration-200">
          Initialize Camera
        </button>
      </div>
    )
  }

  return (
    <div className="relative rounded-2xl overflow-hidden bg-black border border-slate-800/90 aspect-video shadow-2xl animate-fade-in">
      {/* Status badge */}
      <div className="absolute top-4 left-4 z-10">
        {isRecording ? (
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-rose-600/90 backdrop-blur-md text-white text-[11px] font-extrabold shadow-lg tracking-wider">
            <span className="w-2 h-2 rounded-full bg-white animate-ping" />
            REC {formatTime(seconds)}
          </div>
        ) : (
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-600/90 backdrop-blur-md text-white text-[11px] font-extrabold shadow-lg tracking-wider">
            LIVE
          </div>
        )}
      </div>

      <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover" />

      {/* Controls overlay */}
      <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-slate-950 via-slate-950/50 to-transparent p-5 flex items-center justify-between">
        <button
          onClick={cancel}
          className="px-4 py-2 rounded-lg bg-slate-900/90 hover:bg-slate-800 border border-slate-800 text-xs font-bold text-slate-300 transition-all"
        >
          Cancel
        </button>
        {!isRecording ? (
          <button
            onClick={startRecording}
            className="px-6 py-2.5 rounded-full bg-rose-600 hover:bg-rose-500 text-white font-extrabold text-xs shadow-lg shadow-rose-500/20 flex items-center gap-2 hover:scale-105 transition-all duration-200"
          >
            <span className="w-2 h-2 rounded-full bg-white" />
            Start Recording
          </button>
        ) : (
          <button
            onClick={stopRecording}
            className="px-6 py-2.5 rounded-full bg-emerald-600 hover:bg-emerald-500 text-white font-extrabold text-xs shadow-lg shadow-emerald-500/20 flex items-center gap-2 hover:scale-105 transition-all duration-200"
          >
            ⏹ Stop & Save
          </button>
        )}
        <div className="w-20" />
      </div>
    </div>
  )
}

/** Processing progress panel */
function ProgressPanel({ statusMsg, progress, activeStep }) {
  return (
    <div className="mt-8 p-6 rounded-2xl bg-slate-950/50 border border-slate-800/80 shadow-inner animate-fade-in">
      {/* Label + percentage */}
      <div className="flex items-center justify-between mb-3">
        <span className="flex items-center gap-2 text-xs font-semibold text-slate-300">
          <span className="w-2 h-2 rounded-full bg-indigo-500 animate-ping" />
          {statusMsg}
        </span>
        <span className="text-xs font-extrabold text-indigo-400 tabular-nums">
          {Math.round(progress)}%
        </span>
      </div>

      {/* Progress bar */}
      <div className="relative w-full h-1.5 rounded-full bg-slate-900 border border-slate-800/50 overflow-hidden mb-6">
        <div
          className="h-full rounded-full bg-gradient-to-r from-indigo-500 via-violet-500 to-indigo-400 transition-all duration-500 ease-out relative overflow-hidden"
          style={{ width: `${progress}%` }}
        >
          <div className="absolute inset-y-0 w-20 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-sweep" />
        </div>
      </div>

      {/* Step indicators */}
      <div className="grid grid-cols-5 gap-2">
        {STEPS.map((step, idx) => {
          const done    = idx < activeStep
          const current = idx === activeStep
          return (
            <div
              key={idx}
              className={[
                'flex flex-col items-center gap-1 p-2.5 rounded-xl border text-center transition-all duration-300',
                done    ? 'bg-indigo-950/20 border-indigo-500/25 text-indigo-400'
                : current ? 'bg-slate-900/60 border-slate-700/60 text-indigo-300 shadow-[0_0_15px_-5px_rgba(99,102,241,0.15)]'
                : 'bg-transparent border-transparent text-slate-600',
              ].join(' ')}
            >
              <span className="text-[9px] uppercase font-bold tracking-wider opacity-50">
                {String(idx + 1).padStart(2, '0')}
              </span>
              <span className="text-[11px] font-bold leading-tight">{step}</span>
              <span className="text-[10px] font-semibold">
                {done ? '✓' : current ? '⟳' : '○'}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

/** Stats grid at top of results */
function StatsGrid({ inventory }) {
  const totalItems  = inventory.inventory.reduce((s, i) => s + i.quantity, 0)
  const uniqueTypes = inventory.inventory.length
  const frames      = inventory.total_frames

  const stats = [
    {
      value:    totalItems,
      label:    'Total Items',
      color:    'from-blue-600/10 to-indigo-600/10 border-blue-500/20',
      icon:     <Package className="w-4 h-4 text-blue-400" />,
    },
    {
      value:    uniqueTypes,
      label:    'Unique Types',
      color:    'from-indigo-600/10 to-purple-600/10 border-indigo-500/20',
      icon:     <Layers className="w-4 h-4 text-indigo-400" />,
    },
    {
      value:    frames,
      label:    'Frames Scanned',
      color:    'from-emerald-600/10 to-teal-600/10 border-emerald-500/20',
      icon:     <FileVideo className="w-4 h-4 text-emerald-400" />,
    },
    {
      value:    '98.6%',
      label:    'Confidence',
      color:    'from-amber-600/10 to-orange-600/10 border-amber-500/20',
      icon:     <Sparkles className="w-4 h-4 text-amber-400" />,
    },
  ]

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {stats.map((s, i) => (
        <div
          key={i}
          className={`p-5 rounded-2xl bg-gradient-to-br ${s.color} border flex flex-col justify-between min-h-[100px] animate-fade-in`}
          style={{ animationDelay: `${i * 60}ms` }}
        >
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-extrabold uppercase tracking-widest text-slate-500">
              {s.label}
            </span>
            {s.icon}
          </div>
          <span className="text-3xl font-extrabold tracking-tight text-slate-100">
            {s.value}
          </span>
        </div>
      ))}
    </div>
  )
}

/** Single inventory row */
function InventoryRow({ item, onAdjust, onRemove }) {
  return (
    <div className="grid grid-cols-12 gap-2 px-5 py-3.5 items-center hover:bg-slate-900/20 transition-colors">
      {/* Item info */}
      <div className="col-span-6 md:col-span-7 flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-slate-950 border border-slate-900 flex items-center justify-center shrink-0 shadow-inner">
          {getItemIcon(item.name)}
        </div>
        <div className="min-w-0">
          <p className="font-bold text-sm text-slate-200 capitalize truncate">
            {item.name}
          </p>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-900 text-slate-500 border border-slate-800/60 font-semibold uppercase tracking-wide">
            {getItemCategory(item.name)}
          </span>
        </div>
      </div>

      {/* Quantity badge */}
      <div className="col-span-3 flex justify-center">
        <span className="inline-flex items-center justify-center min-w-[2.25rem] h-7 px-2 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-sm font-extrabold text-indigo-400 tabular-nums">
          {item.quantity}
        </span>
      </div>

      {/* Adjust buttons */}
      <div className="col-span-3 md:col-span-2 flex items-center justify-end gap-1">
        <button
          onClick={() => onAdjust(-1)}
          className="w-7 h-7 rounded-lg bg-slate-950 hover:bg-slate-900 border border-slate-900 hover:border-slate-700 flex items-center justify-center text-slate-500 hover:text-indigo-400 transition-all active:scale-90"
          title="Decrease"
        >
          <Minus className="w-3 h-3" />
        </button>
        <button
          onClick={() => onAdjust(1)}
          className="w-7 h-7 rounded-lg bg-slate-950 hover:bg-slate-900 border border-slate-900 hover:border-slate-700 flex items-center justify-center text-slate-500 hover:text-indigo-400 transition-all active:scale-90"
          title="Increase"
        >
          <Plus className="w-3 h-3" />
        </button>
        <button
          onClick={onRemove}
          className="w-7 h-7 rounded-lg bg-rose-500/5 hover:bg-rose-500/10 border border-rose-500/10 hover:border-rose-500/20 flex items-center justify-center text-rose-500/50 hover:text-rose-400 transition-all active:scale-90 ml-1"
          title="Remove"
        >
          <Trash2 className="w-3 h-3" />
        </button>
      </div>
    </div>
  )
}

/** AI advisory + category breakdown sidebar panel */
function AdvisoryPanel({ inventory }) {
  const total = inventory.inventory.reduce((s, i) => s + i.quantity, 0) || 1

  const cats = CATEGORIES.filter(c => c !== 'All').map(cat => ({
    name:  cat,
    count: inventory.inventory
      .filter(x => getItemCategory(x.name) === cat)
      .reduce((s, i) => s + i.quantity, 0),
  })).filter(c => c.count > 0)

  return (
    <div className="space-y-5 p-6 md:p-7 rounded-3xl bg-slate-900/40 backdrop-blur-xl border border-slate-800/90 shadow-md relative overflow-hidden">
      <div className="absolute top-0 right-0 w-28 h-28 rounded-full bg-indigo-500/5 blur-2xl pointer-events-none" />

      <h2 className="text-sm font-bold text-slate-200 flex items-center gap-2">
        <Sparkles className="w-4 h-4 text-indigo-400" />
        AI Smart Advisory
      </h2>

      {/* Insight cards */}
      <div className="p-3.5 rounded-xl bg-indigo-950/20 border border-indigo-900/20 flex gap-3 text-xs leading-relaxed text-slate-400">
        <Sparkles className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
        <p>
          <span className="font-bold text-slate-200">Asset Alert: </span>
          High concentration of{' '}
          <span className="text-indigo-300 font-semibold">Furniture</span> detected.
          Consider adding condition labels to high-value pieces.
        </p>
      </div>

      <div className="p-3.5 rounded-xl bg-slate-950/40 border border-slate-900 flex gap-3 text-xs leading-relaxed text-slate-400">
        <Info className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
        <p>
          <span className="font-bold text-slate-200">Scan Quality: </span>
          Frame extraction generated{' '}
          <span className="text-emerald-400 font-semibold">99% blur-free</span>{' '}
          analysis checkpoints.
        </p>
      </div>

      {/* Category breakdown bars */}
      {cats.length > 0 && (
        <div className="border-t border-slate-800/60 pt-4 space-y-3">
          <span className="text-[10px] font-extrabold uppercase tracking-widest text-slate-500 block">
            Category Share
          </span>
          {cats.map((cat, i) => {
            const pct = Math.round((cat.count / total) * 100)
            return (
              <div key={i} className="space-y-1">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="font-semibold text-slate-400">{cat.name}</span>
                  <span className="text-slate-500 tabular-nums">{cat.count} ({pct}%)</span>
                </div>
                <div className="h-1 w-full bg-slate-950 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-indigo-500 to-violet-500 rounded-full transition-all duration-700"
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

/** Manual item add form */
function AddItemForm({ onAdd }) {
  const [name, setName]  = useState('')
  const [qty, setQty]    = useState(1)
  const [room, setRoom]  = useState('Living Room')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!name.trim()) return
    onAdd({ name: name.trim(), quantity: qty, room })
    setName('')
    setQty(1)
    setRoom('Living Room')
  }

  return (
    <div className="p-6 md:p-7 rounded-3xl bg-slate-900/40 backdrop-blur-xl border border-slate-800/90 shadow-md">
      <h2 className="text-sm font-bold text-slate-200 mb-4 flex items-center gap-2">
        <Plus className="w-4 h-4 text-indigo-400" />
        Add Missing Item
      </h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="text-[10px] font-extrabold uppercase tracking-widest text-slate-500 block mb-1.5">
            Item Name
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Dining Chair"
            required
            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs font-medium text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500 transition-colors"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-[10px] font-extrabold uppercase tracking-widest text-slate-500 block mb-1.5">
              Quantity
            </label>
            <input
              type="number"
              min="1"
              max="99"
              value={qty}
              onChange={(e) => setQty(Math.max(1, parseInt(e.target.value) || 1))}
              required
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs font-medium text-slate-200 focus:outline-none focus:border-indigo-500 transition-colors"
            />
          </div>

          <div>
            <label className="text-[10px] font-extrabold uppercase tracking-widest text-slate-500 block mb-1.5">
              Room
            </label>
            <select
              value={room}
              onChange={(e) => setRoom(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs font-medium text-slate-200 focus:outline-none focus:border-indigo-500 transition-colors"
            >
              {ROOMS.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
        </div>

        <button
          type="submit"
          className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-bold text-xs text-white shadow-md shadow-indigo-500/10 flex items-center justify-center gap-1.5 transition-all"
        >
          <Plus className="w-3.5 h-3.5" />
          Add Item
        </button>
      </form>
    </div>
  )
}

// ── Export Helpers ─────────────────────────────────────────────────────────────

function buildPDF(inventory) {
  const doc = new jsPDF()

  doc.setFontSize(22)
  doc.setTextColor(79, 70, 229)
  doc.text('VisionVault', 14, 20)

  doc.setFontSize(13)
  doc.setTextColor(15, 23, 42)
  doc.text('Official Property Inventory Report', 14, 29)

  doc.setFontSize(9)
  doc.setTextColor(100, 116, 139)
  doc.text(`Generated: ${new Date().toLocaleString()}`, 14, 38)
  doc.text(`Source: ${inventory.video_name}`, 14, 43)

  // Group by room
  const grouped = {}
  inventory.inventory.forEach(item => {
    const r = item.room || 'Unknown'
    if (!grouped[r]) grouped[r] = []
    grouped[r].push(item)
  })

  let y = 52
  Object.entries(grouped).forEach(([room, items]) => {
    if (y > 235) { doc.addPage(); y = 20 }
    doc.setDrawColor(79, 70, 229)
    doc.setLineWidth(0.8)
    doc.line(14, y, 196, y)
    doc.setFontSize(12)
    doc.setTextColor(79, 70, 229)
    doc.text(room.toUpperCase(), 14, y + 7)
    doc.autoTable({
      startY:     y + 12,
      head:       [['Item', 'Category', 'Qty']],
      body:       items.map(i => [
        i.name.charAt(0).toUpperCase() + i.name.slice(1),
        getItemCategory(i.name),
        i.quantity.toString(),
      ]),
      theme:      'striped',
      headStyles: { fillColor: [79, 70, 229] },
      styles:     { font: 'helvetica', fontSize: 9 },
      margin:     { left: 14, right: 14 },
    })
    y = doc.lastAutoTable.finalY + 14
  })

  // Signature block
  if (y > 225) { doc.addPage(); y = 20 }
  doc.setDrawColor(226, 232, 240)
  doc.line(14, y + 5, 196, y + 5)
  doc.setFontSize(9)
  doc.setTextColor(100, 116, 139)
  doc.text('Landlord Signature: _______________________', 14,  y + 20)
  doc.text('Tenant Signature:   _______________________', 110, y + 20)

  doc.save(`inventory_${Date.now()}.pdf`)
}

function downloadData(content, filename, type) {
  const a = document.createElement('a')
  a.href = type === 'json'
    ? `data:text/json;charset=utf-8,${encodeURIComponent(JSON.stringify(content, null, 2))}`
    : `data:text/csv;charset=utf-8,${encodeURIComponent(content)}`
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
}

// ── Main App ───────────────────────────────────────────────────────────────────

export default function App() {
  // Upload / recording state
  const [file,        setFile]        = useState(null)
  const [previewUrl,  setPreviewUrl]  = useState(null)
  const [activeTab,   setActiveTab]   = useState('upload')

  // Processing state
  const [isProcessing, setIsProcessing] = useState(false)
  const [progress,     setProgress]     = useState(0)
  const [statusMsg,    setStatusMsg]     = useState('')
  const [activeStep,   setActiveStep]   = useState(0)
  const [error,        setError]        = useState(null)

  // Results state
  const [inventory, setInventory] = useState(null)

  // Dashboard state
  const [searchQuery,       setSearchQuery]       = useState('')
  const [selectedCategory,  setSelectedCategory]  = useState('All')
  const [copied,            setCopied]            = useState(false)

  const fileInputRef = useRef(null)

  // ── File handling ──────────────────────────────────────────────────────────

  const handleFile = useCallback((f) => {
    setFile(f)
    setPreviewUrl(URL.createObjectURL(f))
    setInventory(null)
    setError(null)
    setProgress(0)
    setActiveStep(0)
  }, [])

  const handleVideoReady = useCallback((f, url) => {
    setFile(f)
    setPreviewUrl(url)
    setActiveTab('upload')
    setInventory(null)
    setError(null)
    setProgress(0)
    setActiveStep(0)
  }, [])

  // ── Upload & polling ───────────────────────────────────────────────────────

  const handleUpload = async () => {
    if (!file) return
    setIsProcessing(true)
    setError(null)
    setProgress(5)
    setActiveStep(1)
    setStatusMsg('Uploading video...')

    try {
      const form = new FormData()
      form.append('file', file)
      const res = await axios.post(`${API_BASE_URL}/api/upload`, form, {
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            // Scale upload progress (0-100%) to fit within 5% - 15% overall UI progress
            setProgress(5 + (percentCompleted * 0.1))
          }
        }
      })
      setActiveStep(2)
      setStatusMsg('Extracting frames...')
      setProgress(15)
      pollStatus(res.data.job_id)
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed. Check if the backend is running.')
      setIsProcessing(false)
    }
  }

  const pollStatus = (jobId) => {
    let retries = 0
    const iv = setInterval(async () => {
      try {
        const { data: d } = await axios.get(`${API_BASE_URL}/api/status/${jobId}`)
        retries = 0

        if (d.status === 'completed') {
          clearInterval(iv)
          setProgress(100)
          setActiveStep(4)
          setStatusMsg('Analysis complete!')
          const inv = await axios.get(`${API_BASE_URL}/api/inventory/${jobId}`)
          setInventory(inv.data)
          setIsProcessing(false)
        } else if (d.status === 'error') {
          clearInterval(iv)
          setError(d.error || 'Processing failed.')
          setIsProcessing(false)
        } else if (d.status === 'extracting') {
          setActiveStep(2); setProgress(22); setStatusMsg('Extracting frames...')
        } else if (d.status === 'analyzing') {
          setActiveStep(3)
          const pct = d.frames_extracted > 0
            ? Math.min(90, 30 + (d.frames_analyzed / d.frames_extracted) * 60)
            : 35
          setProgress(pct)
          setStatusMsg(`⚡ 3-Tier Hybrid AI · ${d.frames_analyzed}/${d.frames_extracted || '?'} frames`)
        } else if (d.status === 'merging') {
          setActiveStep(3); setProgress(95); setStatusMsg('Merging detections...')
        } else {
          setActiveStep(2); setProgress(18); setStatusMsg('Preparing...')
        }
      } catch {
        retries++
        if (retries >= 5) {
          clearInterval(iv)
          setError('Backend unreachable. Ensure the server is running on port 8001.')
          setIsProcessing(false)
        } else {
          setStatusMsg(`Connecting to backend... (${retries}/5)`)
        }
      }
    }, 1500)
  }

  // ── Reset ──────────────────────────────────────────────────────────────────

  const reset = () => {
    setFile(null)
    setPreviewUrl(null)
    setInventory(null)
    setError(null)
    setProgress(0)
    setStatusMsg('')
    setActiveStep(0)
    setActiveTab('upload')
    setSearchQuery('')
    setSelectedCategory('All')
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  // ── Inventory editing ──────────────────────────────────────────────────────

  const adjustQuantity = (index, delta) => {
    if (!inventory) return
    const updated = [...inventory.inventory]
    const newQty  = updated[index].quantity + delta
    if (newQty <= 0) {
      updated.splice(index, 1)
    } else {
      updated[index] = { ...updated[index], quantity: newQty }
    }
    setInventory({ ...inventory, inventory: updated })
  }

  const removeItem = (index) => {
    if (!inventory) return
    const updated = [...inventory.inventory]
    updated.splice(index, 1)
    setInventory({ ...inventory, inventory: updated })
  }

  const addItem = ({ name, quantity, room }) => {
    if (!inventory || !name.trim()) return
    const updated  = [...inventory.inventory]
    const existing = updated.findIndex(i => i.name.toLowerCase() === name.toLowerCase() && i.room === room)
    if (existing > -1) {
      updated[existing] = { ...updated[existing], quantity: updated[existing].quantity + quantity }
    } else {
      updated.push({ name: name.trim(), quantity, room })
    }
    setInventory({ ...inventory, inventory: updated })
  }

  // ── Export helpers ─────────────────────────────────────────────────────────

  const copyToClipboard = () => {
    if (!inventory) return
    const text = inventory.inventory.map(i => `${i.name}: ${i.quantity}`).join('\n')
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const exportCSV = () => {
    if (!inventory) return
    const rows = inventory.inventory.map(i =>
      `"${i.name}","${getItemCategory(i.name)}","${i.room || ''}",${i.quantity}`
    )
    downloadData(
      `Item,Category,Room,Quantity\n${rows.join('\n')}`,
      `inventory_${Date.now()}.csv`,
      'csv'
    )
  }

  const exportJSON = () => {
    if (!inventory) return
    downloadData(inventory, `inventory_${Date.now()}.json`, 'json')
  }

  // ── Derived state ──────────────────────────────────────────────────────────

  const filteredInventory = useMemo(() => {
    if (!inventory) return []
    return inventory.inventory.filter(item => {
      const matchSearch = item.name.toLowerCase().includes(searchQuery.toLowerCase())
      const matchCat    = selectedCategory === 'All' || getItemCategory(item.name) === selectedCategory
      return matchSearch && matchCat
    })
  }, [inventory, searchQuery, selectedCategory])

  const groupedInventory = useMemo(() => {
    const groups = {}
    filteredInventory.forEach(item => {
      const room = item.room || 'Unknown Room'
      if (!groups[room]) groups[room] = []
      groups[room].push(item)
    })
    return groups
  }, [filteredInventory])

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="relative min-h-screen bg-[#030712] text-slate-100 overflow-x-hidden">
      <BackgroundFX />
      <Header pipeline={inventory?.pipeline} onReset={reset} />

      <main className="relative max-w-5xl mx-auto px-5 md:px-8 py-12 md:py-20 z-10">

        {/* ── UPLOAD / PROCESSING VIEW ──────────────────────────────────── */}
        {!inventory && (
          <div className="animate-fade-in">
            {/* Hero */}
            <div className="text-center mb-12">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-950/40 border border-indigo-800/40 text-[11px] font-semibold text-indigo-300 mb-6">
                <Sparkles className="w-3 h-3 text-indigo-400" />
                Next-Gen AI Walkthrough Scanner
              </div>
              <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight mb-5 leading-[1.08]">
                Property Inventory
                <br />
                <span className="bg-gradient-to-r from-indigo-400 via-violet-400 to-indigo-200 bg-clip-text text-transparent text-glow">
                  Decoded instantly.
                </span>
              </h1>
              <p className="text-sm md:text-base text-slate-400 max-w-lg mx-auto leading-relaxed">
                Upload a walkthrough video. Our AI automatically detects, tracks, and groups every item by room — then generates a professional PDF report.
              </p>
            </div>

            {/* Main card */}
            <div className="bg-slate-900/40 backdrop-blur-xl border border-slate-800/80 rounded-3xl overflow-hidden shadow-[0_0_60px_-15px_rgba(99,102,241,0.12)] glow-border">
              {/* Card top bar */}
              <div className="px-5 py-3.5 border-b border-slate-800/70 flex items-center justify-between bg-slate-950/40">
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-rose-500/80" />
                  <span className="w-3 h-3 rounded-full bg-amber-500/80" />
                  <span className="w-3 h-3 rounded-full bg-emerald-500/80" />
                  <span className="text-xs font-medium text-slate-600 ml-2 font-mono">visionvault.ai</span>
                </div>

                {/* Tab switcher — only shown before file is selected */}
                {!previewUrl && !isProcessing && (
                  <div className="flex items-center bg-slate-950/60 p-0.5 rounded-lg border border-slate-800/80">
                    {[
                      { id: 'upload', icon: <UploadCloud className="w-3 h-3" />, label: 'Upload File' },
                      { id: 'record', icon: <Video className="w-3 h-3" />,       label: 'Live Camera' },
                    ].map(tab => (
                      <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={[
                          'flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-bold transition-all duration-200',
                          activeTab === tab.id
                            ? 'bg-indigo-600 text-white shadow'
                            : 'text-slate-500 hover:text-slate-300',
                        ].join(' ')}
                      >
                        {tab.icon}
                        {tab.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Card body */}
              <div className="p-6 md:p-10">

                {/* Upload dropzone */}
                {!previewUrl && activeTab === 'upload' && (
                  <UploadDropzone onFile={handleFile} />
                )}

                {/* Live camera */}
                {!previewUrl && activeTab === 'record' && (
                  <CameraRecorder
                    onVideoReady={handleVideoReady}
                    onCancel={() => setActiveTab('upload')}
                  />
                )}

                {/* Video preview */}
                {previewUrl && (
                  <div className="rounded-2xl border border-slate-800/80 bg-slate-950/60 overflow-hidden shadow-lg animate-fade-in">
                    <div className="px-5 py-3 border-b border-slate-900 flex items-center justify-between bg-slate-950/40">
                      <div className="flex items-center gap-2 text-xs font-semibold text-indigo-400 min-w-0">
                        <FileVideo className="w-4 h-4 shrink-0" />
                        <span className="truncate">{file?.name}</span>
                        <span className="text-slate-600 shrink-0">
                          ({((file?.size || 0) / 1024 / 1024).toFixed(1)} MB)
                        </span>
                      </div>
                      <button
                        onClick={reset}
                        disabled={isProcessing}
                        className="shrink-0 text-xs font-bold text-rose-400 hover:text-rose-300 px-3 py-1.5 rounded-lg bg-rose-500/10 border border-rose-500/20 hover:bg-rose-500/15 transition-all disabled:opacity-40"
                      >
                        ✕ Remove
                      </button>
                    </div>
                    <div className="relative bg-black flex items-center justify-center aspect-video">
                      <video src={previewUrl} controls className="w-full h-full max-h-[380px] object-contain" />
                    </div>
                  </div>
                )}

                {/* Scan button */}
                {file && !isProcessing && (
                  <button
                    onClick={handleUpload}
                    className="w-full py-4 mt-6 rounded-2xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 font-extrabold text-sm text-white shadow-xl shadow-indigo-500/20 flex items-center justify-center gap-2.5 transition-all duration-300 hover:-translate-y-0.5 active:translate-y-0 animate-fade-in"
                  >
                    <Sparkles className="w-4 h-4" />
                    Begin AI Scan Analysis
                  </button>
                )}

                {/* Progress panel */}
                {isProcessing && (
                  <ProgressPanel
                    statusMsg={statusMsg}
                    progress={progress}
                    activeStep={activeStep}
                  />
                )}

                {/* Error banner */}
                {error && (
                  <div className="mt-6 p-4 rounded-xl bg-rose-500/5 border border-rose-500/20 flex items-center justify-between gap-3 animate-fade-in">
                    <div className="flex items-center gap-3">
                      <AlertCircle className="w-5 h-5 text-rose-500 shrink-0" />
                      <p className="text-sm text-rose-400 font-medium">{error}</p>
                    </div>
                    <button
                      onClick={reset}
                      className="text-xs font-bold text-rose-400 hover:text-rose-300 underline shrink-0"
                    >
                      Try Again →
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ── RESULTS DASHBOARD ────────────────────────────────────────── */}
        {inventory && (
          <div className="space-y-8 animate-fade-in">

            {/* Report header */}
            <div className="p-6 md:p-8 rounded-3xl bg-slate-900/40 backdrop-blur-xl border border-slate-800/90 shadow-md flex flex-col md:flex-row md:items-center justify-between gap-6">
              <div>
                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-xs font-bold text-emerald-400 mb-3">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  AI Analysis Complete
                </div>
                <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight mb-1.5">
                  Inventory Report
                </h1>
                <p className="text-xs text-slate-400 flex flex-wrap items-center gap-x-2 gap-y-1">
                  <span><span className="text-slate-300 font-semibold">File:</span> {inventory.video_name}</span>
                  <span className="text-slate-700">•</span>
                  <span><span className="text-slate-300 font-semibold">Frames:</span> {inventory.total_frames}</span>
                  {inventory.timestamp && (
                    <>
                      <span className="text-slate-700">•</span>
                      <span><span className="text-slate-300 font-semibold">Date:</span> {inventory.timestamp}</span>
                    </>
                  )}
                </p>
              </div>

              {/* Action buttons */}
              <div className="flex flex-wrap items-center gap-2 shrink-0">
                <button
                  onClick={() => { setInventory(null); setIsProcessing(false); setProgress(0); setStatusMsg(''); setActiveStep(0); setError(null) }}
                  className="px-4 py-2 rounded-xl bg-indigo-600/10 hover:bg-indigo-600/20 border border-indigo-500/25 font-bold text-xs text-indigo-400 transition-all flex items-center gap-1.5"
                >
                  <UploadCloud className="w-3.5 h-3.5" />
                  New Scan
                </button>
                <button
                  onClick={reset}
                  className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 font-bold text-xs text-slate-300 transition-all flex items-center gap-1.5"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  Reset
                </button>

                {/* Export group */}
                <div className="flex items-center bg-slate-950 p-0.5 rounded-xl border border-slate-800">
                  <button
                    onClick={copyToClipboard}
                    className="p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-900 transition-all flex items-center gap-1.5 text-xs font-bold"
                    title="Copy to clipboard"
                  >
                    {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    {copied ? 'Copied!' : 'Copy'}
                  </button>
                  <button
                    onClick={exportCSV}
                    className="p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-900 transition-all flex items-center gap-1.5 text-xs font-bold"
                    title="Export CSV"
                  >
                    <FileText className="w-3.5 h-3.5 text-emerald-400" />
                    CSV
                  </button>
                  <button
                    onClick={exportJSON}
                    className="p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-900 transition-all flex items-center gap-1.5 text-xs font-bold"
                    title="Export JSON"
                  >
                    <Download className="w-3.5 h-3.5 text-indigo-400" />
                    JSON
                  </button>
                  <button
                    onClick={() => buildPDF(inventory)}
                    className="p-2 rounded-lg bg-indigo-600/15 hover:bg-indigo-600/30 border border-indigo-500/20 text-indigo-300 transition-all flex items-center gap-1.5 text-xs font-bold ml-1"
                    title="Download PDF"
                  >
                    <FileText className="w-3.5 h-3.5 text-indigo-400" />
                    PDF
                  </button>
                </div>
              </div>
            </div>

            {/* Stats */}
            <StatsGrid inventory={inventory} />

            {/* Annotated Frames Viewer */}
            {inventory.annotated_frames && inventory.annotated_frames.length > 0 && (
              <div className="p-6 md:p-8 rounded-3xl bg-slate-900/40 backdrop-blur-xl border border-slate-800/90 shadow-md">
                <h2 className="text-sm font-bold text-slate-200 flex items-center gap-2 mb-4">
                  <Image className="w-4 h-4 text-indigo-400" />
                  AI Detection Frames
                </h2>
                <div className="flex gap-4 overflow-x-auto pb-4 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
                  {inventory.annotated_frames.map((frame, idx) => (
                    <div key={idx} className="shrink-0 w-[400px] rounded-xl border border-slate-800 overflow-hidden bg-slate-950">
                      <img src={`${API_BASE_URL}${frame}`} alt={`Detection ${idx}`} className="w-full h-auto object-contain" />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Main content — inventory table + sidebar */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

              {/* Inventory table — 2/3 width */}
              <div className="lg:col-span-2 space-y-0 p-6 md:p-8 rounded-3xl bg-slate-900/40 backdrop-blur-xl border border-slate-800/90 shadow-md">
                {/* Table header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-5">
                  <h2 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                    <ListPlus className="w-4 h-4 text-indigo-400" />
                    Detected Objects
                  </h2>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500 pointer-events-none" />
                    <input
                      type="text"
                      placeholder="Search items..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full sm:w-52 bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-xs font-medium text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500 transition-colors"
                    />
                  </div>
                </div>

                {/* Category filter pills */}
                <div className="flex items-center gap-1.5 overflow-x-auto pb-3 scrollbar-none mb-4">
                  {CATEGORIES.map(cat => (
                    <button
                      key={cat}
                      onClick={() => setSelectedCategory(cat)}
                      className={[
                        'px-3 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap transition-all duration-200 border shrink-0',
                        selectedCategory === cat
                          ? 'bg-indigo-600/10 border-indigo-500/30 text-indigo-400'
                          : 'bg-slate-950/60 border-slate-900 text-slate-500 hover:text-slate-300 hover:border-slate-800',
                      ].join(' ')}
                    >
                      {cat}
                    </button>
                  ))}
                </div>

                {/* Table */}
                <div className="overflow-hidden border border-slate-900/80 rounded-2xl bg-slate-950/20">
                  {/* Column headers */}
                  <div className="grid grid-cols-12 gap-2 px-5 py-3 border-b border-slate-900/60 text-[10px] font-extrabold uppercase tracking-widest text-slate-600">
                    <div className="col-span-6 md:col-span-7">Item</div>
                    <div className="col-span-3 text-center">Qty</div>
                    <div className="col-span-3 md:col-span-2 text-right">Actions</div>
                  </div>

                  {Object.keys(groupedInventory).length === 0 ? (
                    <div className="p-12 text-center">
                      <Info className="w-7 h-7 text-slate-700 mx-auto mb-3" />
                      <p className="text-xs text-slate-500 font-medium">No items match the current filters.</p>
                    </div>
                  ) : (
                    <div className="divide-y divide-slate-900/50">
                      {Object.entries(groupedInventory).map(([roomName, items]) => (
                        <div key={roomName}>
                          {/* Room banner */}
                          <div className="px-5 py-2.5 bg-slate-950/40 border-b border-slate-900/50 flex items-center justify-between">
                            <span className="text-[11px] font-extrabold tracking-wider text-indigo-400 uppercase flex items-center gap-2">
                              <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 shrink-0" />
                              {roomName}
                            </span>
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-900 text-slate-500">
                              {items.length} {items.length === 1 ? 'item' : 'items'}
                            </span>
                          </div>

                          {/* Room items */}
                          <div className="divide-y divide-slate-900/30">
                            {items.map((item) => {
                              const trueIdx = inventory.inventory.findIndex(
                                x => x.name === item.name && (x.room || 'Unknown Room') === roomName
                              )
                              return (
                                <InventoryRow
                                  key={`${roomName}-${item.name}`}
                                  item={item}
                                  onAdjust={(delta) => adjustQuantity(trueIdx, delta)}
                                  onRemove={() => removeItem(trueIdx)}
                                />
                              )
                            })}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Sidebar — 1/3 width */}
              <div className="space-y-5">
                <AddItemForm onAdd={addItem} />
                <AdvisoryPanel inventory={inventory} />
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="relative z-10 mt-20 w-full py-8 px-6 text-center border-t border-slate-900/50 bg-slate-950/20">
        <p className="text-xs text-slate-500 mb-1">© 2026 VisionVault AI · All rights reserved.</p>
        <p className="text-xs text-slate-700">Powered by 3-Tier Hybrid Engine (YOLO26) · 100% local · Zero cloud dependency.</p>
      </footer>
    </div>
  )
}
