import React from "react";
import CrasPageHeader from "./CrasPageHeader.jsx";

export default function CreasPageHeader(props) {
  const userName =
    props.userName ?? props.usuarioNome ?? props.user?.name ?? "Admin Pop Rua";

  return (
    <CrasPageHeader
      {...props}
      moduleChip="CREAS"
      userName={userName}
    />
  );
}
