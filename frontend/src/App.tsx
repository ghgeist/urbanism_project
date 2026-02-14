import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Explore } from "./pages/Explore";
import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Explore />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
