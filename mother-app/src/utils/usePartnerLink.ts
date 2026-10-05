// The partner QR code: her spouse scans it and sees only the pregnancy week and due date.
import QRCode from 'qrcode'
import { onMounted, ref, shallowRef, watch } from 'vue'

import { partner as partnerApi } from '@/api/endpoints'
import type { PartnerLink } from '@/api/types'
import { useToasts } from '@/stores/toast'

import { useAction } from './useAction'

export function usePartnerLink(copiedText: () => string) {
  const { busy, act } = useAction()
  const toasts = useToasts()
  const loading = ref(true)
  const link = shallowRef<PartnerLink | null>(null)
  const qr = ref('')

  watch(link, async (value) => {
    qr.value = value ? await QRCode.toDataURL(value.url, { margin: 1, width: 480 }) : ''
  })

  onMounted(async () => {
    await act(async () => {
      link.value = await partnerApi.current()
    })
    loading.value = false
  })

  const create = () => act(async () => {
    link.value = await partnerApi.create()
  })

  const revoke = () => act(async () => {
    await partnerApi.revoke()
    link.value = null
  }, 'partner.revoked')

  async function copy() {
    if (!link.value) return
    await navigator.clipboard.writeText(link.value.url)
    toasts.show(copiedText())
  }

  return { loading, busy, link, qr, create, revoke, copy }
}
