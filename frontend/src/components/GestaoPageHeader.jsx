import React from "react";
import CrasPageHeader from "./CrasPageHeader.jsx";

export default function GestaoPageHeader(props) {
  return (
    <CrasPageHeader
      {...props}
      moduleTag={props.moduleTag ?? "MÓDULO SUAS · GESTÃO"}
      moduleChip={props.moduleChip ?? "GESTÃO"}
    />
  );
}
