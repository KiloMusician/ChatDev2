import useSWR from "swr";
const fetcher = (u:string)=> fetch(u, { cache:"no-store" }).then(r=>r.json());
export function useProvision() {
  const { data, error } = useSWR("/system-status.json", fetcher, { refreshInterval: 7000, revalidateOnFocus: false });
  return { data, error };
}