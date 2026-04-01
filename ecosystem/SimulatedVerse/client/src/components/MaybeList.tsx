// client/src/components/MaybeList.tsx
import React from "react";
import { isListish } from "../../../packages/util/safe";

export function MaybeList({ data, children }: { data: unknown; children: React.ReactNode }) {
  if (!isListish(data)) return null;
  return <>{children}</>;
}
