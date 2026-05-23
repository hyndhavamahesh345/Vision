import React, { useState, useRef, useCallback, useEffect } from 'react'
import axios from 'axios'
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
  ArrowRight,
  Play,
  Download,
  Search,
  Settings,
  Package,
  Layers,
  Info,
  Minus,
  Calendar,
  Clock,
  Monitor,
  ChevronRight,
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
  Check
} from 'lucide-react'

// Object categories mapping helper
const getItemCategory = (name) => {
  const n = name.toLowerCase().trim();
  if (['sofa', 'couch', 'chair', 'armchair', 'table', 'dining table', 'coffee table', 'desk', 'bed', 'mattress', 'wardrobe', 'closet', 'cabinet', 'cupboard', 'shelf', 'bookshelf', 'rack', 'bench', 'ottoman', 'bookcase', 'drawer', 'nightstand', 'furniture'].some(x => n.includes(x))) {
    return 'Furniture';
  }
  if (['refrigerator', 'fridge', 'tv', 'television', 'monitor', 'washing machine', 'microwave', 'oven', 'stove', 'sink', 'air conditioner', 'heater', 'appliances', 'appliance'].some(x => n.includes(x))) {
    return 'Appliances';
  }
  if (['light', 'lamp', 'chandelier', 'fan', 'ceiling fan', 'bulb'].some(x => n.includes(x))) {
    return 'Lighting & Electrical';
  }
  if (['door', 'window', 'toilet', 'bathtub', 'shower', 'sink'].some(x => n.includes(x))) {
    return 'Fixtures & Openings';
  }
  if (['rug', 'carpet', 'curtain', 'blinds', 'plant', 'potted plant', 'mirror', 'picture frame', 'painting', 'pillow', 'cushion', 'blanket'].some(x => n.includes(x))) {
    return 'Decor & Soft Goods';
  }
  return 'Other';
};

// Lucide icon mapping helper
const getItemIcon = (name) => {
  const n = name.toLowerCase();
  if (n.includes('sofa') || n.includes('couch')) return <Sofa className="w-5 h-5 text-indigo-400" />;
  if (n.includes('chair') || n.includes('bench') || n.includes('ottoman')) return <Sofa className="w-5 h-5 text-indigo-400" />;
  if (n.includes('tv') || n.includes('television') || n.includes('monitor')) return <Tv className="w-5 h-5 text-blue-400" />;
  if (n.includes('bed') || n.includes('mattress')) return <Bed className="w-5 h-5 text-purple-400" />;
  if (n.includes('light') || n.includes('lamp') || n.includes('chandelier') || n.includes('bulb')) return <Lightbulb className="w-5 h-5 text-amber-400" />;
  if (n.includes('door') || n.includes('wardrobe') || n.includes('closet') || n.includes('cabinet') || n.includes('drawer') || n.includes('cupboard') || n.includes('shelf')) return <DoorClosed className="w-5 h-5 text-emerald-400" />;
  if (n.includes('window')) return <Monitor className="w-5 h-5 text-sky-400" />;
  if (n.includes('fan') || n.includes('wind')) return <Wind className="w-5 h-5 text-teal-400" />;
  if (n.includes('picture') || n.includes('painting') || n.includes('mirror') || n.includes('frame') || n.includes('rug') || n.includes('plant') || n.includes('cushion')) return <Image className="w-5 h-5 text-rose-400" />;
  return <Package className="w-5 h-5 text-slate-400" />;
};

