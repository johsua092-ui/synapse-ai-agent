import { useEffect, useState } from "react";
import {
  Bot,
  Pencil,
  Plus,
  Trash2,
  Users,
  Play,
  Loader2,
  X,
} from "lucide-react";
import { api } from "@/lib/api";
import type {
  AgentInfo,
  AgentTeamInfo,
  AgentTeamTask,
  SkillInfo,
  ToolsetInfo,
  ActiveSubagent,
} from "@/lib/api";
import { useProfileScope } from "@/contexts/useProfileScope";
import { useToast } from "@nous-research/ui/hooks/use-toast";
import { Toast } from "@nous-research/ui/ui/components/toast";
import { Card, CardContent, CardHeader, CardTitle } from "@nous-research/ui/ui/components/card";
import { Badge } from "@nous-research/ui/ui/components/badge";
import { Button } from "@nous-research/ui/ui/components/button";
import { Spinner } from "@nous-research/ui/ui/components/spinner";
import { Input } from "@nous-research/ui/ui/components/input";
import { Label } from "@nous-research/ui/ui/components/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@nous-research/ui/ui/components/dialog";
import { usePageHeader } from "@/contexts/usePageHeader";

function CheckboxPicker({
  available,
  selected,
  onChange,
  emptyLabel,
}: {
  available: Array<{ name: string; label?: string; description?: string | null }>;
  selected: string[];
  onChange: (names: string[]) => void;
  emptyLabel: string;
}) {
  const all = [...available];
  const orphaned = selected.filter(
    (s) => !all.some((item) => item.name === s),
  ).map((name) => ({ name, label: name, description: "" }));

  if (all.length === 0 && orphaned.length === 0) {
    return <p className="text-xs text-muted-foreground">{emptyLabel}</p>;
  }
  const rows = [...orphaned, ...all];
  const toggle = (name: string, checked: boolean) => {
    if (checked) onChange([...selected, name]);
    else onChange(selected.filter((s) => s !== name));
  };
  return (
    <div className="max-h-36 overflow-y-auto border border-border bg-background/40 p-1">
      {rows.map((item) => (
        <label
          key={item.name}
          className="flex cursor-pointer items-center gap-2 px-2 py-1 text-xs hover:bg-muted/40"
          title={item.description || undefined}
        >
          <input
            type="checkbox"
            className="accent-foreground"
            checked={selected.includes(item.name)}
            onChange={(e) => toggle(item.name, e.target.checked)}
          />
          <span className="font-mono-ui truncate">{item.label || item.name}</span>
        </label>
      ))}
    </div>
  );
}

