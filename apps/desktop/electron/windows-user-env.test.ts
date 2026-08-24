import assert from 'node:assert/strict'

import { test } from 'vitest'

import { expandWindowsEnvRefs, parseRegQueryValue, readWindowsUserEnvVar } from './windows-user-env'

// ── parseRegQueryValue ─────────────────────────────────────────────────────

test('parseRegQueryValue extracts a REG_SZ value', () => {
  const out = ['', 'HKEY_CURRENT_USER\\Environment', '    SYNAPSE_HOME    REG_SZ    F:\\Synapse\\data', ''].join('\r\n')
  assert.equal(parseRegQueryValue(out, 'SYNAPSE_HOME'), 'F:\\Synapse\\data')
})

test('parseRegQueryValue matches the name case-insensitively', () => {
  const out = 'HKEY_CURRENT_USER\\Environment\r\n    Synapse_Home    REG_EXPAND_SZ    %USERPROFILE%\\h\r\n'
  assert.equal(parseRegQueryValue(out, 'SYNAPSE_HOME'), '%USERPROFILE%\\h')
})

test('parseRegQueryValue preserves spaces inside the value', () => {
  const out = '    SYNAPSE_HOME    REG_SZ    C:\\Program Files\\Synapse\r\n'
  assert.equal(parseRegQueryValue(out, 'SYNAPSE_HOME'), 'C:\\Program Files\\Synapse')
})

test('parseRegQueryValue returns null when the value line is absent', () => {
  const out = 'HKEY_CURRENT_USER\\Environment\r\n    Path    REG_SZ    C:\\x\r\n'
  assert.equal(parseRegQueryValue(out, 'SYNAPSE_HOME'), null)
  assert.equal(parseRegQueryValue('', 'SYNAPSE_HOME'), null)
  assert.equal(parseRegQueryValue('garbage', 'SYNAPSE_HOME'), null)
})

// ── expandWindowsEnvRefs ───────────────────────────────────────────────────

test('expandWindowsEnvRefs expands %VAR% case-insensitively', () => {
  assert.equal(expandWindowsEnvRefs('%UserProfile%\\h', { USERPROFILE: 'C:\\Users\\jeff' }), 'C:\\Users\\jeff\\h')
})

test('expandWindowsEnvRefs leaves literal paths and unknown refs intact', () => {
  assert.equal(expandWindowsEnvRefs('F:\\Synapse\\data', {}), 'F:\\Synapse\\data')
  assert.equal(expandWindowsEnvRefs('%NOPE%\\x', {}), '%NOPE%\\x')
})

// ── readWindowsUserEnvVar ──────────────────────────────────────────────────

test('readWindowsUserEnvVar returns null off Windows without spawning', () => {
  let spawned = false

  const exec = () => {
    spawned = true

    return ''
  }

  assert.equal(readWindowsUserEnvVar('SYNAPSE_HOME', { platform: 'linux', exec }), null)
  assert.equal(spawned, false)
})

test('readWindowsUserEnvVar queries HKCU\\Environment and expands the value', () => {
  const calls = []

  const exec = (cmd, args) => {
    calls.push([cmd, args])

    return 'HKEY_CURRENT_USER\\Environment\r\n    SYNAPSE_HOME    REG_EXPAND_SZ    %DRIVE%\\Synapse\r\n'
  }

  const value = readWindowsUserEnvVar('SYNAPSE_HOME', {
    platform: 'win32',
    env: { DRIVE: 'F:' },
    exec
  })

  assert.equal(value, 'F:\\Synapse')
  assert.deepEqual(calls, [['reg', ['query', 'HKCU\\Environment', '/v', 'SYNAPSE_HOME']]])
})

test('readWindowsUserEnvVar returns null when reg exits non-zero (value missing)', () => {
  const exec = () => {
    throw new Error('reg exited 1')
  }

  assert.equal(readWindowsUserEnvVar('SYNAPSE_HOME', { platform: 'win32', exec }), null)
})

test('readWindowsUserEnvVar returns null for an empty value', () => {
  const exec = () => '    SYNAPSE_HOME    REG_SZ    \r\n'
  assert.equal(readWindowsUserEnvVar('SYNAPSE_HOME', { platform: 'win32', exec }), null)
})