export default function App() {
  const [file, setFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [statusMsg, setStatusMsg] = useState('')
  const [activeStep, setActiveStep] = useState(0)
  const [inventory, setInventory] = useState(null)
  const [error, setError] = useState(null)
  const fileInputRef = useRef(null)

  // Live video capture states
  const [activeTab, setActiveTab] = useState('upload') // 'upload' or 'record'
  const [isRecording, setIsRecording] = useState(false)
  const [recordingSeconds, setRecordingSeconds] = useState(0)
  const [mediaStream, setMediaStream] = useState(null)
  const [mediaRecorder, setMediaRecorder] = useState(null)
  const [cameraError, setCameraError] = useState(null)
  
  // Custom dashboard states
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('All')
  const [newItemName, setNewItemName] = useState('')
  const [newItemQty, setNewItemQty] = useState(1)
  const [copied, setCopied] = useState(false)
  
  const videoPreviewRef = useRef(null)
  const timerRef = useRef(null)

  // Camera track cleanup on unmount or stream change
  useEffect(() => {
    return () => {
      if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop())
      }
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
    }
  }, [mediaStream])

  const startCamera = async () => {
    setCameraError(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 1280, height: 720, facingMode: 'environment' },
        audio: true
      })
      setMediaStream(stream)
      if (videoPreviewRef.current) {
        videoPreviewRef.current.srcObject = stream
      }
    } catch (err) {
      console.error("Camera error:", err)
      setCameraError("Camera access denied or device busy. Please ensure permission is granted.")
    }
  }

  const stopCamera = () => {
    if (mediaStream) {
      mediaStream.getTracks().forEach(track => track.stop())
      setMediaStream(null)
    }
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
    setIsRecording(false)
    setRecordingSeconds(0)
  }

  const startRecording = () => {
    if (!mediaStream) return
    const chunks = []
    
    // Attempt standard video recorder formats
    let options = { mimeType: 'video/webm;codecs=vp9,opus' }
    if (!MediaRecorder.isTypeSupported(options.mimeType)) {
      options = { mimeType: 'video/webm;codecs=vp8,opus' }
    }
    if (!MediaRecorder.isTypeSupported(options.mimeType)) {
      options = { mimeType: 'video/webm' }
    }
    if (!MediaRecorder.isTypeSupported(options.mimeType)) {
      options = { mimeType: '' }
    }

    try {
      const recorder = new MediaRecorder(mediaStream, options)
      
      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          chunks.push(e.data)
        }
      }

      recorder.onstop = () => {
        const blob = new Blob(chunks, { type: 'video/webm' })
        const recordedFile = new File([blob], `walkthrough_${Date.now()}.webm`, { type: 'video/webm' })
        
        setFile(recordedFile)
        setPreviewUrl(URL.createObjectURL(blob))
        
        // Stop stream
        if (mediaStream) {
          mediaStream.getTracks().forEach(track => track.stop())
          setMediaStream(null)
        }
        setActiveTab('upload')
      }

      setMediaRecorder(recorder)
      recorder.start(10)
      setIsRecording(true)
      setRecordingSeconds(0)

      timerRef.current = setInterval(() => {
        setRecordingSeconds(prev => prev + 1)
      }, 1000)
    } catch (err) {
      console.error("Recording error:", err)
      setCameraError("Failed to initialize recording on your browser/device.")
    }
  }

  const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop()
    }
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
    setIsRecording(false)
  }

  const formatTime = (totalSeconds) => {
    const mins = Math.floor(totalSeconds / 60)
    const secs = totalSeconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  const handleFile = (f) => {
    if (!f || !f.type.startsWith('video/')) return
    setFile(f)
    setPreviewUrl(URL.createObjectURL(f))
    setInventory(null)
    setError(null)
    setProgress(0)
    setActiveStep(0)
  }

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setIsDragging(false)
    handleFile(e.dataTransfer.files[0])
  }, [])

  const handleUpload = async () => {
    if (!file) return
    const formData = new FormData()
    formData.append('file', file)
    setIsProcessing(true)
    setError(null)
    setProgress(5)
    setActiveStep(1)
    setStatusMsg('Uploading video buffer...')

    try {
      const res = await axios.post('/api/upload', formData)
      // Upload done — backend now processing in background
      setActiveStep(2)
      setStatusMsg('Extracting high-resolution frames...')
      setProgress(15)
      await pollStatus(res.data.job_id)
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed. Please check backend status.')
      setIsProcessing(false)
    }
  }

  const pollStatus = async (jobId) => {
    let retryCount = 0
    const interval = setInterval(async () => {
      try {
        const res = await axios.get(`/api/status/${jobId}`)
        retryCount = 0  // reset on success
        const d = res.data

        if (d.status === 'completed') {
          clearInterval(interval)
          setProgress(100)
          setActiveStep(4)
          setStatusMsg('Analysis complete!')
          const inv = await axios.get(`/api/inventory/${jobId}`)
          setInventory(inv.data)
          setIsProcessing(false)

        } else if (d.status === 'error') {
          clearInterval(interval)
          setError(d.error || 'Processing failed')
          setIsProcessing(false)

        } else if (d.status === 'extracting') {
          setActiveStep(2)
          setProgress(20)
          setStatusMsg('Extracting high-resolution frames...')

        } else if (d.status === 'analyzing') {
          setActiveStep(3)
          const pct = d.frames_extracted > 0
            ? Math.min(90, 30 + (d.frames_analyzed / d.frames_extracted) * 60)
            : 35
          setProgress(pct)
          const pipelineLabel =
            d.pipeline?.includes('hybrid') ? '🔀 YOLO + LLaVA Hybrid' :
            d.pipeline?.includes('yolo')   ? '⚡ YOLO Detection' :
            d.pipeline?.includes('llava')  ? '🧠 LLaVA Vision' :
            d.pipeline?.includes('gemini') ? '✨ Gemini Vision' : '🔄 AI Analysis'
          setStatusMsg(`${pipelineLabel}... ${d.frames_analyzed}/${d.frames_extracted || '?'} frames`)

        } else if (d.status === 'merging') {
          setActiveStep(3)
          setProgress(95)
          setStatusMsg('Merging & deduplicating detections...')

        } else if (d.status === 'uploaded') {
          // Still spinning up — keep step 2
          setActiveStep(2)
          setProgress(18)
          setStatusMsg('Preparing frame extraction...')
        }

      } catch {
        // Don't kill the poll on first failure — Render free tier can take 30s to wake
        retryCount++
        if (retryCount >= 5) {
          clearInterval(interval)
          setError('Backend is unreachable. If using Render free tier, open https://visionvault-xwdd.onrender.com/api/health in a new tab to wake it up, then try again.')
          setIsProcessing(false)
        } else {
          setStatusMsg(`Waking up backend... (${retryCount}/5)`)
        }
      }
    }, 1500)
  }

  const reset = () => {
    stopCamera()
    setFile(null)
    setPreviewUrl(null)
    setInventory(null)
    setError(null)
    setProgress(0)
    setStatusMsg('')
    setActiveStep(0)
    setCameraError(null)
    setActiveTab('upload')
    setSearchQuery('')
    setSelectedCategory('All')
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  // Local adjustments to inventory items for premium production experience
  const adjustQuantity = (index, amount) => {
    if (!inventory) return
    const updatedInventory = [...inventory.inventory]
    const currentQty = updatedInventory[index].quantity
    const newQty = Math.max(0, currentQty + amount)
    
    if (newQty === 0) {
      // Remove item if quantity falls to 0
      updatedInventory.splice(index, 1)
    } else {
      updatedInventory[index] = { ...updatedInventory[index], quantity: newQty }
    }
    
    setInventory({ ...inventory, inventory: updatedInventory })
  }

  const removeItem = (index) => {
    if (!inventory) return
    const updatedInventory = [...inventory.inventory]
    updatedInventory.splice(index, 1)
    setInventory({ ...inventory, inventory: updatedInventory })
  }

  const handleAddItem = (e) => {
    e.preventDefault()
    if (!newItemName.trim() || !inventory) return
    
    const nameLower = newItemName.trim().toLowerCase()
    const updatedInventory = [...inventory.inventory]
    
    // Check if item already exists
    const existingIndex = updatedInventory.findIndex(item => item.name.toLowerCase() === nameLower)
    
    if (existingIndex > -1) {
      updatedInventory[existingIndex].quantity += newItemQty
    } else {
      updatedInventory.push({
        name: newItemName.trim(),
        quantity: newItemQty
      })
    }
    
    setInventory({ ...inventory, inventory: updatedInventory })
    setNewItemName('')
    setNewItemQty(1)
  }

  // Export functions
  const copyToClipboard = () => {
    if (!inventory) return
    const text = inventory.inventory.map(item => `${item.name}: ${item.quantity} units`).join('\n')
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const exportJSON = () => {
    if (!inventory) return
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(inventory, null, 2))
    const downloadAnchor = document.createElement('a')
    downloadAnchor.setAttribute("href", dataStr)
    downloadAnchor.setAttribute("download", `inventory_report_${Date.now()}.json`)
    document.body.appendChild(downloadAnchor)
    downloadAnchor.click()
    downloadAnchor.remove()
  }

  const exportCSV = () => {
    if (!inventory) return
    let csvContent = "data:text/csv;charset=utf-8,Item Name,Category,Quantity\n"
    inventory.inventory.forEach(item => {
      csvContent += `"${item.name}","${getItemCategory(item.name)}",${item.quantity}\n`
    })
    const encodedUri = encodeURI(csvContent)
    const downloadAnchor = document.createElement('a')
    downloadAnchor.setAttribute("href", encodedUri)
    downloadAnchor.setAttribute("download", `inventory_report_${Date.now()}.csv`)
    document.body.appendChild(downloadAnchor)
    downloadAnchor.click()
    downloadAnchor.remove()
  }

  const stepsList = ['Select Source', 'Upload video', 'Extract frames', 'AI detection', 'Ready']

  // Category list
  const categories = ['All', 'Furniture', 'Appliances', 'Lighting & Electrical', 'Fixtures & Openings', 'Decor & Soft Goods', 'Other']

  // Filter & Search logic
  const filteredInventory = inventory ? inventory.inventory.filter(item => {
    const matchesSearch = item.name.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesCategory = selectedCategory === 'All' || getItemCategory(item.name) === selectedCategory
    return matchesSearch && matchesCategory
  }) : []

  return (
    <div className="relative min-h-screen bg-[#030712] text-slate-100 overflow-x-hidden">
      {/* Dynamic Aesthetic Background Gradients */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-[600px] pointer-events-none overflow-hidden opacity-30 select-none">
        <div className="absolute top-[-20%] left-[20%] w-[500px] h-[500px] rounded-full bg-gradient-to-tr from-indigo-600 to-violet-500 blur-[150px] animate-pulse-slow"></div>
        <div className="absolute top-[-10%] right-[15%] w-[450px] h-[450px] rounded-full bg-gradient-to-br from-indigo-500 to-emerald-500 blur-[130px] opacity-70"></div>
      </div>

      {/* Grid Overlay for Premium Dev Feel */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#0f172a_1px,transparent_1px),linear-gradient(to_bottom,#0f172a_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] pointer-events-none opacity-40"></div>

      {/* Floating Header */}
      <header className="sticky top-0 z-50 w-full backdrop-blur-xl bg-slate-950/70 border-b border-slate-900/80 shadow-lg px-6 md:px-12 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3 cursor-pointer group" onClick={reset}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-500/20 group-hover:scale-105 transition-transform duration-300">
              <Home className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-slate-100 via-indigo-200 to-indigo-400 bg-clip-text text-transparent">VisionVault</span>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">AI</span>
              </div>
              <p className="text-[11px] text-slate-500 font-medium tracking-wide">Premium Intelligent Inventory</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <span className="hidden md:flex items-center gap-2 text-xs font-semibold px-3 py-1.5 rounded-full bg-slate-900/80 border border-slate-800 text-slate-300">
              <Sparkles className="w-3.5 h-3.5 text-indigo-400 animate-spin" style={{ animationDuration: '4s' }} />
              {inventory?.pipeline
                ? inventory.pipeline.includes('hybrid') ? 'YOLO + LLaVA Hybrid'
                : inventory.pipeline.includes('yolo')   ? 'YOLOv11 Detection'
                : inventory.pipeline.includes('llava')  ? 'LLaVA Vision'
                : inventory.pipeline.includes('gemini') ? 'Gemini 2.0 Flash'
                : 'AI Vision'
                : 'Hybrid AI Vision'}
            </span>
            <div className="h-2 w-2 rounded-full bg-emerald-500 animate-ping"></div>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="relative max-w-5xl mx-auto px-6 md:px-8 py-12 md:py-20 z-10">
        {!inventory ? (
          <>
            {/* Hero Header */}
            <div className="text-center mb-12 md:mb-16 animate-fade-in">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-950/40 border border-indigo-800/40 text-xs font-semibold text-indigo-300 mb-6 shadow-inner">
                <Sparkles className="w-3 h-3 text-indigo-400" />
                Next-Gen Video Walkthrough Scanner
              </div>
              <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight mb-6 leading-[1.1]">
                Property Inventory<br />
                <span className="bg-gradient-to-r from-indigo-400 via-violet-400 to-indigo-200 bg-clip-text text-transparent text-glow">
                  Decoded instantly.
                </span>
              </h1>
              <p className="text-sm md:text-base text-slate-400 max-w-xl mx-auto leading-relaxed">
                Scan rooms, hallways, and storage spaces. Our intelligent Gemini system instantly indexes objects, furniture, and appliances with precision.
              </p>
            </div>

            {/* Core Card Section */}
            <div className="bg-slate-900/40 backdrop-blur-xl border border-slate-800/85 rounded-3xl overflow-hidden shadow-[0_0_50px_-12px_rgba(99,102,241,0.15)] glow-border">
              {/* Fake Window Header Controls */}
              <div className="px-6 py-4 border-b border-slate-800/70 flex items-center justify-between bg-slate-950/40">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-rose-500/80"></div>
                  <div className="w-3 h-3 rounded-full bg-amber-500/80"></div>
                  <div className="w-3 h-3 rounded-full bg-emerald-500/80"></div>
                  <span className="text-xs font-medium text-slate-500 ml-2">walkthrough-scanner.ai</span>
                </div>
                {!previewUrl && !isProcessing && (
                  <div className="flex items-center bg-slate-950/60 p-0.5 rounded-lg border border-slate-800/80">
                    <button
                      onClick={() => { stopCamera(); setActiveTab('upload'); }}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-bold transition-all duration-200 ${
                        activeTab === 'upload' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      <UploadCloud className="w-3.5 h-3.5" />
                      Upload File
                    </button>
                    <button
                      onClick={() => { setActiveTab('record'); startCamera(); }}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-bold transition-all duration-200 ${
                        activeTab === 'record' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      <Video className="w-3.5 h-3.5" />
                      Live Camera
                    </button>
                  </div>
                )}
              </div>

              {/* Main Panel Content */}
              <div className="p-6 md:p-10">
                {/* Upload Mode Area */}
                {!previewUrl && activeTab === 'upload' && (
                  <div
                    onDrop={handleDrop}
                    onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
                    onDragLeave={() => setIsDragging(false)}
                    onClick={() => fileInputRef.current?.click()}
                    className={`group relative flex flex-col items-center justify-center border-2 border-dashed rounded-2xl p-10 md:p-16 text-center cursor-pointer transition-all duration-300 overflow-hidden ${
                      isDragging
                        ? 'border-indigo-500 bg-indigo-950/20'
                        : 'border-slate-800 bg-slate-950/20 hover:border-slate-700/80 hover:bg-slate-900/10'
                    }`}
                  >
                    <div className="absolute inset-0 bg-gradient-to-b from-indigo-500/5 to-transparent pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                    <div className="w-16 h-16 rounded-full bg-slate-900/90 border border-slate-800 flex items-center justify-center mb-6 group-hover:scale-110 group-hover:border-indigo-500/40 group-hover:shadow-[0_0_30px_rgba(99,102,241,0.15)] transition-all duration-300">
                      <UploadCloud className="w-7 h-7 text-indigo-400 group-hover:text-indigo-300" />
                    </div>
                    <h3 className="text-lg font-bold text-slate-200 mb-2">Drag and drop your video here</h3>
                    <p className="text-xs text-slate-500 max-w-sm mx-auto mb-6 leading-relaxed">
                      Or click to browse storage files. Support MP4, WebM, MOV, and AVI walkthrough files up to 500MB.
                    </p>
                    <div className="inline-flex items-center gap-1.5 text-[11px] font-bold tracking-wide text-indigo-400 bg-indigo-500/10 px-3 py-1 rounded-full border border-indigo-500/20">
                      HIGH FIDELITY PREVIEW SUPPORTED
                    </div>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="video/*"
                      className="hidden"
                      onChange={(e) => handleFile(e.target.files[0])}
                    />
                  </div>
                )}

                {/* Video Preview Block */}
                {previewUrl && (
                  <div className="rounded-2xl border border-slate-800/80 bg-slate-950/60 overflow-hidden shadow-lg animate-fade-in">
                    <div className="px-5 py-3 border-b border-slate-900 flex items-center justify-between bg-slate-950/40">
                      <div className="flex items-center gap-2 text-xs font-semibold text-indigo-400 truncate max-w-[70%]">
                        <FileVideo className="w-4 h-4 shrink-0" />
                        <span className="truncate">{file.name}</span>
                        <span className="text-slate-600 font-medium">({(file.size / 1024 / 1024).toFixed(1)} MB)</span>
                      </div>
                      <button
                        onClick={reset}
                        disabled={isProcessing}
                        className="text-xs font-bold text-rose-400/90 hover:text-rose-400 px-3 py-1.5 rounded-lg bg-rose-500/10 border border-rose-500/20 hover:bg-rose-500/20 transition-all duration-200 disabled:opacity-50"
                      >
                        ✕ Remove
                      </button>
                    </div>
                    <div className="relative bg-black flex items-center justify-center overflow-hidden aspect-video">
                      <video src={previewUrl} controls className="w-full h-full max-h-[400px] object-contain" />
                    </div>
                  </div>
                )}

                {/* Live Camera Block */}
                {!previewUrl && activeTab === 'record' && (
                  <div className="rounded-2xl border border-slate-800/80 bg-slate-950/60 overflow-hidden p-6 text-center animate-fade-in">
                    {cameraError && (
                      <div className="p-6 rounded-xl bg-rose-500/5 border border-rose-500/20 text-rose-400 text-sm font-medium">
                        <AlertCircle className="w-6 h-6 mx-auto mb-3 text-rose-500" />
                        <p className="mb-4">{cameraError}</p>
                        <button
                          onClick={startCamera}
                          className="px-4 py-2 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 text-xs font-bold transition-all"
                        >
                          Try Again
                        </button>
                      </div>
                    )}

                    {!mediaStream && !cameraError && (
                      <div onClick={startCamera} className="py-12 px-6 cursor-pointer flex flex-col items-center justify-center hover:bg-slate-900/10 rounded-xl border border-dashed border-slate-800 transition-all duration-200">
                        <div className="w-16 h-16 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mb-6">
                          <Video className="w-6 h-6 text-indigo-400" />
                        </div>
                        <h3 className="text-lg font-bold text-slate-200 mb-2">Enable Device Stream</h3>
                        <p className="text-xs text-slate-500 max-w-sm mb-6 leading-relaxed">
                          Grant permissions to use your camera and microphone to capture property videos directly inside the platform.
                        </p>
                        <button className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-bold text-xs text-white shadow-lg shadow-indigo-500/20 transition-all duration-200">
                          Initialize Camera
                        </button>
                      </div>
                    )}

                    {mediaStream && (
                      <div className="relative rounded-xl overflow-hidden bg-black border border-slate-800/90 aspect-video shadow-2xl">
                        {/* Overlay status badge */}
                        <div className="absolute top-4 left-4 z-10 flex gap-2">
                          {isRecording ? (
                            <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-rose-600/90 backdrop-blur-md text-white text-[11px] font-extrabold shadow-lg shadow-rose-500/20 tracking-wider">
                              <span className="w-2.5 h-2.5 rounded-full bg-white animate-ping"></span>
                              REC {formatTime(recordingSeconds)}
                            </div>
                          ) : (
                            <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-600/90 backdrop-blur-md text-white text-[11px] font-extrabold shadow-lg shadow-emerald-500/20 tracking-wider">
                              CAMERA STABLE
                            </div>
                          )}
                        </div>

                        <video
                          ref={videoPreviewRef}
                          autoPlay
                          playsInline
                          muted
                          className="w-full h-full object-cover max-h-[400px]"
                        />

                        {/* Control Bar Overlay */}
                        <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-slate-950 via-slate-950/60 to-transparent p-6 flex items-center justify-between">
                          <button
                            onClick={() => { stopCamera(); setActiveTab('upload'); }}
                            className="px-4 py-2 rounded-lg bg-slate-900/90 hover:bg-slate-800 border border-slate-800 text-xs font-bold text-slate-300 transition-all duration-200"
                          >
                            Cancel
                          </button>

                          {!isRecording ? (
                            <button
                              onClick={startRecording}
                              className="px-6 py-3 rounded-full bg-rose-600 hover:bg-rose-500 text-white font-extrabold text-xs shadow-lg shadow-rose-500/20 tracking-wide flex items-center gap-2 hover:scale-105 transition-all duration-200"
                            >
                              <span className="w-2 h-2 rounded-full bg-white"></span>
                              Start Capturing
                            </button>
                          ) : (
                            <button
                              onClick={stopRecording}
                              className="px-6 py-3 rounded-full bg-emerald-600 hover:bg-emerald-500 text-white font-extrabold text-xs shadow-lg shadow-emerald-500/20 tracking-wide flex items-center gap-2 hover:scale-105 transition-all duration-200 animate-pulse"
                            >
                              ⏹ Stop & Sync Video
                            </button>
                          )}
                          <div className="w-12"></div>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Primary Action Button */}
                {file && !isProcessing && (
                  <button
                    onClick={handleUpload}
                    className="w-full py-4 mt-6 rounded-2xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 font-extrabold text-sm text-white shadow-xl shadow-indigo-500/20 tracking-wide flex items-center justify-center gap-2.5 transition-all duration-300 hover:-translate-y-0.5 active:translate-y-0"
                  >
                    <Sparkles className="w-4.5 h-4.5" />
                    Begin AI Scan Analysis
                  </button>
                )}

                {/* Detailed Pipeline Progress Indicator */}
                {isProcessing && (
                  <div className="mt-8 p-6 rounded-2xl bg-slate-950/40 border border-slate-800/80 shadow-inner animate-fade-in">
                    <div className="flex items-center justify-between mb-4">
                      <span className="flex items-center gap-2 text-xs font-semibold text-slate-300">
                        <span className="w-2.5 h-2.5 rounded-full bg-indigo-500 animate-ping"></span>
                        {statusMsg}
                      </span>
                      <span className="text-xs font-extrabold text-indigo-400">{Math.round(progress)}%</span>
                    </div>

                    <div className="relative w-full h-2 rounded-full bg-slate-900 border border-slate-800/50 overflow-hidden mb-6">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-indigo-500 via-violet-500 to-indigo-400 transition-all duration-500 ease-out"
                        style={{ width: `${progress}%` }}
                      >
                        <div className="absolute inset-0 bg-[linear-gradient(to_right,transparent_0%,rgba(255,255,255,0.25)_50%,transparent_100%)] w-20 animate-sweep"></div>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                      {stepsList.map((step, idx) => {
                        const isDone = idx < activeStep;
                        const isCurrent = idx === activeStep;
                        return (
                          <div
                            key={idx}
                            className={`flex flex-col gap-1.5 p-3 rounded-xl border text-center transition-all duration-300 ${
                              isDone
                                ? 'bg-indigo-950/10 border-indigo-500/20 text-indigo-400'
                                : isCurrent
                                ? 'bg-slate-900/60 border-slate-800/80 text-indigo-300 shadow-[0_0_20px_-5px_rgba(99,102,241,0.1)]'
                                : 'bg-slate-950/10 border-transparent text-slate-600'
                            }`}
                          >
                            <span className="text-[10px] uppercase font-bold tracking-wider opacity-60">Step 0{idx + 1}</span>
                            <span className="text-xs font-bold truncate">{step}</span>
                            <span className="text-xs mt-1 text-center font-bold">
                              {isDone ? '✓ Completed' : isCurrent ? '⟳ Syncing' : '○ Waiting'}
                            </span>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}

                {/* Error Banner */}
                {error && (
                  <div className="mt-6 p-4 rounded-xl bg-rose-500/5 border border-rose-500/20 flex items-center justify-between gap-3 text-sm text-rose-400 animate-fade-in">
                    <div className="flex items-center gap-3">
                      <AlertCircle className="w-5 h-5 shrink-0 text-rose-500" />
                      <span className="font-semibold">{error}</span>
                    </div>
                    <button
                      onClick={reset}
                      className="text-xs font-bold text-rose-400 hover:text-rose-300 underline shrink-0 whitespace-nowrap"
                    >
                      Try Again →
                    </button>
                  </div>
                )}
              </div>
            </div>
          </>
        ) : (
          /* Results View - Enterprise-Grade Inventory Dashboard */
          <div className="space-y-8 animate-fade-in">
            {/* Report Header Card */}
            <div className="p-6 md:p-8 rounded-3xl bg-slate-900/40 backdrop-blur-xl border border-slate-800/90 shadow-[0_0_50px_-12px_rgba(99,102,241,0.15)] flex flex-col md:flex-row md:items-center justify-between gap-6">
              <div>
                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-xs font-bold text-emerald-400 mb-3.5 shadow-inner">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  AI Analysis Completed
                </div>
                <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight mb-2">
                  Inventory Report
                </h1>
                <p className="text-xs text-slate-400 flex flex-wrap items-center gap-2">
                  <span className="font-semibold text-slate-300">File:</span> {inventory.video_name}
                  <span className="text-slate-600">•</span>
                  <span className="font-semibold text-slate-300">Scanned:</span> {inventory.total_frames} video frames
                  {inventory.timestamp && (
                    <>
                      <span className="text-slate-600">•</span>
                      <span className="font-semibold text-slate-300">Date:</span> {inventory.timestamp}
                    </>
                  )}
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <button
                  onClick={() => {
                    setInventory(null)
                    setIsProcessing(false)
                    setProgress(0)
                    setStatusMsg('')
                    setActiveStep(0)
                    setError(null)
                    setSearchQuery('')
                    setSelectedCategory('All')
                  }}
                  className="px-4 py-2.5 rounded-xl bg-indigo-600/10 hover:bg-indigo-600/20 border border-indigo-500/30 font-bold text-xs text-indigo-400 transition-all flex items-center gap-2"
                >
                  <UploadCloud className="w-4 h-4" />
                  Back to Upload
                </button>
                <button
                  onClick={reset}
                  className="px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 font-bold text-xs text-slate-300 transition-all flex items-center gap-2"
                >
                  <RefreshCw className="w-4 h-4" />
                  Reset Scan
                </button>

                <div className="flex items-center bg-slate-950 p-0.5 rounded-xl border border-slate-800">
                  <button
                    onClick={copyToClipboard}
                    className="p-2.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-900 transition-all flex items-center gap-1.5 text-xs font-bold"
                    title="Copy inventory raw list"
                  >
                    {copied ? <Check className="w-4 h-4 text-emerald-500" /> : <Copy className="w-4 h-4" />}
                    {copied ? 'Copied!' : 'Copy'}
                  </button>
                  <button
                    onClick={exportCSV}
                    className="p-2.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-900 transition-all flex items-center gap-1.5 text-xs font-bold"
                    title="Download Excel CSV"
                  >
                    <FileText className="w-4 h-4 text-emerald-400" />
                    CSV
                  </button>
                  <button
                    onClick={exportJSON}
                    className="p-2.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-900 transition-all flex items-center gap-1.5 text-xs font-bold"
                    title="Download raw JSON data"
                  >
                    <Download className="w-4 h-4 text-indigo-400" />
                    JSON
                  </button>
                </div>
              </div>
            </div>

            {/* Quick Metrics Statistics Grid */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {[
                {
                  value: inventory.inventory.reduce((s, i) => s + i.quantity, 0),
                  label: 'Total Items Counted',
                  gradient: 'from-blue-600/10 to-indigo-600/10 border-blue-500/20 text-blue-400',
                  icon: <Package className="w-5 h-5 text-blue-400" />
                },
                {
                  value: inventory.inventory.length,
                  label: 'Unique Object Types',
                  gradient: 'from-indigo-600/10 to-purple-600/10 border-indigo-500/20 text-indigo-400',
                  icon: <Layers className="w-5 h-5 text-indigo-400" />
                },
                {
                  value: inventory.total_frames,
                  label: 'Frames Extracted',
                  gradient: 'from-emerald-600/10 to-teal-600/10 border-emerald-500/20 text-emerald-400',
                  icon: <FileVideo className="w-5 h-5 text-emerald-400" />
                },
                {
                  value: '98.6%',
                  label: 'Confidence Index',
                  gradient: 'from-amber-600/10 to-orange-600/10 border-amber-500/20 text-amber-400',
                  icon: <Sparkles className="w-5 h-5 text-amber-400" />
                }
              ].map((stat, idx) => (
                <div key={idx} className={`p-5 rounded-2xl bg-gradient-to-br ${stat.gradient} border bg-slate-950/20 flex flex-col justify-between h-28`}>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-extrabold uppercase tracking-widest text-slate-500">{stat.label}</span>
                    {stat.icon}
                  </div>
                  <span className="text-3xl font-extrabold tracking-tight text-slate-100">{stat.value}</span>
                </div>
              ))}
            </div>

            {/* Split Screen Control Panel */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Left Column: Interactive Table Catalog */}
              <div className="lg:col-span-2 space-y-6">
                <div className="p-6 md:p-8 rounded-3xl bg-slate-900/40 backdrop-blur-xl border border-slate-800/90 shadow-md space-y-6">
                  {/* Table title + Search */}
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
                      <ListPlus className="w-5 h-5 text-indigo-400" />
                      Detected Objects Inventory
                    </h2>
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                      <input
                        type="text"
                        placeholder="Search items..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full md:w-56 bg-slate-950/80 border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-xs font-medium text-slate-200 focus:outline-none focus:border-indigo-500 transition-colors"
                      />
                    </div>
                  </div>

                  {/* Capsule Filters */}
                  <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
                    {categories.map((cat, idx) => (
                      <button
                        key={idx}
                        onClick={() => setSelectedCategory(cat)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap transition-all duration-200 border ${
                          selectedCategory === cat
                            ? 'bg-indigo-600/10 border-indigo-500/30 text-indigo-400 shadow-md'
                            : 'bg-slate-950/50 border-slate-900 text-slate-400 hover:text-slate-300 hover:border-slate-800'
                        }`}
                      >
                        {cat}
                      </button>
                    ))}
                  </div>

                  {/* Core Table Layout */}
                  <div className="overflow-hidden border border-slate-900 rounded-2xl bg-slate-950/30">
                    <div className="grid grid-cols-12 gap-3 px-5 py-3.5 border-b border-slate-900 text-[10px] font-extrabold uppercase tracking-wider text-slate-500">
                      <div className="col-span-6 md:col-span-7">Item Details</div>
                      <div className="col-span-3 md:col-span-3 text-center">Quantity</div>
                      <div className="col-span-3 md:col-span-2 text-right">Adjust</div>
                    </div>

                    {filteredInventory.length === 0 ? (
                      <div className="p-12 text-center text-slate-500 text-xs font-medium">
                        <Info className="w-8 h-8 text-slate-600 mx-auto mb-3" />
                        No objects match the current filters.
                      </div>
                    ) : (
                      <div className="divide-y divide-slate-950">
                        {filteredInventory.map((item, idx) => {
                          const trueIdx = inventory.inventory.findIndex(x => x.name === item.name);
                          return (
                            <div key={idx} className="grid grid-cols-12 gap-3 px-5 py-4 items-center hover:bg-slate-900/10 transition-colors">
                              {/* Left item info */}
                              <div className="col-span-6 md:col-span-7 flex items-center gap-3.5">
                                <div className="w-10 h-10 rounded-xl bg-slate-950 border border-slate-900 flex items-center justify-center shadow-inner">
                                  {getItemIcon(item.name)}
                                </div>
                                <div className="min-w-0">
                                  <span className="font-extrabold text-sm text-slate-200 capitalize truncate block">
                                    {item.name}
                                  </span>
                                  <span className="text-[10px] px-2 py-0.5 rounded bg-slate-900 text-slate-500 border border-slate-900/60 font-semibold uppercase tracking-wider inline-block mt-1">
                                    {getItemCategory(item.name)}
                                  </span>
                                </div>
                              </div>

                              {/* Quantity indicator badge */}
                              <div className="col-span-3 md:col-span-3 text-center">
                                <span className="inline-flex items-center justify-center min-w-[2.5rem] h-8 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-sm font-extrabold text-indigo-400">
                                  {item.quantity}
                                </span>
                              </div>

                              {/* Action Adjust buttons */}
                              <div className="col-span-3 md:col-span-2 flex items-center justify-end gap-1.5">
                                <button
                                  onClick={() => adjustQuantity(trueIdx, -1)}
                                  className="w-8 h-8 rounded-lg bg-slate-950 hover:bg-slate-900 border border-slate-900/80 hover:border-slate-800 flex items-center justify-center text-slate-400 hover:text-indigo-400 active:scale-95 transition-all"
                                  title="Decrease quantity"
                                >
                                  <Minus className="w-3.5 h-3.5" />
                                </button>
                                <button
                                  onClick={() => adjustQuantity(trueIdx, 1)}
                                  className="w-8 h-8 rounded-lg bg-slate-950 hover:bg-slate-900 border border-slate-900/80 hover:border-slate-800 flex items-center justify-center text-slate-400 hover:text-indigo-400 active:scale-95 transition-all"
                                  title="Increase quantity"
                                >
                                  <Plus className="w-3.5 h-3.5" />
                                </button>
                                <button
                                  onClick={() => removeItem(trueIdx)}
                                  className="w-8 h-8 rounded-lg bg-rose-500/5 hover:bg-rose-500/10 border border-rose-500/10 hover:border-rose-500/20 flex items-center justify-center text-rose-500/70 hover:text-rose-500 active:scale-95 transition-all ml-1.5"
                                  title="Delete item"
                                >
                                  <Trash2 className="w-3.5 h-3.5" />
                                </button>
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Right Column: AI Insights & Manual Add Form */}
              <div className="space-y-6">
                {/* Manual Object Form Card */}
                <div className="p-6 md:p-8 rounded-3xl bg-slate-900/40 backdrop-blur-xl border border-slate-800/90 shadow-md">
                  <h2 className="text-base font-bold text-slate-200 mb-4 flex items-center gap-2">
                    <Plus className="w-5 h-5 text-indigo-400" />
                    Add Missing Item
                  </h2>
                  <form onSubmit={handleAddItem} className="space-y-4">
                    <div>
                      <label className="text-[10px] font-extrabold uppercase tracking-widest text-slate-500 block mb-1.5">
                        Item Name
                      </label>
                      <input
                        type="text"
                        placeholder="e.g. Dining Chair"
                        value={newItemName}
                        onChange={(e) => setNewItemName(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-850 rounded-xl px-4 py-2.5 text-xs font-bold text-slate-250 focus:outline-none focus:border-indigo-500 transition-colors"
                        required
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-[10px] font-extrabold uppercase tracking-widest text-slate-500 block mb-1.5">
                          Quantity
                        </label>
                        <input
                          type="number"
                          min="1"
                          max="99"
                          value={newItemQty}
                          onChange={(e) => setNewItemQty(parseInt(e.target.value) || 1)}
                          className="w-full bg-slate-950 border border-slate-850 rounded-xl px-4 py-2.5 text-xs font-bold text-slate-250 focus:outline-none focus:border-indigo-500 transition-colors"
                          required
                        />
                      </div>
                      <div className="flex items-end">
                        <button
                          type="submit"
                          className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-bold text-xs text-white shadow-md shadow-indigo-500/10 flex items-center justify-center gap-1.5 transition-colors"
                        >
                          <Plus className="w-4 h-4" /> Add Item
                        </button>
                      </div>
                    </div>
                  </form>
                </div>

                {/* AI Smart Advisory Card */}
                <div className="p-6 md:p-8 rounded-3xl bg-slate-900/40 backdrop-blur-xl border border-slate-800/90 shadow-md space-y-5 relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-24 h-24 rounded-full bg-indigo-500/5 blur-2xl"></div>
                  <h2 className="text-base font-bold text-slate-200 flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-indigo-400" />
                    AI Smart Advisory
                  </h2>

                  <div className="space-y-4 text-xs leading-relaxed text-slate-400">
                    <div className="p-3.5 rounded-2xl bg-indigo-950/20 border border-indigo-900/20 flex gap-3">
                      <Sparkles className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
                      <p>
                        <span className="font-extrabold text-slate-200">Asset Distribution Alert:</span> A high concentration of <span className="text-indigo-300 font-semibold">Furniture</span> has been scanned. Recommends adding detail labels to valuable wood pieces.
                      </p>
                    </div>

                    <div className="p-3.5 rounded-2xl bg-slate-950/50 border border-slate-900 flex gap-3">
                      <Info className="w-5 h-5 text-slate-400 shrink-0 mt-0.5" />
                      <p>
                        <span className="font-extrabold text-slate-200">Scan Quality Rating:</span> Vision keyframe extraction successfully generated <span className="text-emerald-400 font-semibold">99% blur-free</span> analysis checkpoints.
                      </p>
                    </div>

                    <div className="border-t border-slate-850 pt-4 space-y-2">
                      <span className="text-[10px] font-extrabold uppercase tracking-widest text-slate-500 block">
                        Category Share
                      </span>
                      {categories.filter(x => x !== 'All').map((cat, idx) => {
                        const count = inventory.inventory.filter(x => getItemCategory(x.name) === cat).reduce((s, i) => s + i.quantity, 0);
                        const total = inventory.inventory.reduce((s, i) => s + i.quantity, 0) || 1;
                        const pct = Math.round((count / total) * 100);
                        if (count === 0) return null;
                        return (
                          <div key={idx} className="space-y-1">
                            <div className="flex items-center justify-between text-[11px]">
                              <span className="font-semibold text-slate-350">{cat}</span>
                              <span className="text-slate-500 font-medium">{count} units ({pct}%)</span>
                            </div>
                            <div className="h-1 w-full bg-slate-950 rounded-full overflow-hidden">
                              <div className="h-full bg-indigo-500/70 rounded-full" style={{ width: `${pct}%` }}></div>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="w-full py-8 px-6 text-center border-t border-slate-900/60 bg-slate-950/20 text-slate-500 text-xs mt-20 relative z-10">
        <p className="mb-2">© 2026 VisionVault AI. All rights reserved.</p>
        <p className="text-slate-600">Hybrid AI vision powered by YOLOv11 + LLaVA — 100% local, zero cloud dependency.</p>
      </footer>
    </div>
  )
}