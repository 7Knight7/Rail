/**
 * App-wide notification runtime.
 *
 * Mounted once in AppShell: listens to the live activity stream and, based on
 * the notification settings, fires a desktop Notification and/or a short
 * WebAudio beep for report completion and failure events.
 */

import { useEffect } from "react";
import { subscribeActivity, type ActivityEntry } from "@/api/activity";
import { getDisplayPrefs, subscribeDisplayPrefs } from "@/utils/displayPrefs";

const COMPLETION_ACTIONS = new Set(["REPORT_COMPLETED", "AUTOMATION_COMPLETED"]);
const FAILURE_ACTIONS = new Set(["REPORT_FAILED", "AUTOMATION_FAILED"]);

let audioContext: AudioContext | null = null;

function playBeep() {
  try {
    audioContext ??= new AudioContext();
    const ctx = audioContext;
    const oscillator = ctx.createOscillator();
    const gain = ctx.createGain();
    oscillator.type = "sine";
    oscillator.frequency.value = 880;
    gain.gain.setValueAtTime(0.08, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.35);
    oscillator.connect(gain).connect(ctx.destination);
    oscillator.start();
    oscillator.stop(ctx.currentTime + 0.4);
  } catch {
    // Audio not available (autoplay policy, no device) — ignore
  }
}

function showDesktopNotification(entry: ActivityEntry, failed: boolean) {
  if (!("Notification" in window) || Notification.permission !== "granted") return;
  try {
    new Notification(failed ? "Report Failed" : "Report Completed", {
      body: entry.message,
      tag: entry.id,
    });
  } catch {
    // Constructor can throw on some platforms (e.g. Android) — ignore
  }
}

function maybeRequestPermission() {
  const prefs = getDisplayPrefs().notifications;
  if (
    prefs.enabled &&
    prefs.desktop &&
    "Notification" in window &&
    Notification.permission === "default"
  ) {
    void Notification.requestPermission();
  }
}

function handleEvent(entry: ActivityEntry) {
  const prefs = getDisplayPrefs().notifications;
  if (!prefs.enabled) return;

  const failed = FAILURE_ACTIONS.has(entry.action) || entry.status === "error";
  const completed = COMPLETION_ACTIONS.has(entry.action);
  if (failed) {
    if (!prefs.onFailure) return;
  } else if (completed) {
    if (!prefs.onCompletion) return;
  } else {
    return;
  }

  if (prefs.desktop) showDesktopNotification(entry, failed);
  if (prefs.sound) playBeep();
}

export function useNotificationRuntime(): void {
  useEffect(() => {
    const subscription = subscribeActivity({ onEvent: handleEvent });
    const unsubscribePrefs = subscribeDisplayPrefs(maybeRequestPermission);
    maybeRequestPermission();
    return () => {
      subscription.close();
      unsubscribePrefs();
    };
  }, []);
}
