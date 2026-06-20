/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

declare module 'marked' {
  interface MarkedOptions {
    breaks?: boolean
    gfm?: boolean
  }
  export function marked(content: string, options?: MarkedOptions): string
}

declare module 'highlight.js' {
  const hljs: any
  export default hljs
}
