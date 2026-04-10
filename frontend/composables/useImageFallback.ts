export function applyImageFallback(event: Event, fallbackSrc = '/images/placeholder-bathing-site.svg') {
  const target = event.target
  if (!(target instanceof HTMLImageElement)) {
    return
  }

  if (target.src.endsWith(fallbackSrc)) {
    return
  }

  target.src = fallbackSrc
}
