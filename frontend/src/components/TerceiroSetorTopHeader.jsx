import React from "react";
import SuasTopHeader from "./SuasTopHeader.jsx";

export default function TerceiroSetorTopHeader(props) {
  return (
    <SuasTopHeader
      {...props}
      titleRight={props.titleRight ?? "Terceiro Setor"}
      subtitle={
        props.subtitle ??
        "OSCs, parcerias (MROSC), metas, monitoramento e prestação de contas — com evidência e auditoria."
      }
    />
  );
}
