import { create } from "zustand";
import { persist } from "zustand/middleware";

// Centralized UI preference model — the single source of truth for every
// appearance/display/accessibility toggle in Settings. Language has its own
// dedicated store (useLanguageStore) and is intentionally NOT duplicated
// here; Settings/backup-restore read both and merge them for import/export.
export const PREFERENCE_DEFAULTS = {
  density: "comfortable", // compact | comfortable | full
  sidebar: "expanded", // expanded | collapsed
  fontSize: "medium", // small | medium | large
  highContrast: false,
  reduceAnimations: false,
  showSearch: true,
  showNotifications: true,
  showProfile: true,
  showBreadcrumbs: true,
  showStatus: true,
  showAvailability: true,
  showHelp: true,
};

export const usePreferencesStore = create(
  persist(
    (set) => ({
      ...PREFERENCE_DEFAULTS,
      setPreference: (key, value) => set({ [key]: value }),
      setMany: (partial) => set(partial),
      resetAll: () => set({ ...PREFERENCE_DEFAULTS }),
    }),
    { name: "smart-ration-preferences" },
  ),
);
