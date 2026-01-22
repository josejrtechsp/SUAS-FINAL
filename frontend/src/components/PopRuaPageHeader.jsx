import React from "react";
import CrasPageHeader from "./CrasPageHeader.jsx";

export default function PopRuaPageHeader(props) {
  const userName =
    props.userName ??
    props.usuarioNome ??
    props.usuarioLogado?.nome ??
    props.user?.name ??
    "—";

  return (
    <CrasPageHeader
      {...props}
      moduleTag={props.moduleTag ?? "MÓDULO SUAS · POP RUA EM REDE"}
      moduleChip={props.moduleChip ?? "POP RUA"}
      userName={userName}
    />
  );
}
