import { useRuntimeConfig } from '#imports'
import type { BathingSite, BathingSiteListResponse } from '../types/bathing-site'

export function useBathingApi() {
  const config = useRuntimeConfig()

  const getList = (query: Record<string, string | number | undefined>) =>
    $fetch<BathingSiteListResponse>(`${config.public.apiBase}/api/bathing-sites`, {
      query,
    })

  const getDetail = (id: string) =>
    $fetch<BathingSite>(`${config.public.apiBase}/api/bathing-sites/${id}`)

  return { getList, getDetail }
}
