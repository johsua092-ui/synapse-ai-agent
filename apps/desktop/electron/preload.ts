import { contextBridge, ipcRenderer, webFrame, webUtils } from 'electron'

// Which translucency the OS can back. Asked synchronously because the renderer
// needs it before its first paint, and answered by main because deciding it
// needs `os.release()` — a sandboxed preload may only require electron, events,
// timers and url, so importing node:os here throws before contextBridge runs
// and takes the ENTIRE bridge down with it (window.synapseDesktop undefined =>
// "Desktop IPC bridge is unavailable"). No reply means no glass, which degrades
// to an ordinary opaque window rather than a page thinned over nothing.
const translucencySupport = ipcRenderer.sendSync('synapse:translucency:support')
const hudNativeDrag = ipcRenderer.sendSync('synapse:hud:native-drag') === true

contextBridge.exposeInMainWorld('synapseDesktop', {
  glassSupported: translucencySupport?.glass === true,
  translucencySupported: translucencySupport?.translucency === true,
  getConnection: profile => ipcRenderer.invoke('synapse:connection', profile),
  // Registry-scoped backend resolution: { connectionId, profile } → descriptor.
  getConnectionFor: payload => ipcRenderer.invoke('synapse:connection:for', payload),
  getProfileRoutes: profiles => ipcRenderer.invoke('synapse:plugin-profile-routes', profiles),
  revalidateConnection: () => ipcRenderer.invoke('synapse:connection:revalidate'),
  touchBackend: profile => ipcRenderer.invoke('synapse:backend:touch', profile),
  getGatewayWsUrl: profile => ipcRenderer.invoke('synapse:gateway:ws-url', profile),
  // Registry-scoped fresh WS URL: { connectionId, profile } → result shape of
  // getGatewayWsUrl, minted against that connection's backend.
  getGatewayWsUrlFor: payload => ipcRenderer.invoke('synapse:gateway:ws-url-for', payload),
  // Union agent roster across every registered connection.
  getAgentRoster: () => ipcRenderer.invoke('synapse:agents:roster'),
  openSessionWindow: (sessionId, opts) => ipcRenderer.invoke('synapse:window:openSession', sessionId, opts),
  openSessionInTerminal: (sessionId, opts) => ipcRenderer.invoke('synapse:window:openInTerminal', sessionId, opts),
  openWindow: () => ipcRenderer.invoke('synapse:window:openInstance'),
  claimAmbientCue: key => ipcRenderer.invoke('synapse:ambient:claim', key),
  wakeIndicator: {
    getState: () => ipcRenderer.invoke('synapse:wake-indicator:get'),
    setState: state => ipcRenderer.send('synapse:wake-indicator:set', state),
    onState: callback => {
      const listener = (_event, state) => callback(state)
      ipcRenderer.on('synapse:wake-indicator:state', listener)

      return () => ipcRenderer.removeListener('synapse:wake-indicator:state', listener)
    }
  },
  petOverlay: {
    // Main renderer → main process: window lifecycle + drag. `request` is
    // `{ bounds, screen }`; resolves with the screen bounds it actually used.
    open: request => ipcRenderer.invoke('synapse:pet-overlay:open', request),
    close: () => ipcRenderer.invoke('synapse:pet-overlay:close'),
    setBounds: bounds => ipcRenderer.send('synapse:pet-overlay:set-bounds', bounds),
    setIgnoreMouse: ignore => ipcRenderer.send('synapse:pet-overlay:ignore-mouse', ignore),
    // Flip the overlay focusable (and focus it) while the composer needs keys.
    setFocusable: focusable => ipcRenderer.send('synapse:pet-overlay:set-focusable', focusable),
    // Main renderer → overlay (forwarded by main): push the latest pet state.
    pushState: payload => ipcRenderer.send('synapse:pet-overlay:state', payload),
    // Overlay → main renderer (forwarded by main): pop back in / composer submit.
    control: payload => ipcRenderer.send('synapse:pet-overlay:control', payload),
    // Overlay subscribes to state pushes.
    onState: callback => {
      const listener = (_event, payload) => callback(payload)
      ipcRenderer.on('synapse:pet-overlay:state', listener)

      return () => ipcRenderer.removeListener('synapse:pet-overlay:state', listener)
    },
    // Main renderer subscribes to overlay control messages.
    onControl: callback => {
      const listener = (_event, payload) => callback(payload)
      ipcRenderer.on('synapse:pet-overlay:control', listener)

      return () => ipcRenderer.removeListener('synapse:pet-overlay:control', listener)
    }
  },
  // HUD mode: the chrome-free floating chat. A full app renderer (own gateway)
  // sized as a floating bar, so it mounts the real composer. Main owns the
  // window; `onChanged` keeps every window's toggle truthful.
  hud: {
    nativeDrag: hudNativeDrag,
    open: request => ipcRenderer.invoke('synapse:hud:open', request),
    close: () => ipcRenderer.invoke('synapse:hud:close'),
    setIgnoreMouse: ignore => ipcRenderer.send('synapse:hud:ignore-mouse', ignore),
    moveBy: delta => ipcRenderer.send('synapse:hud:move-by', delta),
    setWorkspaceTransfer: transferring => ipcRenderer.send('synapse:hud:workspace-transfer', transferring),
    setBounds: bounds => ipcRenderer.send('synapse:hud:set-bounds', bounds),
    resetLayout: () => ipcRenderer.invoke('synapse:hud:reset-layout'),
    // Whether the band covers the window below the bar. Main pairs it with the
    // user's translucency setting to decide the native frost (macOS vibrancy /
    // Windows 11 DWM backdrop) — see hudFrostFor.
    setFrost: showing => ipcRenderer.invoke('synapse:hud:frost', showing),
    // The HUD tells main which session it is on; main hands that back to the
    // app window when the HUD closes, so the app can re-home onto it.
    setSession: sessionId => ipcRenderer.send('synapse:hud:session', sessionId),
    onGoto: callback => {
      const listener = (_event, sessionId) => callback(sessionId)
      ipcRenderer.on('synapse:hud:goto', listener)

      return () => ipcRenderer.removeListener('synapse:hud:goto', listener)
    },
    onChanged: callback => {
      const listener = (_event, state) => callback(state)
      ipcRenderer.on('synapse:hud:changed', listener)

      return () => ipcRenderer.removeListener('synapse:hud:changed', listener)
    },
    // Linux only, and silent elsewhere: where the cursor is, in page
    // coordinates, or null when it has left the window. Stands in for the
    // mousemove that `setIgnoreMouseEvents(true, { forward: true })` delivers on
    // macOS and Windows but not here.
    onCursor: callback => {
      const listener = (_event, point) => callback(point)
      ipcRenderer.on('synapse:hud:cursor', listener)

      return () => ipcRenderer.removeListener('synapse:hud:cursor', listener)
    },
    // Main's game-overlay watch: whether a fullscreen app (a game) is under
    // the HUD, so the renderer can step back to the low-opacity overlay
    // treatment while one owns the screen.
    onGameOverlay: callback => {
      const listener = (_event, state) => callback(state)
      ipcRenderer.on('synapse:hud:game-overlay', listener)

      return () => ipcRenderer.removeListener('synapse:hud:game-overlay', listener)
    }
  },
  // Quick Entry: the global-hotkey mini composer window. Main owns the OS
  // shortcut + the persisted preference; the quick window only captures text
  // and hands it back, and the primary renderer submits it through the normal
  // prompt path.
  quickEntry: {
    getSettings: () => ipcRenderer.invoke('synapse:quick-entry:settings:get'),
    setSettings: patch => ipcRenderer.invoke('synapse:quick-entry:settings:set', patch),
    submit: payload => ipcRenderer.send('synapse:quick-entry:submit', payload),
    dismiss: () => ipcRenderer.send('synapse:quick-entry:dismiss'),
    // Primary renderer → main → quick window: gateway connection state + the
    // recent-session options the target picker offers. Main caches the latest
    // payload so a freshly spawned quick window starts from truth.
    pushState: payload => ipcRenderer.send('synapse:quick-entry:state', payload),
    // Quick window subscribes to those pushes.
    onState: callback => {
      const listener = (_event, payload) => callback(payload)
      ipcRenderer.on('synapse:quick-entry:state', listener)

      return () => ipcRenderer.removeListener('synapse:quick-entry:state', listener)
    },
    // Main → primary renderer: a submit captured by the quick window.
    onSubmit: callback => {
      const listener = (_event, payload) => callback(payload)
      ipcRenderer.on('synapse:quick-entry:submit', listener)

      return () => ipcRenderer.removeListener('synapse:quick-entry:submit', listener)
    },
    // Main → quick window: you were just summoned (reset draft + refocus).
    onShown: callback => {
      const listener = () => callback()
      ipcRenderer.on('synapse:quick-entry:shown', listener)

      return () => ipcRenderer.removeListener('synapse:quick-entry:shown', listener)
    }
  },
  getBootProgress: () => ipcRenderer.invoke('synapse:boot-progress:get'),
  getConnectionConfig: profile => ipcRenderer.invoke('synapse:connection-config:get', profile),
  saveConnectionConfig: payload => ipcRenderer.invoke('synapse:connection-config:save', payload),
  applyConnectionConfig: payload => ipcRenderer.invoke('synapse:connection-config:apply', payload),
  testConnectionConfig: payload => ipcRenderer.invoke('synapse:connection-config:test', payload),
  // v2 multi-connection registry: named agent sources (local / remote / cloud / ssh).
  connections: {
    list: () => ipcRenderer.invoke('synapse:connections:list'),
    save: payload => ipcRenderer.invoke('synapse:connections:save', payload),
    remove: id => ipcRenderer.invoke('synapse:connections:remove', id),
    setPrimary: id => ipcRenderer.invoke('synapse:connections:set-primary', id),
    setLaunchMode: mode => ipcRenderer.invoke('synapse:connections:set-launch-mode', mode),
    setLastUsed: id => ipcRenderer.invoke('synapse:connections:set-last-used', id),
    test: id => ipcRenderer.invoke('synapse:connections:test', id),
    // Fan out `synapse update` to every eligible registered connection.
    // Optional excludeIds skips rows the caller updates through another path.
    updateAll: options => ipcRenderer.invoke('synapse:connections:update-all', options),
    // Registry lifecycle push (main → renderer): a connection was removed or
    // materially edited, so secondaries scoped to it must be disposed (and,
    // for edits, re-dialed at the new target).
    onChanged: callback => {
      const listener = (_event, payload) => callback(payload)
      ipcRenderer.on('synapse:connections:changed', listener)

      return () => ipcRenderer.removeListener('synapse:connections:changed', listener)
    }
  },
  sshConfigHosts: () => ipcRenderer.invoke('synapse:ssh-config:hosts'),
  sshResolveHost: host => ipcRenderer.invoke('synapse:ssh-config:resolve', host),
  probeConnectionConfig: remoteUrl => ipcRenderer.invoke('synapse:connection-config:probe', remoteUrl),
  oauthLoginConnectionConfig: remoteUrl => ipcRenderer.invoke('synapse:connection-config:oauth-login', remoteUrl),
  oauthLogoutConnectionConfig: remoteUrl => ipcRenderer.invoke('synapse:connection-config:oauth-logout', remoteUrl),
  // Synapse Cloud: one portal login powers discovery + silent per-agent sign-in
  // (cloud-auto-discovery Phase 3).
  cloud: {
    status: () => ipcRenderer.invoke('synapse:cloud:status'),
    login: () => ipcRenderer.invoke('synapse:cloud:login'),
    logout: () => ipcRenderer.invoke('synapse:cloud:logout'),
    discover: org => ipcRenderer.invoke('synapse:cloud:discover', org),
    agentSignIn: dashboardUrl => ipcRenderer.invoke('synapse:cloud:agent-sign-in', dashboardUrl)
  },
  profile: {
    get: () => ipcRenderer.invoke('synapse:profile:get'),
    set: name => ipcRenderer.invoke('synapse:profile:set', name)
  },
  api: request => ipcRenderer.invoke('synapse:api', request),
  notify: payload => ipcRenderer.invoke('synapse:notify', payload),
  requestMicrophoneAccess: () => ipcRenderer.invoke('synapse:requestMicrophoneAccess'),
  readWindowBelow: () => ipcRenderer.invoke('synapse:window:readBelow'),
  readFileDataUrl: filePath => ipcRenderer.invoke('synapse:readFileDataUrl', filePath),
  readFileDataUrlForAttach: filePath => ipcRenderer.invoke('synapse:readFileDataUrlForAttach', filePath),
  dataUrlReadMax: {
    get: () => ipcRenderer.invoke('synapse:data-url-read-max:get'),
    set: maxMb => ipcRenderer.invoke('synapse:data-url-read-max:set', maxMb)
  },
  readFileText: filePath => ipcRenderer.invoke('synapse:readFileText', filePath),
  readPluginSource: (filePath: string) => ipcRenderer.invoke('synapse:readPluginSource', filePath),
  selectPaths: options => ipcRenderer.invoke('synapse:selectPaths', options),
  selectSavePath: options => ipcRenderer.invoke('synapse:selectSavePath', options),
  writeClipboard: text => ipcRenderer.invoke('synapse:writeClipboard', text),
  readClipboard: () => ipcRenderer.invoke('synapse:readClipboard'),
  saveGatewayFile: payload => ipcRenderer.invoke('synapse:saveGatewayFile', payload),
  saveImageFromUrl: url => ipcRenderer.invoke('synapse:saveImageFromUrl', url),
  contextMenuEdit: command => ipcRenderer.invoke('synapse:context-menu:edit', command),
  contextMenuCopyImage: () => ipcRenderer.invoke('synapse:context-menu:copy-image'),
  contextMenuSpellcheck: action => ipcRenderer.invoke('synapse:context-menu:spellcheck', action),
  contextMenuGuestAddWord: payload => ipcRenderer.invoke('synapse:context-menu:guest-add-word', payload),
  onContextMenuSpellcheck: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('synapse:context-menu-spellcheck', listener)

    return () => ipcRenderer.removeListener('synapse:context-menu-spellcheck', listener)
  },
  saveImageBuffer: (data, ext) => ipcRenderer.invoke('synapse:saveImageBuffer', { data, ext }),
  saveClipboardImage: () => ipcRenderer.invoke('synapse:saveClipboardImage'),
  getPathForFile: file => {
    try {
      return webUtils.getPathForFile(file) || ''
    } catch {
      return ''
    }
  },
  normalizePreviewTarget: (target, baseDir) => ipcRenderer.invoke('synapse:normalizePreviewTarget', target, baseDir),
  watchPreviewFile: url => ipcRenderer.invoke('synapse:watchPreviewFile', url),
  watchDirectory: dir => ipcRenderer.invoke('synapse:watchDirectory', dir),
  stopPreviewFileWatch: id => ipcRenderer.invoke('synapse:stopPreviewFileWatch', id),
  setActiveWork: payload => ipcRenderer.send('synapse:active-work', payload),
  setTitleBarTheme: payload => ipcRenderer.send('synapse:titlebar-theme', payload),
  setNativeTheme: mode => ipcRenderer.send('synapse:native-theme', mode),
  setTranslucency: payload => ipcRenderer.send('synapse:translucency', payload),
  setKeepAwake: on => ipcRenderer.send('synapse:keep-awake', on),
  setDisableF12: blocked => ipcRenderer.send('synapse:devtools:disable-f12', blocked),
  setPreviewShortcutActive: active => ipcRenderer.send('synapse:previewShortcutActive', Boolean(active)),
  openExternal: url => ipcRenderer.invoke('synapse:openExternal', url),
  openPreviewInBrowser: url => ipcRenderer.invoke('synapse:openPreviewInBrowser', url),
  reachPreviewUrl: url => ipcRenderer.invoke('synapse:preview:reach', url),
  fetchLinkTitle: url => ipcRenderer.invoke('synapse:fetchLinkTitle', url),
  resolveFavicon: url => ipcRenderer.invoke('synapse:resolveFavicon', url),
  sanitizeWorkspaceCwd: cwd => ipcRenderer.invoke('synapse:workspace:sanitize', cwd),
  settings: {
    getDefaultProjectDir: () => ipcRenderer.invoke('synapse:setting:defaultProjectDir:get'),
    setDefaultProjectDir: dir => ipcRenderer.invoke('synapse:setting:defaultProjectDir:set', dir),
    pickDefaultProjectDir: () => ipcRenderer.invoke('synapse:setting:defaultProjectDir:pick')
  },
  zoom: {
    // Current zoom of this window, as { level, percent }.
    get: () => ipcRenderer.invoke('synapse:zoom:get'),
    // Synchronous zoom factor (1 = 100%). Coordinate math needs it in the
    // same tick as the event it converts, so no IPC round-trip here.
    factor: () => webFrame.getZoomFactor(),
    setPercent: percent => ipcRenderer.send('synapse:zoom:set-percent', percent),
    // Fires on every zoom change, including the Ctrl/Cmd +/-/0 shortcuts,
    // so the settings UI can stay in sync with the keyboard.
    onChanged: callback => {
      const listener = (_event, payload) => callback(payload)
      ipcRenderer.on('synapse:zoom:changed', listener)

      return () => ipcRenderer.removeListener('synapse:zoom:changed', listener)
    }
  },
  revealLogs: () => ipcRenderer.invoke('synapse:logs:reveal'),
  getRecentLogs: () => ipcRenderer.invoke('synapse:logs:recent'),
  // Fire-and-forget: persists a renderer error-boundary catch (with component
  // stack) to desktop.log so crashes survive the window (#79428).
  reportRendererError: report => ipcRenderer.send('synapse:logs:renderer-error', report),
  readDir: dirPath => ipcRenderer.invoke('synapse:fs:readDir', dirPath),
  gitRoot: startPath => ipcRenderer.invoke('synapse:fs:gitRoot', startPath),
  revealPath: targetPath => ipcRenderer.invoke('synapse:fs:reveal', targetPath),
  openDir: dirPath => ipcRenderer.invoke('synapse:fs:openDir', dirPath),
  desktopPluginsRoot: () => ipcRenderer.invoke('synapse:fs:desktopPluginsRoot'),
  logsRoot: () => ipcRenderer.invoke('synapse:fs:logsRoot'),
  agentPluginsRoot: () => ipcRenderer.invoke('synapse:fs:agentPluginsRoot'),
  renamePath: (targetPath, newName) => ipcRenderer.invoke('synapse:fs:rename', targetPath, newName),
  writeTextFile: (filePath, content) => ipcRenderer.invoke('synapse:fs:writeText', filePath, content),
  trashPath: targetPath => ipcRenderer.invoke('synapse:fs:trash', targetPath),
  git: {
    worktreeList: repoPath => ipcRenderer.invoke('synapse:git:worktreeList', repoPath),
    worktreeAdd: (repoPath, options) => ipcRenderer.invoke('synapse:git:worktreeAdd', repoPath, options),
    worktreeRemove: (repoPath, worktreePath, options) =>
      ipcRenderer.invoke('synapse:git:worktreeRemove', repoPath, worktreePath, options),
    branchSwitch: (repoPath, branch) => ipcRenderer.invoke('synapse:git:branchSwitch', repoPath, branch),
    branchList: repoPath => ipcRenderer.invoke('synapse:git:branchList', repoPath),
    baseBranchList: repoPath => ipcRenderer.invoke('synapse:git:baseBranchList', repoPath),
    repoStatus: repoPath => ipcRenderer.invoke('synapse:git:repoStatus', repoPath),
    fileDiff: (repoPath, filePath) => ipcRenderer.invoke('synapse:git:fileDiff', repoPath, filePath),
    scanRepos: (roots, options) => ipcRenderer.invoke('synapse:git:scanRepos', roots, options),
    review: {
      list: (repoPath, scope, baseRef) => ipcRenderer.invoke('synapse:git:review:list', repoPath, scope, baseRef),
      diff: (repoPath, filePath, scope, baseRef, staged) =>
        ipcRenderer.invoke('synapse:git:review:diff', repoPath, filePath, scope, baseRef, staged),
      stage: (repoPath, filePath) => ipcRenderer.invoke('synapse:git:review:stage', repoPath, filePath),
      unstage: (repoPath, filePath) => ipcRenderer.invoke('synapse:git:review:unstage', repoPath, filePath),
      revert: (repoPath, filePath) => ipcRenderer.invoke('synapse:git:review:revert', repoPath, filePath),
      revParse: (repoPath, ref) => ipcRenderer.invoke('synapse:git:review:revParse', repoPath, ref),
      commit: (repoPath, message, push) => ipcRenderer.invoke('synapse:git:review:commit', repoPath, message, push),
      commitContext: repoPath => ipcRenderer.invoke('synapse:git:review:commitContext', repoPath),
      push: repoPath => ipcRenderer.invoke('synapse:git:review:push', repoPath),
      shipInfo: repoPath => ipcRenderer.invoke('synapse:git:review:shipInfo', repoPath),
      prList: (repoPath, branches, numbers) =>
        ipcRenderer.invoke('synapse:git:review:prList', repoPath, branches, numbers),
      fetchPrComment: (repoPath, url) => ipcRenderer.invoke('synapse:git:review:fetchPrComment', repoPath, url),
      createPr: repoPath => ipcRenderer.invoke('synapse:git:review:createPr', repoPath)
    }
  },
  terminal: {
    cwd: id => ipcRenderer.invoke('synapse:terminal:cwd', id),
    dispose: id => ipcRenderer.invoke('synapse:terminal:dispose', id),
    resize: (id, size) => ipcRenderer.invoke('synapse:terminal:resize', id, size),
    start: options => ipcRenderer.invoke('synapse:terminal:start', options),
    write: (id, data) => ipcRenderer.invoke('synapse:terminal:write', id, data),
    onData: (id, callback) => {
      const channel = `synapse:terminal:${id}:data`
      const listener = (_event, payload) => callback(payload)
      ipcRenderer.on(channel, listener)

      return () => ipcRenderer.removeListener(channel, listener)
    },
    onExit: (id, callback) => {
      const channel = `synapse:terminal:${id}:exit`
      const listener = (_event, payload) => callback(payload)
      ipcRenderer.on(channel, listener)

      return () => ipcRenderer.removeListener(channel, listener)
    }
  },
  onClosePreviewRequested: callback => {
    const listener = () => callback()
    ipcRenderer.on('synapse:close-preview-requested', listener)

    return () => ipcRenderer.removeListener('synapse:close-preview-requested', listener)
  },
  onPreviewNav: callback => {
    const listener = (_event, command) => callback(command)
    ipcRenderer.on('synapse:preview-nav', listener)

    return () => ipcRenderer.removeListener('synapse:preview-nav', listener)
  },
  onOpenFolderRequested: callback => {
    const listener = () => callback()
    ipcRenderer.on('synapse:open-folder-requested', listener)

    return () => ipcRenderer.removeListener('synapse:open-folder-requested', listener)
  },
  onOpenUpdatesRequested: callback => {
    const listener = () => callback()
    ipcRenderer.on('synapse:open-updates', listener)

    return () => ipcRenderer.removeListener('synapse:open-updates', listener)
  },
  onDeepLink: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('synapse:deep-link', listener)

    return () => ipcRenderer.removeListener('synapse:deep-link', listener)
  },
  signalDeepLinkReady: () => ipcRenderer.invoke('synapse:deep-link-ready'),
  probePluginRepo: payload => ipcRenderer.invoke('synapse:plugin:probe', payload),
  installDesktopPlugin: payload => ipcRenderer.invoke('synapse:plugin:installDesktop', payload),
  onWindowStateChanged: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('synapse:window-state-changed', listener)

    return () => ipcRenderer.removeListener('synapse:window-state-changed', listener)
  },
  onFocusSession: callback => {
    const listener = (_event, sessionId) => callback(sessionId)
    ipcRenderer.on('synapse:focus-session', listener)

    return () => ipcRenderer.removeListener('synapse:focus-session', listener)
  },
  onNotificationAction: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('synapse:notification-action', listener)

    return () => ipcRenderer.removeListener('synapse:notification-action', listener)
  },
  onNotificationActivate: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('synapse:notification-activate', listener)

    return () => ipcRenderer.removeListener('synapse:notification-activate', listener)
  },
  onPreviewFileChanged: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('synapse:preview-file-changed', listener)

    return () => ipcRenderer.removeListener('synapse:preview-file-changed', listener)
  },
  onBackendExit: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('synapse:backend-exit', listener)

    return () => ipcRenderer.removeListener('synapse:backend-exit', listener)
  },
  // Soft gateway-mode apply finished tearing down the primary backend. Renderer
  // should wipe session lists + re-dial without a window reload.
  onConnectionApplied: callback => {
    const listener = () => callback()
    ipcRenderer.on('synapse:connection:applied', listener)

    return () => ipcRenderer.removeListener('synapse:connection:applied', listener)
  },
  onPowerResume: callback => {
    const listener = () => callback()
    ipcRenderer.on('synapse:power-resume', listener)

    return () => ipcRenderer.removeListener('synapse:power-resume', listener)
  },
  // AC ↔ battery transitions; renderers slow their backstop polls on battery.
  getOnBattery: () => ipcRenderer.invoke('synapse:power-battery:get'),
  onBatteryChanged: callback => {
    const listener = (_event, onBattery) => callback(Boolean(onBattery))
    ipcRenderer.on('synapse:power-battery', listener)

    return () => ipcRenderer.removeListener('synapse:power-battery', listener)
  },
  onBootProgress: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('synapse:boot-progress', listener)

    return () => ipcRenderer.removeListener('synapse:boot-progress', listener)
  },
  // First-launch bootstrap progress -- emitted by the install.ps1 stage
  // runner in main.ts (apps/desktop/electron/bootstrap-runner.ts).
  // Renderer's install overlay subscribes to live events and queries the
  // current snapshot via getBootstrapState() to recover after a devtools
  // reload mid-bootstrap.
  getBootstrapState: () => ipcRenderer.invoke('synapse:bootstrap:get'),
  continueBootstrapLocal: () => ipcRenderer.invoke('synapse:bootstrap:continue-local'),
  resetBootstrap: () => ipcRenderer.invoke('synapse:bootstrap:reset'),
  repairBootstrap: () => ipcRenderer.invoke('synapse:bootstrap:repair'),
  cancelBootstrap: () => ipcRenderer.invoke('synapse:bootstrap:cancel'),
  onBootstrapEvent: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('synapse:bootstrap:event', listener)

    return () => ipcRenderer.removeListener('synapse:bootstrap:event', listener)
  },
  getVersion: () => ipcRenderer.invoke('synapse:version'),
  getRemoteDisplayReason: () => ipcRenderer.invoke('synapse:get-remote-display-reason'),
  uninstall: {
    summary: () => ipcRenderer.invoke('synapse:uninstall:summary'),
    run: mode => ipcRenderer.invoke('synapse:uninstall:run', { mode })
  },
  updates: {
    check: () => ipcRenderer.invoke('synapse:updates:check'),
    apply: opts => ipcRenderer.invoke('synapse:updates:apply', opts),
    getBranch: () => ipcRenderer.invoke('synapse:updates:branch:get'),
    setBranch: name => ipcRenderer.invoke('synapse:updates:branch:set', name),
    onProgress: callback => {
      const listener = (_event, payload) => callback(payload)
      ipcRenderer.on('synapse:updates:progress', listener)

      return () => ipcRenderer.removeListener('synapse:updates:progress', listener)
    }
  },
  themes: {
    fetchMarketplace: id => ipcRenderer.invoke('synapse:vscode-theme:fetch', id),
    searchMarketplace: query => ipcRenderer.invoke('synapse:vscode-theme:search', query)
  },
  // Find-in-page (Ctrl/Cmd+F): delegates to Electron's
  // webContents.findInPage on the IPC sender's window so a Cmd+F pressed
  // in a secondary session window searches THAT window, not the primary.
  // `onFoundInPage` returns the unsubscribe fn; the renderer wires it via
  // `initFindInPageListener` in store/find-in-page.ts and tears it down
  // when the FindBar unmounts.
  findInPage: (query, options) => ipcRenderer.invoke('synapse:find-in-page', query, options),
  stopFindInPage: () => ipcRenderer.invoke('synapse:stop-find-in-page'),
  onFoundInPage: callback => {
    const listener = (_event, result) => callback(result)
    ipcRenderer.on('synapse:found-in-page', listener)

    return () => ipcRenderer.removeListener('synapse:found-in-page', listener)
  },
  // Main-process `before-input-event` forwards Ctrl/Cmd+F here so renderer
  // can open the FindBar even when the GTK compositor has already grabbed
  // the chord at the windowing layer (#81727).
  onOpenFindBarRequested: callback => {
    const listener = () => callback()
    ipcRenderer.on('synapse:open-find-bar', listener)

    return () => ipcRenderer.removeListener('synapse:open-find-bar', listener)
  }
})
