import { computed, watch } from 'vue'
import { useRoute, useRouter } from '#imports'
import type { MapItem } from '../types/map'

export function useMapSelection() {
  const route = useRoute()
  const router = useRouter()
  const state = useMapState()
  const { loadDetailsById, loadDetailsBySlug } = useMapData()

  const routeSlug = computed(() => {
    const slug = route.params.slug
    return typeof slug === 'string' ? slug : null
  })

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
    if (routeSlug.value === item.slug) {
      return
    }

    await router.push({ path: `/${item.slug}` })
  }

  async function closeSelection() {
    state.clearSelection()
    if (routeSlug.value) {
      await router.push({ path: '/' })
    }
  }

  watch(routeSlug, async (slug) => {
    if (!slug) {
      state.clearSelection()
      return
    }

    const item = await selectBySlug(slug)
    if (!item && routeSlug.value) {
      await router.replace({ path: '/' })
    }
  }, { immediate: true })

  return {
    routeSlug,
    selectById,
    selectBySlug,
    navigateToItem,
    closeSelection,
  }
}
