import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AppLayout } from "./layouts/AppLayout";
import { Explore } from "./pages/Explore";
import { Compare } from "./pages/Compare";
import { Method } from "./pages/Method";
import { Dashboard } from "./pages/Dashboard";
import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<Explore />} />
          <Route path="compare" element={<Compare />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="method" element={<Method />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
