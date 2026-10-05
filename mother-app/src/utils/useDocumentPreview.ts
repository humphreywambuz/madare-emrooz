// Opening one of her documents: fetch the file and hand it to the preview dialog.
import { onUnmounted, ref, shallowRef } from 'vue'

import { documents as documentsApi } from '@/api/endpoints'
import type { MedicalDocument } from '@/api/types'

import { useAction } from './useAction'

export function useDocumentPreview() {
  const { busy, act } = useAction()
  const open = ref(false)
  const url = ref('')
  const doc = shallowRef<MedicalDocument | null>(null)

  async function view(document: MedicalDocument) {
    await act(async () => {
      const blob = await documentsApi.file(document.id)
      URL.revokeObjectURL(url.value)
      url.value = URL.createObjectURL(blob)
      doc.value = document
      open.value = true
    })
  }
  onUnmounted(() => URL.revokeObjectURL(url.value))

  return { busy, open, url, doc, view }
}
