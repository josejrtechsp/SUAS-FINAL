import React from "react";
import SuasTopHeader from "./SuasTopHeader.jsx";

export default function CreasTopHeader(props) {
  return (
    <SuasTopHeader
      {...props}
      titleRight="CREAS"
      subtitle="PAEFI, rede e prazos com rastreabilidade (LGPD aplicada)"
      unidadeLabel="Unidade CREAS:"
    />
  );
}
