import React from "react";

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    // opcional: log
    // console.error("ErrorBoundary caught:", error, info);
  }

  render() {
    if (this.state.hasError) {
      // Se você passar um fallback, ele aparece aqui
      if (this.props.fallback) return this.props.fallback;

      return (
        <div style={{ padding: 24 }}>
          <div
            style={{
              maxWidth: 900,
              margin: "0 auto",
              borderRadius: 18,
              padding: 18,
              background: "rgba(255,255,255,0.75)",
              border: "1px solid rgba(0,0,0,0.06)",
              boxShadow: "0 20px 60px rgba(0,0,0,0.12)",
            }}
          >
            <div style={{ fontSize: 18, fontWeight: 800, marginBottom: 8 }}>
              Algo deu errado nesta tela
            </div>
            <div style={{ opacity: 0.85, marginBottom: 12 }}>
              Tente recarregar. Se continuar, volte e tente novamente.
            </div>

            <button
              onClick={() => window.location.reload()}
              style={{
                padding: "10px 14px",
                borderRadius: 12,
                border: "1px solid rgba(0,0,0,0.12)",
                background: "white",
                fontWeight: 700,
                cursor: "pointer",
              }}
            >
              Recarregar
            </button>

            <div style={{ marginTop: 12, fontSize: 12, opacity: 0.7 }}>
              {this.state.error?.message ? `Detalhe: ${this.state.error.message}` : ""}
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
