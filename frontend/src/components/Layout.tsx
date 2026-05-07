import { useState } from "react";
import type { ReactNode } from "react";
import {
  BarChart3,
  Check,
  ClipboardCheck,
  FileCheck2,
  FileText,
  FolderUp,
  Scale,
  ShieldCheck,
  Sparkles,
  UploadCloud,
  UserCheck,
} from "lucide-react";
import { useAppStore } from "../lib/store";

const STEPS = [
  { label: "Upload Tender", icon: UploadCloud },
  { label: "Review Criteria", icon: ClipboardCheck },
  { label: "Upload Bidder", icon: FolderUp },
  { label: "Evaluation", icon: Scale },
  { label: "Human Review", icon: UserCheck },
  { label: "Report", icon: BarChart3 },
];

export default function Layout({
  children,
  onNavigate,
}: {
  children: ReactNode;
  onNavigate: (step: number) => void;
}) {
  const { currentStep, maxUnlockedStep } = useAppStore();
  const [tilt, setTilt] = useState({ x: 0, y: 0 });
  const StepIcon = STEPS[currentStep].icon;

  const handlePointerMove = (event: React.PointerEvent<HTMLDivElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width - 0.5) * 2;
    const y = ((event.clientY - rect.top) / rect.height - 0.5) * 2;
    setTilt({ x: Number((x * 8).toFixed(2)), y: Number((-y * 8).toFixed(2)) });
  };

  return (
    <div
      className="layout"
      style={
        {
          "--tilt-x": `${tilt.x}deg`,
          "--tilt-y": `${tilt.y}deg`,
        } as React.CSSProperties
      }
      onPointerMove={handlePointerMove}
      onPointerLeave={() => setTilt({ x: 0, y: 0 })}
    >
      <div className="ambient-grid" />
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-icon">
            <ShieldCheck size={26} />
          </div>
          <h1>ProcureSense</h1>
          <p className="brand-sub">Evaluation System</p>
        </div>

        <nav className="sidebar-nav">
          {STEPS.map((step, index) => {
            const Icon = step.icon;
            const isLocked = index > maxUnlockedStep;
            return (
              <button
                key={step.label}
                className={`nav-item ${index === currentStep ? "nav-active" : ""} ${index < currentStep ? "nav-done" : ""} ${isLocked ? "nav-locked" : ""}`}
                onClick={() => onNavigate(index)}
                disabled={isLocked}
              >
                <span className="nav-icon">
                  {index < currentStep ? <Check size={17} /> : <Icon size={17} />}
                </span>
                <span className="nav-label">{step.label}</span>
                <span className="nav-step">Step {index + 1}</span>
              </button>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          <p>AI-Assisted Prototype</p>
          <p className="version">v1.0.0</p>
        </div>
      </aside>

      <main className="main-content">
        <section className="command-hero">
          <div>
            <span className="eyebrow">
              <Sparkles size={14} /> Live evaluation workspace
            </span>
            <h2>{STEPS[currentStep].label}</h2>
            <p>Extract, verify, review, and publish tender decisions through a guided AI workflow.</p>
          </div>
          <div className="hero-3d" aria-hidden="true">
            <div className="hero-stage">
              <div className="floating-card card-a">
                <FileText size={22} />
                <span>Tender PDF</span>
              </div>
              <div className="floating-card card-b">
                <StepIcon size={24} />
                <span>{STEPS[currentStep].label}</span>
              </div>
              <div className="floating-card card-c">
                <FileCheck2 size={22} />
                <span>Audit Trail</span>
              </div>
              <div className="scan-beam" />
            </div>
          </div>
        </section>

        <div className="content-wrapper">{children}</div>
      </main>
    </div>
  );
}
