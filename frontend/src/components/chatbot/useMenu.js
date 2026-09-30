import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Small accessible popup-menu behaviour shared by the chatbot's language menu and launcher menu:
 * focus the first item on open, Up/Down/Home/End move between items, Escape or Tab closes, a click
 * outside closes, and focus returns to the trigger button.
 */
export function useMenu() {
  const [open, setOpen] = useState(false);
  const triggerRef = useRef(null);
  const menuRef = useRef(null);

  const items = () => [...(menuRef.current?.querySelectorAll('[role^="menuitem"]') ?? [])];

  const close = useCallback((returnFocus = true) => {
    setOpen(false);
    if (returnFocus) setTimeout(() => triggerRef.current?.focus(), 0);
  }, []);

  useEffect(() => {
    if (!open) return undefined;
    const focusFirst = setTimeout(() => (items().find((i) => i.getAttribute("aria-checked") === "true") ?? items()[0])?.focus(), 0);
    const onDown = (e) => {
      if (!menuRef.current?.contains(e.target) && !triggerRef.current?.contains(e.target)) close(false);
    };
    document.addEventListener("pointerdown", onDown);
    return () => {
      clearTimeout(focusFirst);
      document.removeEventListener("pointerdown", onDown);
    };
  }, [open, close]);

  const onMenuKeyDown = (e) => {
    const list = items();
    const index = list.indexOf(document.activeElement);
    const move = (i) => {
      e.preventDefault();
      list[(i + list.length) % list.length]?.focus();
    };
    if (e.key === "ArrowDown") move(index + 1);
    else if (e.key === "ArrowUp") move(index - 1);
    else if (e.key === "Home") move(0);
    else if (e.key === "End") move(list.length - 1);
    else if (e.key === "Escape") {
      e.preventDefault();
      e.stopPropagation(); // closes the menu only, not the chat window
      close();
    } else if (e.key === "Tab") close(false);
  };

  return { open, setOpen, close, triggerRef, menuRef, onMenuKeyDown };
}
