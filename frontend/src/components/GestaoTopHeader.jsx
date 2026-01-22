import React from "react";
import SuasTopHeader from "./SuasTopHeader.jsx";

export default function GestaoTopHeader(props) {
  const unidadeLabel = props.unidadeLabel ?? "Unidade (opcional):";

  return (
    <SuasTopHeader
      {...props}
      titleRight={props.titleRight ?? "Gestão"}
      subtitle={props.subtitle ?? "Dashboard do Secretário: visão consolidada, gargalos (SLA), fila e rede."}
      unidadeLabel={unidadeLabel}
    />
  );
}
