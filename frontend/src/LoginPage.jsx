import { useState } from "react";
import "./App.css";
import { API_BASE } from "./config";

// ✅ Safari-friendly: evita IPv6/localhost travado
export default function LoginPage({ onLogin, modulo = "poprua", onVoltar }) {
  const [email, setEmail] = useState("admin@poprua.local");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState("");
  const [loading, setLoading] = useState(false);

  const moduloLabel = (() => {
    const m = String(modulo || "poprua").toLowerCase();
    if (m === "cras") return "CRAS";
    if (m === "creas") return "CREAS";
    if (m === "gestao") return "Gestão";
    if (m === "hub") return "Módulos";
    return "Pop Rua";
  })();

  async function handleSubmit(e) {
    e.preventDefault();
    setErro("");

    const emailNorm = (email || "").trim().toLowerCase();
    const senhaNorm = (senha || "").trim();

    if (!emailNorm || !senhaNorm) {
      setErro("Informe o e-mail e a senha.");
      return;
    }

    // ✅ Nunca mais fica “Entrando…” infinito
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 12000); // 12s

    try {
      setLoading(true);

      const form = new URLSearchParams();
      form.append("grant_type", "password");
      form.append("username", emailNorm);
      form.append("password", senhaNorm);

      const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: form.toString(),
        signal: controller.signal,
      });

      const data = await res.json().catch(() => null);

      if (!res.ok) {
        const msg =
          data?.detail ||
          `Login falhou (HTTP ${res.status}). Verifique e-mail e senha.`;
        throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
      }

      // ✅ Padrão do seu sistema
      localStorage.setItem("poprua_token", data.access_token);
      localStorage.setItem("poprua_usuario", JSON.stringify(data.usuario));

      // limpa lixo antigo
      localStorage.removeItem("token");
      localStorage.removeItem("access_token");

      onLogin?.(data.usuario);
    } catch (err) {
      if (err.name === "AbortError") {
        setErro(
          "O backend não respondeu. Confirme se http://" + window.location.hostname + ":8001/health abre no Safari."
        );
      } else {
        setErro(err.message || "Erro ao fazer login.");
      }
    } finally {
      clearTimeout(timeoutId);
      setLoading(false);
    }
  }

  return (
    <div className="login-root">
      <div className="login-shell">
        <div className="login-side">
          <div className="login-logo-tag">
            Sistema Pop Rua
            <span style={{ marginLeft: 10, opacity: .85, fontWeight: 900 }}>
              · Módulo: {modulo === "poprua" ? "Pop Rua" : String(modulo)}
            </span>
          </div>
          <h1 className="login-side-title">Pop Rua em rede, com dados qualificados.</h1>
          <p className="login-side-text">
            Organize o atendimento, conecte equipes e apoie decisões com base em dados.
          </p>

          <ul className="login-side-lista">
            <li><span className="login-side-icone">🧭</span><span><strong>Linha de metrô</strong> para acompanhar casos</span></li>
            <li><span className="login-side-icone">👥</span><span><strong>Perfis e hierarquia</strong> conforme LGPD</span></li>
            <li><span className="login-side-icone">📊</span><span><strong>Gestão regional</strong> e dashboards</span></li>
          </ul>
        </div>

        <div className="login-card">
          <div className="login-header">
            {onVoltar ? (
              <button
                type="button"
                className="btn btn-secundario btn-secundario-mini"
                onClick={() => onVoltar?.()}
                style={{ marginBottom: 10 }}
              >
                ← Voltar para módulos
              </button>
            ) : null}
            <div className="login-tag">Acesso restrito</div>
            <h2 className="login-title">Entrar no painel</h2>
            <p className="login-subtitle">
              Use seu e-mail institucional e senha para acessar o painel {moduloLabel}.
            </p>
          </div>

          <form className="login-form" onSubmit={handleSubmit}>
            <label className="form-label">
              E-mail
              <input
                className="input"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@poprua.local"
              />
            </label>

            <label className="form-label">
              Senha
              <input
                className="input"
                type="password"
                value={senha}
                onChange={(e) => setSenha(e.target.value)}
                placeholder="admin123"
              />
            </label>

            {erro && <p className="erro-global">{erro}</p>}

            <div className="card-footer-right" style={{ marginTop: 12 }}>
              <button type="submit" className="btn btn-primario" disabled={loading}>
                {loading ? "Entrando..." : "Entrar"}
              </button>
            </div>
          </form>

          <div className="login-perfis">
            <h3>Perfis de acesso</h3>
            <p>
              <strong>Operador:</strong> registra atendimentos e casos.<br />
              <strong>Coordenação municipal:</strong> acompanha casos do município.<br />
              <strong>Gestor do consórcio:</strong> visão regional.<br />
              <strong>Admin:</strong> acesso total.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}