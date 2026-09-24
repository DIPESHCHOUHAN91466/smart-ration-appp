import { create } from "zustand";

// Global QR scanner visibility. Any authenticated screen can call
// useQrScannerStore.getState().open() (or the hook) to launch the scanner;
// the modal itself is mounted once in DashboardLayout.
export const useQrScannerStore = create((set) => ({
  isOpen: false,
  open: () => set({ isOpen: true }),
  close: () => set({ isOpen: false }),
}));

export const openGlobalQrScanner = () => useQrScannerStore.getState().open();
