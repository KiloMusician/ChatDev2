/**
 * 🔗 GitHub Integration Service - Infrastructure-First PR Pipeline
 * CoreLink Foundation - Autonomous Development Ecosystem
 * 
 * Converts PUs (Proposal Units) into GitHub PRs with CI/CD integration
 * Following Infrastructure-First Principles: GitHub as single source of truth
 */

import type { Request, Response } from "express";
import crypto from "node:crypto";
import { Octokit } from "octokit";
import { App } from "octokit";

type FilePatch = {
  path: string;
  content: string;          // full file content (UTF-8)
  mode?: "100644" | "100755";
};

type CommitPlan = {
  branch: string;           // e.g. "agent/Z67-selfplay-smoke"
  title: string;            // commit + PR title
  body?: string;            // PR body
  base?: string;            // default "main"
  files: FilePatch[];       // full-file writes (simpler, safe)
  labels?: string[];        // e.g. ["automerge","agent"]
  draft?: boolean;
};

type PUToPRInput = {
  id?: string;
  branch?: string;
  base?: string;
  title?: string;
  files?: FilePatch[];
  labels?: string[];
  phase?: string;
  automerge?: boolean;
  draft?: boolean;
  body?: string;
};

// **CONFIGURATION** - Environment-driven settings
const repo = process.env.GIT_REPO || "corelink/foundation";
const [ownerRaw, repoNameRaw] = repo.split("/");
const owner = ownerRaw || "corelink";
const repoName = repoNameRaw || "foundation";
const defaultBranch = process.env.DEFAULT_BRANCH || "main";
const automergeLabel = process.env.AUTO_MERGE_LABEL || "automerge";

/**
 * **GITHUB CLIENT** - App authentication preferred, PAT fallback
 */
async function getOctokit() {
  const appId = process.env.GH_APP_ID;
  const installationId = process.env.GH_APP_INSTALLATION_ID;
  const key = process.env.GH_APP_PRIVATE_KEY;
  
  if (appId && installationId && key) {
    const app = new App({ 
      appId, 
      privateKey: key.replace(/\\n/g, "\n") 
    });
    return await app.getInstallationOctokit(Number(installationId));
  }
  
  const token = process.env.GH_TOKEN;
  if (!token) {
    throw new Error("No GitHub credentials found. Set either GH_APP_* or GH_TOKEN");
  }
  
  return new Octokit({ auth: token });
}

/**
 * **BRANCH MANAGEMENT** - Ensure branch exists from base
 */
async function ensureBranch(octokit: Awaited<ReturnType<typeof getOctokit>>, base: string, newBranch: string) {
  try {
    const baseRef = await octokit.rest.git.getRef({ 
      owner, 
      repo: repoName, 
      ref: `heads/${base}` 
    });
    const sha = baseRef.data.object.sha;
    
    try {
      await octokit.rest.git.getRef({ 
        owner, 
        repo: repoName, 
        ref: `heads/${newBranch}` 
      });
      console.log(`[GitBot] Branch ${newBranch} already exists`);
      return;
    } catch {
      await octokit.rest.git.createRef({ 
        owner, 
        repo: repoName, 
        ref: `refs/heads/${newBranch}`, 
        sha 
      });
      console.log(`[GitBot] Created branch ${newBranch} from ${base}`);
    }
  } catch (error) {
    console.error(`[GitBot] Branch creation failed:`, error);
    throw error;
  }
}

/**
 * **CORE PR CREATION** - Commit files and open/update PR
 */
