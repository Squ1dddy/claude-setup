export type UsageLimit = { kind: string; percentUsed: number; resetsAt: string | null }

export type BandInfo = {
  tokens: number | null
  percent: number | null
  limits: UsageLimit[]
  project: string | null
  next: string | null
  noteAgeMin: number | null
}

declare module 'claude-code' {
  interface PluginState {
    'checkpoint-band': { info: BandInfo | null; lastSaveAt: number | null }
  }
}
