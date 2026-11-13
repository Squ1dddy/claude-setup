import { atom, read, update } from 'claude-code'
import type { Engine, Register } from 'claude-code'

import type { BandInfo } from '../types'

const BRAIN = '{{HOME}}/Brain'
const PROJECTS = `${BRAIN}/Projects`
const WARN_TOKENS = 150_000
const STALE_SAVE_MIN = 45

const info = atom({ plugin: 'checkpoint-band', key: 'info' } as const, null)
const lastSaveAt = atom({ plugin: 'checkpoint-band', key: 'lastSaveAt' } as const, null)

const norm = (p: string) => p.replace(/\\/g, '/').replace(/\/+$/, '').toLowerCase()

const ago = (min: number) =>
  min < 60 ? `${min}m` : min < 60 * 48 ? `${Math.round(min / 60)}h` : `${Math.round(min / 1440)}d`

const kTokens = (n: number) => `${Math.round(n / 1000)}k`

// Claude brand ramp, softened to pastel: warm grey -> sand -> peach -> coral
// as a gauge fills (0 to 1).
const RAMP: [number, string][] = [
  [0, '#B1ADA1'],
  [0.5, '#E3C2A2'],
  [0.75, '#EFA587'],
  [1, '#E8896A'],
]
const ACCENT = '#EFA587'
const CONTEXT_FULL = 200_000

function rampColor(fill: number): string {
  const hex = (c: string) => [1, 3, 5].map(i => parseInt(c.slice(i, i + 2), 16))
  for (let i = 1; i < RAMP.length; i++) {
    const [hiAt, hiColor] = RAMP[i]
    if (fill > hiAt) continue
    const [loAt, loColor] = RAMP[i - 1]
    const t = Math.max(0, (fill - loAt) / (hiAt - loAt))
    const lo = hex(loColor)
    const hi = hex(hiColor)
    return `#${lo.map((v, k) => Math.round(v + (hi[k] - v) * t).toString(16).padStart(2, '0')).join('')}`
  }
  return RAMP[RAMP.length - 1][1]
}

const LIMIT_NAMES: Record<string, string> = {
  five_hour: '5-hour limit',
  seven_day: 'Weekly limit',
  spend_limit: 'Spend limit',
}

function resetsIn(iso: string | undefined, now: number): string {
  const at = iso ? Date.parse(iso) : NaN
  if (Number.isNaN(at)) return ''
  const min = Math.max(0, Math.round((at - now) / 60_000))
  const d = Math.floor(min / 1440)
  const h = Math.floor((min % 1440) / 60)
  const m = min % 60
  const span = d > 0 ? `${d}d ${h}h` : h > 0 ? `${h}h ${m}m` : `${m}m`
  return `resets in ${span}`
}

// Pick the Resume section the way brain.py does: `## Resume: <branch>` first,
// then plain `## Resume`, then the first Resume of any kind.
function resumeNext(body: string, branch: string | null): string | null {
  const lines = body.split(/\r?\n/)
  const sections: { title: string; start: number }[] = []
  lines.forEach((line, i) => {
    const m = /^##\s+Resume\b:?\s*(.*)$/.exec(line)
    if (m) sections.push({ title: m[1].trim(), start: i + 1 })
  })
  if (sections.length === 0) return null

  const firstWord = (t: string) => t.split(/\s+/)[0]?.replace(/[^\w./-]/g, '') ?? ''
  const pick =
    (branch && sections.find(s => firstWord(s.title) === branch)) ||
    sections.find(s => s.title === '') ||
    sections[0]

  for (let i = pick.start; i < lines.length && !/^##\s/.test(lines[i]); i++) {
    const m = /\bNext\b[^:]{0,30}:\**\s*(.+)$/i.exec(lines[i])
    if (m) {
      const text = m[1].replace(/\*\*/g, '').trim()
      return text.length > 110 ? `${text.slice(0, 107)}...` : text
    }
  }
  return null
}

