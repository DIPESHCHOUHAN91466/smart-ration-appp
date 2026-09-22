import { create } from "zustand";
import { persist } from "zustand/middleware";
import { translations } from "./translations";

export const useLanguageStore = create(
  persist(
    (set) => ({
      language: "en",
      setLanguage: (language) => set({ language }),
    }),
    { name: "smart-ration-language" },
  ),
);

export function useTranslation() {
  const language = useLanguageStore((state) => state.language);
  const setLanguage = useLanguageStore((state) => state.setLanguage);

  const t = (key) => translations[language]?.[key] ?? translations.en[key] ?? key;

  return { t, language, setLanguage };
}
