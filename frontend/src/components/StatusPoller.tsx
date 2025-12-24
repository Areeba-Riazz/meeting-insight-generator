import { useEffect } from "react";

type Props = {
  meetingId: string;
  status: string | null;
  onPoll: () => Promise<void>;
  polling: boolean;
};

export function StatusPoller({ meetingId, status, onPoll, polling }: Props) {
  useEffect(() => {
    if (!meetingId) return;
    if (status === "completed" || (status ?? "").startsWith("error")) return;
    const id = setInterval(() => {
      onPoll();
    }, 2500);
    return () => clearInterval(id);
  }, [meetingId, status, onPoll]);

  return (
    <div className="card">
      <h3>Status</h3>
      <p><strong>Meeting ID:</strong> {meetingId}</p>
      <p><strong>Status:</strong> {status ?? "unknown"}</p>
      <button onClick={onPoll} disabled={polling}>Refresh now</button>
    </div>
  );
}