async function makeCommitAndPR(plan: CommitPlan): Promise<string> {
  const octokit = await getOctokit();
  const base = plan.base || defaultBranch;
  
  console.log(`[GitBot] Creating PR: ${plan.title}`);
  console.log(`[GitBot] Branch: ${plan.branch}, Files: ${plan.files.length}`);
  
  await ensureBranch(octokit, base, plan.branch);

  // **1) GET LATEST COMMIT**
  const headRef = await octokit.rest.git.getRef({ 
    owner, 
    repo: repoName, 
    ref: `heads/${plan.branch}` 
  });
  const headSha = headRef.data.object.sha;

  // **2) GET BASE TREE**
  const commit = await octokit.rest.git.getCommit({ 
    owner, 
    repo: repoName, 
    commit_sha: headSha 
  });
  const baseTreeSha = commit.data.tree.sha;

  // **3) CREATE BLOBS FOR FILES**
  const blobs = await Promise.all(plan.files.map(async f => {
    const blob = await octokit.rest.git.createBlob({ 
      owner, 
      repo: repoName, 
      content: f.content, 
      encoding: "utf-8" 
    });
    return { 
      path: f.path, 
      mode: f.mode || "100644", 
      type: "blob" as const, 
      sha: blob.data.sha 
    };
  }));

  // **4) CREATE NEW TREE**
  const tree = await octokit.rest.git.createTree({
    owner, 
    repo: repoName, 
    base_tree: baseTreeSha, 
    tree: blobs
  });

  // **5) CREATE COMMIT**
  const commitMsg = plan.title;
  const newCommit = await octokit.rest.git.createCommit({
    owner, 
    repo: repoName, 
    message: commitMsg, 
    tree: tree.data.sha, 
    parents: [headSha]
  });

  // **6) UPDATE BRANCH REF**
  await octokit.rest.git.updateRef({
    owner, 
    repo: repoName, 
    ref: `heads/${plan.branch}`, 
    sha: newCommit.data.sha, 
    force: true
  });

  // **7) OPEN OR UPDATE PR**
  const prs = await octokit.rest.pulls.list({
    owner, 
    repo: repoName, 
    head: `${owner}:${plan.branch}`, 
    state: "open"
  });
  
  type PRRef = { number: number; node_id: string; html_url: string };
  let pr: PRRef | null = prs.data[0]
    ? { number: prs.data[0].number, node_id: prs.data[0].node_id, html_url: prs.data[0].html_url }
    : null;
  if (pr) {
    console.log(`[GitBot] Updated existing PR #${pr.number}`);
  } else {
    const created = (await octokit.rest.pulls.create({
      owner, 
      repo: repoName,
      title: plan.title,
      head: plan.branch,
      base,
      body: plan.body || `🤖 **Autonomous System Generated**\n\nThis PR was created by the CoreLink Foundation autonomous development system.\n\n**Files changed:** ${plan.files.length}\n**Branch:** ${plan.branch}`
    })).data;
    pr = { number: created.number, node_id: created.node_id, html_url: created.html_url };
    console.log(`[GitBot] Created new PR #${pr.number}`);
  }

  if (!pr) {
    throw new Error('[GitBot] PR creation failed');
  }

  // **8) ADD LABELS**
  if (plan.labels?.length) {
    await octokit.rest.issues.addLabels({ 
      owner, 
      repo: repoName, 
      issue_number: pr.number, 
      labels: plan.labels 
    });
    console.log(`[GitBot] Added labels: ${plan.labels.join(', ')}`);
  }

  // **9) REQUEST AUTO-MERGE** (if supported)
  try {
    if (plan.labels?.includes(automergeLabel)) {
      await octokit.graphql(`
        mutation($pr:ID!) {
          enablePullRequestAutoMerge(input:{pullRequestId:$pr, mergeMethod: SQUASH}) { 
            clientMutationId 
          }
        }
      `, {
        pr: pr.node_id
      });
      console.log(`[GitBot] Auto-merge enabled for PR #${pr.number}`);
    }
  } catch (error) {
    console.warn(`[GitBot] Auto-merge request failed (may be expected on PAT):`, error);
  }

  return pr.html_url;
}

