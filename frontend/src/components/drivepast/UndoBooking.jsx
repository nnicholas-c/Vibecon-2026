import { useEffect, useState } from "react";
import { Undo2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { useFleet } from "@/context/FleetContext";
import { friendlyMessage, http } from "@/lib/api";
import { money } from "@/lib/format";

export function UndoBooking({ unitKey, requestKey, onDone }) {
  const { version, reload } = useFleet();
  const [quote, setQuote] = useState(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    const q = requestKey ? `request_key=${requestKey}` : `unit_key=${unitKey}`;
    http.get(`/quotes?${q}&status=accepted`).then(({ data }) => setQuote(data[0] || null)).catch(() => setQuote(null));
  }, [unitKey, requestKey, version]);
  if (!quote) return null;
  const undo = async () => {
    setBusy(true);
    try {
      const { data } = await http.post(`/quotes/${quote.key}/undo`);
      toast.success(data.message || "Booking undone");
      setQuote(null);
      await reload();
      onDone?.();
    } catch (err) {
      toast.error(friendlyMessage(err, "Couldn't undo. Try again."));
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="dp-card flex flex-wrap items-center justify-between gap-3 px-5 py-3" data-testid="undo-booking-bar">
      <p className="text-sm">Booked: <span className="font-semibold">{quote.customer}</span>, {money(quote.price)} {quote.per === "visit" ? "a visit" : `a ${quote.per}`} on {quote.unit_name}</p>
      <Button onClick={undo} disabled={busy} variant="outline" className="h-9 rounded-full px-4 font-semibold" data-testid="undo-booking-button">
        <Undo2 className="mr-2 h-4 w-4" />{busy ? "Undoing..." : "Undo"}
      </Button>
    </div>
  );
}
