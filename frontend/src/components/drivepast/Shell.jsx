import { useEffect, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { useFleet } from "@/context/FleetContext";
import Rail from "./Rail";
import ChatPane from "./ChatPane";
import UnitPage from "./UnitPage";
import DispatchPage from "./DispatchPage";
import SettingsPage from "./settings/SettingsPage";
import { DemoPhones } from "./DemoPhones";
import InboxPage from "./inbox/InboxPage";
import MemoryPage from "./MemoryPage";
import ActivityPage from "./ActivityPage";
import { OfflineBanner } from "./Offline";
import { MobileTabs } from "./MobileTabs";
import { TopBar } from "./TopBar";
import { LiveWatcher, ReorderToasts } from "./LiveWatcher";
import { DemoAutoplay } from "./DemoAutoplay";
import PresenterView from "./presenter/PresenterView";

function viewFor(pathname) {
  if (pathname.startsWith("/present")) return "present";
  if (pathname.startsWith("/units/")) return "unit";
  if (pathname.startsWith("/settings")) return "settings";
  if (pathname.startsWith("/inbox")) return "inbox";
  if (pathname.startsWith("/phones")) return "phones";
  if (pathname.startsWith("/memory")) return "memory";
  if (pathname.startsWith("/activity")) return "activity";
  return "dispatch";
}

function PageView({ view, unitKey }) {
  if (view === "unit") return <UnitPage unitKey={unitKey} />;
  if (view === "settings") return <SettingsPage />;
  if (view === "inbox") return <InboxPage />;
  if (view === "memory") return <MemoryPage />;
  if (view === "activity") return <ActivityPage />;
  if (view === "phones") return <DispatchPage />;
  return <DispatchPage />;
}

export default function Shell() {
  const location = useLocation();
  const { pathname } = location;
  const { unitKey } = useParams();
  const navigate = useNavigate();
  const { error, phonesOpen, setPhonesOpen } = useFleet();
  const view = viewFor(pathname);
  const [agentKey, setAgentKey] = useState(view === "unit" ? unitKey : "dispatch");
  const [tab, setTab] = useState("list");

  useEffect(() => {
    if (view === "phones") setPhonesOpen(true);
  }, [view, setPhonesOpen]);
  useEffect(() => {
    if (!phonesOpen && view === "phones") navigate("/");
  }, [phonesOpen, view, navigate]);

  useEffect(() => {
    if (view === "unit" && unitKey) setAgentKey(unitKey);
    if (view === "dispatch") setAgentKey("dispatch");
  }, [view, unitKey]);

  const go = (path) => {
    navigate(path);
    setTab("page");
  };
  const pane = (name) => `${tab === name ? "flex" : "hidden"} md:flex`;

  if (view === "present") {
    return (
      <div className="dp-backdrop flex h-[100dvh] flex-col overflow-y-auto lg:overflow-hidden" data-testid="app-shell">
        <LiveWatcher />
        <ReorderToasts />
        <PresenterView />
      </div>
    );
  }

  return (
    <div className="dp-backdrop flex h-[100dvh] flex-col overflow-hidden" data-testid="app-shell">
      <LiveWatcher />
      <ReorderToasts />
      <DemoAutoplay />
      <MobileTabs tab={tab} onChange={setTab} />
      {error && <OfflineBanner message={error} />}
      <div className="flex min-h-0 flex-1 md:grid md:grid-cols-[260px_minmax(320px,400px)_minmax(0,1fr)] md:gap-2 md:p-2">
        <aside className={`${pane("list")} dp-dark dp-frame min-h-0 w-full flex-col`} data-testid="pane-rail">
          <Rail view={view} unitKey={unitKey} onNavigate={go} />
        </aside>
        <section className={`${pane("chat")} ${view === "inbox" ? "md:hidden" : ""} dp-frame min-h-0 w-full flex-col bg-[var(--dp-page)]`} data-testid="pane-chat">
          <ChatPane agentKey={agentKey} draft={location.state?.ask} draftId={location.state?.at} />
        </section>
        <main className={`${pane("page")} ${view === "inbox" ? "md:col-span-2" : ""} dp-frame dp-scroll min-h-0 w-full min-w-0 flex-col overflow-y-auto bg-[var(--dp-page)]`} data-testid="pane-page">
          <TopBar />
          <PageView view={view} unitKey={unitKey} />
        </main>
      </div>
      <DemoPhones />
    </div>
  );
}
