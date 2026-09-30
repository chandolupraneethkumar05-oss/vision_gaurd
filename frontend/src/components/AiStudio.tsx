import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Camera, UploadCloud, Play, Pause, RefreshCw, Layers, ShieldCheck, Sparkles, AlertCircle } from 'lucide-react';

interface Detection {
  bbox: [number, number, number, number];
  class: string;
  confidence: number;
  color: string;
}

interface PlateResult {
  bbox: [number, number, number, number];
  text: string;
  confidence: number;
  category: string;
  vehicle_class?: string;
}

interface StudioResponse {
  status: string;
  resolution: string;
  inference_ms: number;
  vehicle_count: number;
  class_breakdown: Record<string, number>;
  detections: Detection[];
  plates: PlateResult[];
  annotated_image: string;
}

interface SampleScene {
  id: string;
  name: string;
  description: string;
  traffic_density: string;
  lanes: number;
}

const API_BASE = 'http://localhost:8000';

export const AiStudio: React.FC = () => {
  const [activeMode, setActiveMode] = useState<'webcam' | 'upload' | 'samples'>('samples');
  const [confidence, setConfidence] = useState<number>(0.35);
  const [detectPlates, setDetectPlates] = useState<boolean>(true);
  
  // Streaming state
  const [isWebcamActive, setIsWebcamActive] = useState<boolean>(false);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [webcamError, setWebcamError] = useState<string | null>(null);

  // Analysis result
  const [result, setResult] = useState<StudioResponse | null>(null);
  const [sampleScenes, setSampleScenes] = useState<SampleScene[]>([]);
  const [activeSampleId, setActiveSampleId] = useState<string>('');

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const loopRef = useRef<number | null>(null);

  // Load sample scenes on mount
  useEffect(() => {
    fetch(`${API_BASE}/api/studio/samples`)
      .then((r) => r.json())
      .then((data) => {
        if (data.scenes && data.scenes.length > 0) {
          setSampleScenes(data.scenes);
          // Auto-load first scene
          loadSampleScene(data.scenes[0].id);
        }
      })
      .catch((err) => console.warn('Could not load sample scenes:', err));
  }, []);

  // Stop webcam stream cleanly when switching away or unmounting
  const stopWebcam = useCallback(() => {
    if (loopRef.current) {
      window.cancelAnimationFrame(loopRef.current);
      loopRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsWebcamActive(false);
  }, []);

  useEffect(() => {
    return () => {
      stopWebcam();
    };
  }, [stopWebcam]);

  // Start webcam
  const startWebcam = async () => {
    stopWebcam();
    setWebcamError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 } },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }
      setIsWebcamActive(true);
      startWebcamLoop();
    } catch (err: unknown) {
      console.error('Webcam access error:', err);
      const errorMsg = err instanceof Error ? err.message : 'Webcam permission denied or no camera device found.';
      setWebcamError(errorMsg);
      setIsWebcamActive(false);
    }
  };

  // Webcam inference loop
  const lastProcessedTime = useRef<number>(0);
  const startWebcamLoop = () => {
    const processFrame = async () => {
      const now = performance.now();
      // Process every 250ms (~4 FPS) to keep UI ultra-responsive
      if (videoRef.current && canvasRef.current && now - lastProcessedTime.current > 250) {
        const video = videoRef.current;
        const canvas = canvasRef.current;
        if (video.videoWidth > 0 && video.videoHeight > 0) {
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          const ctx = canvas.getContext('2d');
          if (ctx) {
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            const b64 = canvas.toDataURL('image/jpeg', 0.7);
            lastProcessedTime.current = now;
            try {
              const res = await fetch(`${API_BASE}/api/studio/detect-frame`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  image_base64: b64,
                  confidence,
                  detect_plates: detectPlates,
                }),
              });
              if (res.ok) {
                const data: StudioResponse = await res.json();
                setResult(data);
              }
            } catch (err) {
              console.warn('Frame processing failed:', err);
            }
          }
        }
      }
      loopRef.current = window.requestAnimationFrame(processFrame);
    };
    loopRef.current = window.requestAnimationFrame(processFrame);
  };

  // Process uploaded image file
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsProcessing(true);
    const reader = new FileReader();
    reader.onload = async (event) => {
      const b64 = event.target?.result as string;
      try {
        const res = await fetch(`${API_BASE}/api/studio/detect-frame`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            image_base64: b64,
            confidence,
            detect_plates: detectPlates,
          }),
        });
        if (res.ok) {
          const data: StudioResponse = await res.json();
          setResult(data);
        }
      } catch (err) {
        console.error('Upload detection failed:', err);
      } finally {
        setIsProcessing(false);
      }
    };
    reader.readAsDataURL(file);
  };

  // Load sample scene
  const loadSampleScene = async (sceneId: string) => {
    setIsProcessing(true);
    setActiveSampleId(sceneId);
    try {
      const sceneRes = await fetch(`${API_BASE}/api/studio/sample-scene/${sceneId}`);
      const sceneData = await sceneRes.json();
      
      const detRes = await fetch(`${API_BASE}/api/studio/detect-frame`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image_base64: sceneData.image_base64,
          confidence,
          detect_plates: detectPlates,
        }),
      });
      if (detRes.ok) {
        const data: StudioResponse = await detRes.json();
        setResult(data);
      }
    } catch (err) {
      console.error('Failed to load sample scene:', err);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Studio Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--color-border-subtle)] pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-bold text-[var(--color-forest)] font-serif">
              AI VIDEO & WEBCAM STUDIO
            </h2>
            <span className="text-[10px] px-1.5 py-0.5 rounded font-mono font-bold bg-[var(--color-forest-subtle)] text-[var(--color-forest)] border border-[#C4DCC8]">
              LIVE INFERENCE
            </span>
          </div>
          <p className="text-xs text-[var(--color-text-muted)]">
            Test real-time deep-learning vehicle detection, multi-class breakdown, and Indian ANPR on live webcams or traffic video clips.
          </p>
        </div>

        {/* Mode Selector Tabs */}
        <div className="flex items-center gap-1 p-1 bg-[var(--color-surface)] border border-[var(--color-border-subtle)] rounded-lg">
          <button
            onClick={() => {
              stopWebcam();
              setActiveMode('samples');
            }}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition-colors ${
              activeMode === 'samples'
                ? 'bg-[var(--color-forest)] text-white shadow-xs'
                : 'text-[var(--color-text-muted)] hover:text-black'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Demo Scenes</span>
          </button>

          <button
            onClick={() => {
              stopWebcam();
              setActiveMode('upload');
            }}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition-colors ${
              activeMode === 'upload'
                ? 'bg-[var(--color-forest)] text-white shadow-xs'
                : 'text-[var(--color-text-muted)] hover:text-black'
            }`}
          >
            <UploadCloud className="w-3.5 h-3.5" />
            <span>Upload Media</span>
          </button>

          <button
            onClick={() => {
              setActiveMode('webcam');
            }}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition-colors ${
              activeMode === 'webcam'
                ? 'bg-[var(--color-forest)] text-white shadow-xs'
                : 'text-[var(--color-text-muted)] hover:text-black'
            }`}
          >
            <Camera className="w-3.5 h-3.5" />
            <span>Live Webcam</span>
          </button>
        </div>
      </div>

      {/* Main Studio Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Video / Detection Feed Monitor */}
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-[var(--color-surface)] border border-[var(--color-border-subtle)] rounded-lg overflow-hidden shadow-xs">
            {/* Monitor Header Bar */}
            <div className="px-4 py-2.5 bg-[var(--color-canvas-alt)] border-b border-[var(--color-border-subtle)] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className={`w-2.5 h-2.5 rounded-full ${isWebcamActive ? 'bg-red-500 animate-pulse' : 'bg-emerald-600'}`}></span>
                <span className="text-xs font-mono font-bold uppercase tracking-wider text-[var(--color-text-main)]">
                  {activeMode === 'webcam'
                    ? isWebcamActive
                      ? 'LIVE WEBCAM STREAM'
                      : 'WEBCAM STANDBY'
                    : activeMode === 'upload'
                    ? 'CUSTOM MEDIA STREAM'
                    : `SCENE: ${activeSampleId.toUpperCase()}`}
                </span>
              </div>

              {result && (
                <div className="flex items-center gap-3 text-[11px] font-mono text-[var(--color-text-muted)]">
                  <span>RES: {result.resolution}</span>
                  <span>INFERENCE: <strong className="text-[var(--color-forest)]">{result.inference_ms}ms</strong></span>
                </div>
              )}
            </div>

            {/* Video Viewport */}
            <div className="relative aspect-video bg-neutral-900 flex items-center justify-center overflow-hidden">
              {/* Hidden elements for webcam capture */}
              <video ref={videoRef} className="hidden" playsInline muted autoPlay />
              <canvas ref={canvasRef} className="hidden" />

              {/* Render Annotated Result */}
              {result?.annotated_image ? (
                <img
                  src={result.annotated_image}
                  alt="VisionGuard AI Detection Feed"
                  className="w-full h-full object-contain"
                />
              ) : isProcessing ? (
                <div className="flex flex-col items-center gap-3 text-neutral-400">
                  <RefreshCw className="w-8 h-8 animate-spin text-[var(--color-forest)]" />
                  <p className="text-xs font-mono">Running Deep-Learning Inference...</p>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-2 text-neutral-400">
                  <Camera className="w-10 h-10 stroke-1" />
                  <p className="text-xs font-mono">Select a mode or start camera to begin stream</p>
                </div>
              )}

              {/* Live Overlay Badge */}
              {isWebcamActive && (
                <div className="absolute top-3 left-3 bg-red-600 text-white text-[10px] font-mono px-2 py-0.5 rounded flex items-center gap-1.5 shadow-sm">
                  <span className="w-1.5 h-1.5 rounded-full bg-white animate-ping"></span>
                  <span>WEBCAM LIVE</span>
                </div>
              )}
            </div>

            {/* Controls Bar */}
            <div className="p-4 bg-[var(--color-surface)] border-t border-[var(--color-border-subtle)] flex flex-wrap items-center justify-between gap-4">
              {/* Webcam Controls */}
              {activeMode === 'webcam' && (
                <div className="flex items-center gap-2">
                  {!isWebcamActive ? (
                    <button
                      onClick={startWebcam}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[var(--color-forest)] text-white text-xs font-medium hover:bg-opacity-90 shadow-xs"
                    >
                      <Play className="w-3.5 h-3.5" />
                      <span>Start Webcam</span>
                    </button>
                  ) : (
                    <button
                      onClick={stopWebcam}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-red-700 text-white text-xs font-medium hover:bg-opacity-90 shadow-xs"
                    >
                      <Pause className="w-3.5 h-3.5" />
                      <span>Stop Stream</span>
                    </button>
                  )}
                  {webcamError && (
                    <div className="flex items-center gap-1 text-xs text-red-600">
                      <AlertCircle className="w-3.5 h-3.5" />
                      <span>{webcamError}</span>
                    </div>
                  )}
                </div>
              )}

              {/* Upload Controls */}
              {activeMode === 'upload' && (
                <div className="flex items-center gap-3">
                  <label className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[var(--color-forest)] text-white text-xs font-medium cursor-pointer hover:bg-opacity-90 shadow-xs">
                    <UploadCloud className="w-3.5 h-3.5" />
                    <span>Upload Image / Video Frame</span>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleFileUpload}
                      className="hidden"
                    />
                  </label>
                  <span className="text-xs text-[var(--color-text-muted)]">
                    Supported: JPG, PNG, WEBP (under 10MB)
                  </span>
                </div>
              )}

              {/* Sample Scene Buttons */}
              {activeMode === 'samples' && (
                <div className="flex flex-wrap items-center gap-2">
                  {sampleScenes.map((sc) => (
                    <button
                      key={sc.id}
                      onClick={() => loadSampleScene(sc.id)}
                      className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                        activeSampleId === sc.id
                          ? 'bg-[var(--color-forest)] text-white'
                          : 'bg-[var(--color-canvas-alt)] text-[var(--color-text-main)] hover:bg-[#EBE5D8] border border-[var(--color-border-subtle)]'
                      }`}
                    >
                      {sc.name}
                    </button>
                  ))}
                </div>
              )}

              {/* Sliders: Confidence & ANPR toggle */}
              <div className="flex items-center gap-4 text-xs font-mono ml-auto">
                <div className="flex items-center gap-2">
                  <span className="text-[var(--color-text-muted)]">CONF:</span>
                  <input
                    type="range"
                    min="0.15"
                    max="0.85"
                    step="0.05"
                    value={confidence}
                    onChange={(e) => setConfidence(parseFloat(e.target.value))}
                    className="w-20 accent-[var(--color-forest)]"
                  />
                  <span className="font-bold text-[var(--color-forest)]">{Math.round(confidence * 100)}%</span>
                </div>

                <label className="flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={detectPlates}
                    onChange={(e) => setDetectPlates(e.target.checked)}
                    className="rounded text-[var(--color-forest)] focus:ring-0"
                  />
                  <span>ANPR</span>
                </label>
              </div>
            </div>
          </div>
        </div>

        {/* Right Col: Live Telemetry, Class Breakdown & ANPR Badges */}
        <div className="space-y-4">
          {/* Total Vehicles Detected Summary Card */}
          <div className="bg-[var(--color-surface)] border border-[var(--color-border-subtle)] rounded-lg p-4 shadow-xs">
            <div className="flex items-center justify-between pb-3 border-b border-[var(--color-border-subtle)]">
              <span className="text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-wider">
                VEHICLES IN FRAME
              </span>
              <span className="text-2xl font-mono font-bold text-[var(--color-forest)]">
                {result?.vehicle_count || 0}
              </span>
            </div>

            {/* Class Breakdown List */}
            <div className="mt-3 space-y-2">
              <span className="text-[11px] font-mono text-[var(--color-text-muted)] uppercase">
                Classification Breakdown:
              </span>
              <div className="grid grid-cols-2 gap-2 text-xs">
                {['car', 'suv', 'bus', 'truck', 'auto_rickshaw', 'motorcycle'].map((clsKey) => {
                  const count = result?.class_breakdown?.[clsKey] || 0;
                  return (
                    <div
                      key={clsKey}
                      className="flex items-center justify-between p-2 rounded bg-[var(--color-canvas-alt)] border border-[var(--color-border-subtle)]"
                    >
                      <span className="capitalize text-[var(--color-text-muted)]">
                        {clsKey.replace('_', ' ')}:
                      </span>
                      <strong className={`font-mono ${count > 0 ? 'text-[var(--color-forest)]' : 'text-neutral-400'}`}>
                        {count}
                      </strong>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* ANPR MoRTH License Plates Card */}
          <div className="bg-[var(--color-surface)] border border-[var(--color-border-subtle)] rounded-lg p-4 shadow-xs">
            <div className="flex items-center justify-between pb-2 border-b border-[var(--color-border-subtle)]">
              <div className="flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-[var(--color-forest)]" />
                <span className="text-xs font-bold text-[var(--color-forest)] uppercase tracking-wider">
                  IDENTIFIED PLATES (HSRP)
                </span>
              </div>
              <span className="text-xs font-mono text-[var(--color-text-muted)]">
                {result?.plates?.length || 0} Plates
              </span>
            </div>

            <div className="mt-3 space-y-2 max-h-56 overflow-y-auto pr-1">
              {result?.plates && result.plates.length > 0 ? (
                result.plates.map((pl, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded bg-[var(--color-canvas-alt)] border border-[var(--color-border-subtle)] flex items-center justify-between"
                  >
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className="text-[10px] font-mono px-1 py-0.2 rounded bg-amber-200 text-amber-900 font-bold border border-amber-300">
                          IND
                        </span>
                        <span className="font-mono font-bold text-xs text-[var(--color-text-main)]">
                          {pl.text}
                        </span>
                      </div>
                      <div className="text-[10px] text-[var(--color-text-muted)] mt-0.5">
                        {pl.category.replace('_', ' ')} • {pl.vehicle_class || 'Vehicle'}
                      </div>
                    </div>

                    <div className="text-right">
                      <span className="text-[11px] font-mono font-bold text-[var(--color-forest)]">
                        {Math.round(pl.confidence * 100)}%
                      </span>
                      <div className="text-[9px] text-[var(--color-text-muted)]">CONF</div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="py-6 text-center text-xs text-[var(--color-text-muted)]">
                  No license plate detected in active frame.
                </div>
              )}
            </div>
          </div>

          {/* Model Architecture Info */}
          <div className="bg-[var(--color-surface)] border border-[var(--color-border-subtle)] rounded-lg p-3 text-[11px] text-[var(--color-text-muted)] space-y-1">
            <div className="font-bold text-[var(--color-text-main)] flex items-center gap-1">
              <Layers className="w-3.5 h-3.5 text-[var(--color-brown)]" />
              <span>Deep-Learning Inference Pipeline:</span>
            </div>
            <div>• Model: YOLOv8 Nano Vehicle Detector (Ultralytics / ONNX)</div>
            <div>• ANPR: OpenCV Morphological + CLAHE + MoRTH Regex Validation</div>
            <div>• Temporal Filtering: 15-frame rolling consensus voting</div>
          </div>
        </div>
      </div>
    </div>
  );
};