function AgentEditor({
  editName,
  existing,
  skills,
  toolsets,
  profile,
  onClose,
  onSaved,
}: {
  editName: string | null;
  existing: AgentInfo | null;
  skills: SkillInfo[];
  toolsets: ToolsetInfo[];
  profile?: string;
  onClose: () => void;
  onSaved: () => Promise<void>;
}) {
  const { showToast } = useToast();
  const [name, setName] = useState(existing?.name ?? editName ?? "");
  const [model, setModel] = useState(existing?.model ?? "");
  const [task, setTask] = useState(existing?.task ?? "");
  const [selSkills, setSelSkills] = useState<string[]>(existing?.skills ?? []);
  const [selTools, setSelTools] = useState<string[]>(existing?.toolsets ?? []);
  const [busy, setBusy] = useState(false);

  const handleSave = async () => {
    const trimmed = name.trim();
    if (!trimmed) {
      showToast("A subagent name is required", "error");
      return;
    }
    setBusy(true);
    try {
      if (editName) {
        await api.updateAgent(
          editName,
          { model, task, skills: selSkills, toolsets: selTools },
          profile,
        );
      } else {
        await api.createAgent(
          { name: trimmed, model, task, skills: selSkills, toolsets: selTools },
          profile,
        );
      }
      await onSaved();
      onClose();
    } catch {
      showToast("Failed to save subagent", "error");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{editName ? "Edit subagent" : "New subagent"}</DialogTitle>
          <DialogDescription>
            Define a reusable subagent with its own model, skills, and toolsets.
          </DialogDescription>
        </DialogHeader>
        <div className="flex flex-col gap-3 py-2">
          {!editName && (
            <div className="flex flex-col gap-1.5">
              <Label>Name</Label>
              <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="security-reviewer" />
            </div>
          )}
          <div className="flex flex-col gap-1.5">
            <Label>Model (optional)</Label>
            <Input value={model} onChange={(e) => setModel(e.target.value)} placeholder="leave empty for default" />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Task (optional)</Label>
            <Input value={task} onChange={(e) => setTask(e.target.value)} placeholder="What this subagent should do" />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Skills</Label>
            <CheckboxPicker
              available={skills.map((s) => ({ name: s.name, description: s.description }))}
              selected={selSkills}
              onChange={setSelSkills}
              emptyLabel="No skills available"
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Toolsets</Label>
            <CheckboxPicker
              available={toolsets.map((t) => ({ name: t.name, label: t.label, description: t.description }))}
              selected={selTools}
              onChange={setSelTools}
              emptyLabel="Inherit parent toolsets"
            />
          </div>
        </div>
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={onClose} disabled={busy}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={busy}>
            {busy && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Save
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default function AgentsPage() {
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [teams, setTeams] = useState<AgentTeamInfo[]>([]);
  const [active, setActive] = useState<ActiveSubagent[]>([]);
  const [skills, setSkills] = useState<SkillInfo[]>([]);
  const [toolsets, setToolsets] = useState<ToolsetInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<{ mode: "create" } | { mode: "edit"; agent: AgentInfo } | null>(null);
  const [teamSeed, setTeamSeed] = useState<string[]>([]);
  const [teamResult, setTeamResult] = useState<{ name: string; tasks: AgentTeamTask[] } | null>(null);
  const [runningTeam, setRunningTeam] = useState<string | null>(null);
  const { showToast } = useToast();
  const { profile: selectedProfile } = useProfileScope();
  const { setAfterTitle, setEnd } = usePageHeader();

  const reload = async () => {
    const [ag, tm, act, sk, tl] = await Promise.all([
      api.getAgents(selectedProfile || undefined),
      api.getTeams(selectedProfile || undefined).catch(() => ({ teams: [] })),
      api.getActiveSubagents().catch(() => ({ active: [] })),
      api.getSkills(selectedProfile || undefined).catch(() => []),
      api.getToolsets(selectedProfile || undefined).catch(() => []),
    ]);
    setAgents(ag.agents);
    setTeams(tm.teams);
    setActive(act.active);
    setSkills(sk);
    setToolsets(tl);
  };

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      api.getAgents(selectedProfile || undefined),
      api.getTeams(selectedProfile || undefined).catch(() => ({ teams: [] })),
      api.getActiveSubagents().catch(() => ({ active: [] })),
      api.getSkills(selectedProfile || undefined).catch(() => []),
      api.getToolsets(selectedProfile || undefined).catch(() => []),
    ])
      .then(([ag, tm, act, sk, tl]) => {
        if (cancelled) return;
        setAgents(ag.agents);
        setTeams(tm.teams);
        setActive(act.active);
        setSkills(sk);
        setToolsets(tl);
      })
      .catch(() => !cancelled && showToast("Failed to load agents", "error"))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [selectedProfile]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (agents.length) setAfterTitle(<span className="text-xs text-muted-foreground">{agents.length}</span>);
    else setAfterTitle(null);
    setEnd(null);
    return () => {
      setAfterTitle(null);
      setEnd(null);
    };
  }, [agents.length, setAfterTitle, setEnd]);

  const handleDelete = async (name: string) => {
    try {
      await api.deleteAgent(name, selectedProfile || undefined);
      await reload();
      showToast(`Deleted subagent ${name}`);
    } catch {
      showToast("Failed to delete subagent", "error");
    }
  };

  const handleDeleteTeam = async (name: string) => {
    try {
      await api.deleteTeam(name, selectedProfile || undefined);
      await reload();
      showToast(`Deleted team ${name}`);
    } catch {
      showToast("Failed to delete team", "error");
    }
  };

  const handleRunTeam = async (name: string) => {
    setRunningTeam(name);
    try {
      const res = await api.runTeam(name, undefined, selectedProfile || undefined);
      setTeamResult(res);
    } catch {
      showToast("Failed to run team", "error");
    } finally {
      setRunningTeam(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Spinner className="text-2xl text-primary" />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <Toast />
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <Bot className="h-5 w-5" /> Agents
        </h2>
        <Button onClick={() => setEditing({ mode: "create" })}>
          <Plus className="mr-2 h-4 w-4" /> New subagent
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm">
            <Bot className="h-4 w-4" /> Subagents
          </CardTitle>
        </CardHeader>
        <CardContent>
          {agents.length === 0 ? (
            <p className="text-sm text-muted-foreground">No subagents defined yet.</p>
          ) : (
            <div className="flex flex-col">
              {agents.map((a) => (
                <div
                  key={a.name}
                  className="group flex items-start gap-3 px-3 py-2.5 transition-colors hover:bg-muted/40"
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono-ui text-sm">{a.name}</span>
                      {a.model && <Badge variant="outline">{a.model}</Badge>}
                    </div>
                    {a.task && <p className="mt-1 text-xs text-muted-foreground">{a.task}</p>}
                    <div className="mt-1 flex flex-wrap gap-1">
                      {a.skills.map((s) => (
                        <Badge key={s} variant="secondary">{s}</Badge>
                      ))}
                      {a.toolsets.map((t) => (
                        <Badge key={t} variant="outline">{t}</Badge>
                      ))}
                    </div>
                  </div>
                  <div className="flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                    <Button
                      variant="ghost"
                      size="icon"
                      title="Edit"
                      onClick={() => setEditing({ mode: "edit", agent: a })}
                    >
                      <Pencil className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      title="Delete"
                      onClick={() => handleDelete(a.name)}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm">
            <Users className="h-4 w-4" /> Agent Teams
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {teams.length === 0 ? (
            <p className="text-sm text-muted-foreground">No teams defined yet.</p>
          ) : (
            teams.map((t) => (
              <div
                key={t.name}
                className="group flex items-start gap-3 px-3 py-2.5 transition-colors hover:bg-muted/40"
              >
                <div className="min-w-0 flex-1">
                  <span className="font-mono-ui text-sm">{t.name}</span>
                  <p className="mt-1 flex flex-wrap gap-1 text-xs text-muted-foreground">
                    {t.agents.map((a) => (
                      <Badge key={a} variant="outline">{a}</Badge>
                    ))}
                  </p>
                </div>
                <div className="flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                  <Button
                    variant="ghost"
                    size="icon"
                    title="Run"
                    onClick={() => handleRunTeam(t.name)}
                    disabled={runningTeam === t.name}
                  >
                    {runningTeam === t.name ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <Play className="h-3.5 w-3.5" />
                    )}
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    title="Delete team"
                    onClick={() => handleDeleteTeam(t.name)}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </div>
            ))
          )}
          <div className="border-t border-border pt-3">
            <p className="pb-2 text-xs text-muted-foreground">Assemble a new team from saved subagents:</p>
            <CheckboxPicker
              available={agents.map((a) => ({ name: a.name }))}
              selected={teamSeed}
              onChange={setTeamSeed}
              emptyLabel="No subagents to add"
            />
            <div className="mt-2 flex items-center gap-2">
              <Input
                placeholder="team name"
                id="team-name"
                defaultValue=""
                onChange={(e) => {
                  const el = e.target as HTMLInputElement;
                  el.dataset.value = e.target.value;
                }}
              />
              <Button
                onClick={async () => {
                  const inputEl = document.getElementById("team-name") as HTMLInputElement | null;
                  const teamName = (inputEl?.dataset.value ?? inputEl?.value ?? "").trim();
                  if (!teamName) {
                    showToast("Enter a team name", "error");
                    return;
                  }
                  if (teamSeed.length === 0) {
                    showToast("Select at least one agent", "error");
                    return;
                  }
                  try {
                    await api.createTeam({ name: teamName, agents: teamSeed }, selectedProfile || undefined);
                    await reload();
                    setTeamSeed([]);
                    showToast(`Created team ${teamName}`);
                  } catch {
                    showToast("Failed to create team", "error");
                  }
                }}
              >
                <Plus className="mr-2 h-4 w-4" /> Create team
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {teamResult && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between text-sm">
              <span>Team run: {teamResult.name}</span>
              <Button variant="ghost" size="icon" onClick={() => setTeamResult(null)}>
                <X className="h-3.5 w-3.5" />
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-1">
            {teamResult.tasks.map((t, i) => (
              <div key={i} className="flex items-start gap-2 text-xs">
                <span className="font-mono-ui">{t.agent}</span>
                {t.error ? (
                  <span className="text-destructive">{t.error}</span>
                ) : (
                  <span className="text-muted-foreground">{t.goal}</span>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Active subagents</CardTitle>
        </CardHeader>
        <CardContent>
          {active.length === 0 ? (
            <p className="text-sm text-muted-foreground">No subagents currently running.</p>
          ) : (
            <div className="flex flex-col">
              {active.map((a) => (
                <div key={a.subagent_id} className="flex items-center gap-2 px-2 py-1.5 text-xs">
                  <span className="font-mono-ui">{a.subagent_id}</span>
                  <Badge variant="secondary">{a.status}</Badge>
                  <span className="truncate text-muted-foreground">{a.goal}</span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {editing && (
        <AgentEditor
          editName={
            editing.mode === "edit" ? editing.agent.name : null
          }
          existing={editing.mode === "edit" ? editing.agent : null}
          skills={skills}
          toolsets={toolsets}
          profile={selectedProfile || undefined}
          onClose={() => setEditing(null)}
          onSaved={async () => {
            await reload();
            setEditing(null);
          }}
        />
      )}
    </div>
  );
}
