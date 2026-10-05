# Frontend Design & Code Standards

## 1. Aesthetic Direction (Anti-AI Slop)
- Avoid predictable "AI templates": do not put everything in centered 3-card grids with soft rounded corners and purple/blue drop shadows.
- Commit to a clear visual hierarchy: choose an intentional layout posture (e.g., dense SaaS workspace, high-contrast dashboard, or asymmetrical editorial grid) before writing markup.
- Whitespace & Rhythm: Use consistent Tailwind spacing increments (`gap-4`, `gap-6`, `p-6`). Avoid arbitrary padding values.
- Typography: Establish high contrast between headings and body text using weight and tracking (`tracking-tight` on bold headings, readable line heights on body).

## 2. daisyUI Theme Integrity
- Strict Semantic Tokens: NEVER use raw Tailwind palette colors (e.g., `text-gray-700`, `bg-slate-900`, `border-zinc-200`). Hardcoded colors break daisyUI theme switching.
- Always map UI elements to daisyUI theme variables:
  - Backgrounds: `bg-base-100` (page), `bg-base-200` (cards/sections), `bg-base-300` (nested containers/borders).
  - Text: `text-base-content`, `text-neutral-content`, `text-primary-content`.
  - Brand & Status: `btn-primary`, `badge-secondary`, `alert-success`, `text-error`.
- Prefer daisyUI semantic components (`btn`, `card`, `input`, `select`, `modal`, `badge`, `table`, `dropdown`) over chains of 10+ standard Tailwind utilities.
- Do not override daisyUI component states (hover, focus, active) with manual utilities unless specifically asked.

## 3. Vue 3 Standards
- Single-File Components: Use `<script setup lang="ts">` exclusively.
- Reactivity: Use `ref()` and `computed()`. Avoid `reactive()` for primitives or when destructuring is needed.
- Two-Way Binding: Use `defineModel()` for component models instead of manual `modelValue` props and `update:modelValue` emits.
- Props & Emits: Define typed interfaces with `defineProps<{ ... }>()` and `defineEmits<{ ... }>()`. Never use runtime array declarations (`props: ['foo']`).
- Logic Extraction: Extract multi-step UI logic, forms, and API calls into composables (`use*.ts`). Keep the `<script setup>` block lightweight.

