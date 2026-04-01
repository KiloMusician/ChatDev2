// client/src/components/SafeList.tsx
import React from "react";
import { safeMap, normalizeData } from "@/lib/guardedOps";

type Keyish = string | number;
type WithId = { id?: Keyish } & Record<string, any>;

export function SafeList<T extends WithId>({
  data,
  render,
  getKey,
  label = "SafeList",
}: {
  data: unknown;
  render: (item: T, i: number) => React.ReactNode;
  getKey?: (item: T, i: number) => Keyish;
  label?: string;
}) {
  const arr = normalizeData<T>(data);
  const keyFn = getKey ?? ((x: T, i: number) => x?.id ?? i);
  return (
    <>
      {safeMap<T, React.ReactNode>(
        arr,
        (item, i) => <React.Fragment key={keyFn(item, i)}>{render(item, i)}</React.Fragment>,
        label
      )}
    </>
  );
}