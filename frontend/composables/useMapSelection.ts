import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from '#imports'
import type { MapItem } from '../types/map'

export function useMapSelection() {
  const route = useRoute()
  const router = useRouter()
  const state = useMapState()
  const { loadDetailsById, loadDetailsBySlug } = useMapData()
  const clientSlug = ref<string | null>(null)

  const routeSlug = computed(() => {
    const slug = route.params.slug
    return typeof slug === 'string' ? slug : null
  })

  const currentSlug = computed(() => clientSlug.value ?? routeSlug.value)

  function slugFromPathname(pathname: string) {
    const cleaned = pathname.replace(/^\/+|\/+$/g, '')
    return cleaned || null
  }

  async function selectById(id: string) {
    const item = await loadDetailsById(id)
    if (!item) {
      return null
    }

    await navigateToItem(item)
    return item
  }

  async function selectBySlug(slug: string) {
    if (state.selectedItem.value?.slug === slug) {
      return state.selectedItem.value
    }

    return await loadDetailsBySlug(slug)
  }

  async function navigateToItem(item: MapItem) {
    if (currentSlug.value === item.slug) {
      return
    }

    if (import.meta.client) {
      window.history.pushState({}, '', `/${item.slug}`)
      clientSlug.value = item.slug
      return
    }

    await router.push({ path: `/${item.slug}` })
  }

  async function closeSelection() {
    state.clearSelection()
    if (currentSlug.value && import.meta.client) {
      window.history.pushState({}, '', '/')
      clientSlug.value = null
      return
    }

    if (routeSlug.value) {
      await router.push({ path: '/' })
    }
  }

  async function syncSelectionFromSlug(slug: string | null) {
    if (!slug) {
      state.clearSelection()
      return
    }

    const item = await selectBySlug(slug)
    if (!item && currentSlug.value) {
      if (import.meta.client) {
        window.history.replaceState({}, '', '/')
        clientSlug.value = null
        return
      }
      await router.replace({ path: '/' })
    }
  }

  watch(currentSlug, syncSelectionFromSlug, { immediate: true })

  onMounted(() => {
    clientSlug.value = slugFromPathname(window.location.pathname)
    window.addEventListener('popstate', handlePopState)
  })

  onBeforeUnmount(() => {
    if (import.meta.client) {
      window.removeEventListener('popstate', handlePopState)
    }
  })

  function handlePopState() {
    clientSlug.value = slugFromPathname(window.location.pathname)
  }

  return {
    routeSlug: currentSlug,
    selectById,
    selectBySlug,
    navigateToItem,
    closeSelection,
  }
}
