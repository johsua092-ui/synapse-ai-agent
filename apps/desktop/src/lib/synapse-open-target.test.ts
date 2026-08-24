import { describe, expect, it } from 'vitest'

import {
  normalizeSynapseOpenString,
  pathFromSynapseDeepLink,
  pathFromOpenDeepLink,
  resolveSynapseOpenPath
} from './synapse-open-target'

describe('normalizeSynapseOpenString', () => {
  it('accepts hash-router paths and strips a leading hash', () => {
    expect(normalizeSynapseOpenString('/index-network/intent/1')).toBe('/index-network/intent/1')
    expect(normalizeSynapseOpenString('#/index-network/intent/1')).toBe('/index-network/intent/1')
  })

  it('maps plugin-scoped synapse:// deep links to the same path', () => {
    expect(normalizeSynapseOpenString('synapse://index-network/intent/1')).toBe('/index-network/intent/1')
    expect(normalizeSynapseOpenString('synapse://index-network/intent/1?focus=true')).toBe(
      '/index-network/intent/1?focus=true'
    )
  })

  it('maps synapse://open/… deep links by stripping the open host', () => {
    expect(normalizeSynapseOpenString('synapse://open/index-network/intent/1')).toBe('/index-network/intent/1')
    expect(normalizeSynapseOpenString('synapse://open/settings/plugins')).toBe('/settings/plugins')
  })

  it('rejects reserved synapse kinds and unsafe paths', () => {
    expect(normalizeSynapseOpenString('synapse://blueprint/morning-brief')).toBeNull()
    expect(normalizeSynapseOpenString('synapse://plugin/install')).toBeNull()
    expect(normalizeSynapseOpenString('https://example.com/x')).toBeNull()
    expect(normalizeSynapseOpenString('/../etc/passwd')).toBeNull()
    expect(normalizeSynapseOpenString('index-network')).toBeNull()
  })
})

describe('resolveSynapseOpenPath', () => {
  it('merges structured path + params', () => {
    expect(resolveSynapseOpenPath({ path: '/index-network/intent/1', params: { focus: 'true' } })).toBe(
      '/index-network/intent/1?focus=true'
    )
  })

  it('resolves href the same as a bare string', () => {
    expect(resolveSynapseOpenPath({ href: 'synapse://index-network/intent/1' })).toBe('/index-network/intent/1')
  })
})

describe('pathFromSynapseDeepLink', () => {
  it('builds the navigate path from a plugin-scoped deep-link payload', () => {
    expect(pathFromSynapseDeepLink('index-network', 'intent/1')).toBe('/index-network/intent/1')
  })

  it('builds the navigate path from synapse://open/… payloads', () => {
    expect(pathFromOpenDeepLink('index-network/intent/1')).toBe('/index-network/intent/1')
    expect(pathFromSynapseDeepLink('open', 'agent/42')).toBe('/agent/42')
  })

  it('ignores reserved kinds', () => {
    expect(pathFromSynapseDeepLink('blueprint', 'morning-brief')).toBeNull()
    expect(pathFromSynapseDeepLink('plugin', 'install')).toBeNull()
  })
})
