import React from "react";
import SuasTopHeader from "./SuasTopHeader.jsx";

export default function CrasTopHeader(props) {
  return (
    <SuasTopHeader
      {...props}
      titleRight="CRAS"
      subtitle="Triagem, PAIF, SCFV, CadÚnico e rede com LGPD aplicada"
      unidadeLabel="Unidade CRAS:"
    />
  );
}
