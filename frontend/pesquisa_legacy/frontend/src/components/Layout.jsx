import React from "react";
import Header from "./Header.jsx";
import Footer from "./Footer.jsx";

export default function Layout({ children }) {
  return (
    <div className="app-root">
      <Header />
      <main className="main-content">{children}</main>
      <Footer />
    </div>
  );
}