import React from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import QRCodeGenerator from "./QRCodeGenerator";

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<QRCodeGenerator />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
