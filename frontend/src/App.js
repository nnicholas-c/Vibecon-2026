import "@/App.css";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import { FleetProvider } from "@/context/FleetContext";
import Shell from "@/components/drivepast/Shell";
import QuotePage from "@/components/drivepast/QuotePage";
import DriverPage from "@/components/drivepast/mobile/DriverPage";
import DevPage from "@/components/drivepast/DevPage";
import CustomerPage from "@/components/drivepast/mobile/CustomerPage";
import { AuthGate } from "@/components/drivepast/AuthGate";
import { AboutPage, LandingPage, ResearchPage } from "@/landing";

function App() {
  return (
    <div className="App">
      <FleetProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/about" element={<AboutPage />} />
            <Route path="/research" element={<ResearchPage />} />
            <Route path="/q/:token" element={<QuotePage />} />
            <Route path="/dev" element={<DevPage />} />
            <Route path="/driver/:vanId" element={<DriverPage />} />
            <Route path="/customer/:requestKey" element={<CustomerPage />} />
            <Route path="*" element={<AuthGate><Routes>
              <Route path="/dispatch" element={<Shell />} />
              <Route path="/units/:unitKey" element={<Shell />} />
              <Route path="/settings" element={<Shell />} />
              <Route path="/inbox" element={<Shell />} />
              <Route path="/inbox/:requestKey" element={<Shell />} />
              <Route path="/phones" element={<Shell />} />
              <Route path="/memory" element={<Shell />} />
              <Route path="/activity" element={<Shell />} />
              <Route path="/present" element={<Shell />} />
              <Route path="*" element={<Navigate to="/dispatch" replace />} />
            </Routes></AuthGate>} />
          </Routes>
        </BrowserRouter>
        <Toaster position="top-center" richColors />
      </FleetProvider>
    </div>
  );
}

export default App;