export async function createPRsFromPUs(pus: PUToPRInput[]): Promise<Array<{ id?: string; prUrl: string; branch: string; filesCount: number }>> {
  const results: Array<{ id?: string; prUrl: string; branch: string; filesCount: number }> = [];

  for (const pu of pus) {
    // **BRANCH NAMING** - Safe, descriptive
    const branchSuffix = pu.id || crypto.randomUUID().slice(0, 8);
    const branch = (pu.branch || `agent/${branchSuffix}`)
      .replace(/\s+/g, "-")
      .replace(/[^a-zA-Z0-9\-_/]/g, "")
      .slice(0, 60);

    const base = pu.base || defaultBranch;
    const title = pu.title || `[PU] ${pu.id || 'Autonomous Task'}`;

    // **FILE PROCESSING**
    const files: FilePatch[] = (pu.files || []).map((f: any) => ({
      path: String(f.path),
      content: String(f.content),
      mode: f.mode && String(f.mode) === "100755" ? "100755" : "100644"
    }));

    if (files.length === 0) {
      console.warn(`[GitBot] PU ${pu.id} has no files, skipping`);
      continue;
    }

    // **LABELS** - Auto-categorization
    const labels = pu.labels || ["agent", pu.phase || "autonomous"];
    if (pu.automerge) {
      labels.push(automergeLabel);
    }

    const prUrl = await makeCommitAndPR({
      branch,
      base,
      title,
      files,
      labels,
      draft: !!pu.draft,
      body: pu.body
    });

    results.push({
      id: pu.id,
      prUrl,
      branch,
      filesCount: files.length
    });
  }

  return results;
}

/**
 * **API HANDLER** - Convert PUs to PRs
 */
export async function queuePUToPR(req: Request, res: Response) {
  try {
    const payload = Array.isArray(req.body) ? req.body : [req.body];
    
    console.log(`[GitBot] Processing ${payload.length} PU(s) to PR(s)`);
    
    const results = await createPRsFromPUs(payload);
    
    console.log(`[GitBot] ✅ Created ${results.length} PR(s)`);
    res.json({ 
      ok: true, 
      count: results.length, 
      results,
      timestamp: Date.now()
    });
    
  } catch (error: any) {
    console.error(`[GitBot] ❌ queuePUToPR failed:`, error);
    res.status(500).json({ 
      ok: false, 
      error: String(error?.message || error),
      timestamp: Date.now()
    });
  }
}

/**
 * **WEBHOOK VERIFICATION** - HMAC validation for GitHub webhooks
 */
export function verifyGitHubWebhook(signature: string, body: string, secret: string): boolean {
  const hmac = crypto.createHmac('sha256', secret);
  hmac.update(body);
  const expected = `sha256=${hmac.digest('hex')}`;
  return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected));
}

/**
 * **SYNC HANDLER** - Pull latest changes from GitHub
 */
export async function handleReplitSync(req: Request, res: Response) {
  try {
    const sig = req.get('X-Signature') || '';
    const ts = req.get('X-Timestamp') || '';
    const secret = process.env.REPLIT_SYNC_SECRET || '';
    
    if (!secret) {
      return res.status(500).json({ error: 'REPLIT_SYNC_SECRET not configured' });
    }
    
    // **SIGNATURE VERIFICATION**
    const hmac = crypto.createHmac('sha256', secret);
    hmac.update(ts);
    const expected = hmac.digest('base64');
    const isValid = crypto.timingSafeEqual(
      Buffer.from(sig || '', 'base64'), 
      Buffer.from(expected)
    );
    
    if (!isValid) {
      console.warn(`[Sync] Invalid signature from GitHub webhook`);
      return res.status(401).json({ error: 'Invalid signature' });
    }
    
    console.log(`[Sync] ✅ Valid GitHub webhook received`);
    
    // **SYNC OPERATION** - Pull latest changes
    const { exec } = await import('node:child_process');
    exec('git fetch origin main && git checkout main && git reset --hard origin/main', 
      (error, stdout, stderr) => {
        if (error) {
          console.error(`[Sync] Git pull failed:`, error);
        } else {
          console.log(`[Sync] ✅ Synced with GitHub main`);
          console.log(`[Sync] Output:`, stdout);
        }
        
        if (stderr) {
          console.warn(`[Sync] Git warnings:`, stderr);
        }
      }
    );
    
    // **GENTLE RESTART** - Allow current requests to complete
    setTimeout(() => {
      console.log(`[Sync] 🔄 Restarting to apply changes...`);
      process.exit(0);
    }, 1500);
    
    res.json({ 
      ok: true, 
      message: 'Sync initiated, restarting in 1.5s',
      timestamp: Date.now()
    });
    
  } catch (error: any) {
    console.error(`[Sync] ❌ Sync failed:`, error);
    res.status(500).json({ 
      ok: false, 
      error: String(error?.message || error),
      timestamp: Date.now()
    });
  }
}