async function refresh($: Engine): Promise<void> {
  const { context, rateLimits } = await $.session.usage()
  const next: BandInfo = {
    tokens: context.tokens ?? null,
    percent: context.percent ?? null,
    limits: rateLimits.map(r => ({
      kind: r.kind,
      percentUsed: r.percentUsed,
      resetsAt: r.resetsAt ?? null,
    })),
    project: null,
    next: null,
    noteAgeMin: null,
  }

  try {
    const cwd = norm(await $.session.cwd())
    const entries = await $.fs.list(PROJECTS)
    for (const entry of entries) {
      if (!entry.name.endsWith('.md')) continue
      const path = `${PROJECTS}/${entry.name}`
      const body = await $.fs.read(path)
      const repoLine = /^repo:\s*(.+)$/m.exec(body.slice(0, 600))
      if (!repoLine) continue
      const repos = repoLine[1].split(';').map(r => norm(r.trim())).filter(r => r && r !== 'none')
      if (!repos.some(r => cwd === r || cwd.startsWith(`${r}/`))) continue

      const git = await $.process.run(['git', 'branch', '--show-current'], { cwd, timeoutMs: 3000 })
      const branch = git.exitCode === 0 ? git.stdout.trim() || null : null
      const stat = await $.fs.stat(path)

      next.project = entry.name.replace(/\.md$/, '')
      next.next = resumeNext(body, branch)
      next.noteAgeMin = Math.round(((await $.clock.now()) - stat.mtimeMs) / 60_000)
      break
    }
  } catch {
    // No project match is fine: the band shows context and save state only.
  }

  await update($, info, () => next)
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const result = await next(e)
    await refresh($)
    return result
  })

  on('turn.complete', async ($, e, next) => {
    const result = await next(e)
    await refresh($)
    return result
  })

  // A Write or Edit inside the vault counts as a Brain save.
  for (const tool of ['Write', 'Edit'] as const) {
    on('tool.call', { tool }, async ($, e, next) => {
      const ran = await next(e)
      if (ran.deny === undefined && ran.isError !== true && norm(e.file_path).startsWith(`${norm(BRAIN)}/`)) {
        const now = await $.clock.now()
        await update($, lastSaveAt, () => now)
      }
      return ran
    })
  }

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const band = await read($, info)
    if (e.props.hasSurvey || band === null) return next(e)

    const saved = await read($, lastSaveAt)
    const now = await $.clock.now()
    const savedMin = saved === null ? null : Math.round((now - saved) / 60_000)
    const tokens = band.tokens ?? 0

    const saveStale = savedMin === null ? tokens >= WARN_TOKENS : savedMin >= STALE_SAVE_MIN && tokens >= 100_000

    const { Box, Text } = $.ui.resolve(e)

    return (
      <Box flexDirection="column">
        <Box>
          <Text color={rampColor(tokens / CONTEXT_FULL)} bold={tokens >= WARN_TOKENS}>
            {band.tokens === null ? '?' : kTokens(band.tokens)}
            {band.percent === null ? '' : ` (${Math.round(band.percent)}%)`}
          </Text>
          <Text dimColor> · </Text>
          <Text color={saveStale ? ACCENT : undefined} dimColor={!saveStale}>
            {savedMin === null ? 'No Brain save this session' : `Brain saved ${ago(savedMin)} ago`}
          </Text>
        </Box>
        {band.limits.length > 0 && (
          <Box>
            {band.limits.map((limit, i) => (
              <Box key={limit.kind}>
                {i > 0 && <Text dimColor> · </Text>}
                <Text dimColor>{LIMIT_NAMES[limit.kind] ?? limit.kind} </Text>
                <Text color={rampColor(limit.percentUsed / 100)} bold={limit.percentUsed >= 75}>
                  {Math.round(limit.percentUsed)}%
                </Text>
                <Text dimColor>
                  {resetsIn(limit.resetsAt ?? undefined, now) === '' ? '' : ` (${resetsIn(limit.resetsAt ?? undefined, now)})`}
                </Text>
              </Box>
            ))}
          </Box>
        )}
        {band.project !== null && (
          <Text dimColor wrap="truncate-end">
            {band.project}
            {band.noteAgeMin === null ? '' : ` (note ${ago(band.noteAgeMin)} old)`}
            {' › '}
            {band.next === null ? 'no Resume Next line' : `Next: ${band.next}`}
          </Text>
        )}
      </Box>
    )
  })
}
