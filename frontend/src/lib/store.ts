import { create } from "zustand";

interface AppState {
  activeTenderId: number | null;
  activeBidderId: number | null;
  currentStep: number;
  maxUnlockedStep: number;
  setActiveTender: (id: number | null) => void;
  setActiveBidder: (id: number | null) => void;
  setStep: (step: number) => void;
  unlockStep: (step: number) => void;
  resetProgress: (step?: number) => void;
}

export const useAppStore = create<AppState>((set) => ({
  activeTenderId: null,
  activeBidderId: null,
  currentStep: 0,
  maxUnlockedStep: 0,
  setActiveTender: (id) =>
    set((state) => ({
      activeTenderId: id,
      activeBidderId: null,
      currentStep: Math.min(state.currentStep, 1),
      maxUnlockedStep: Math.min(state.maxUnlockedStep, 1),
    })),
  setActiveBidder: (id) => set({ activeBidderId: id }),
  setStep: (step) =>
    set((state) => ({
      currentStep: Math.max(0, Math.min(step, state.maxUnlockedStep)),
    })),
  unlockStep: (step) =>
    set((state) => ({
      maxUnlockedStep: Math.max(state.maxUnlockedStep, step),
    })),
  resetProgress: (step = 0) =>
    set((state) => ({
      currentStep: Math.min(state.currentStep, step),
      maxUnlockedStep: Math.max(0, step),
    })),
}));
