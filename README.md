<p align="center">
  <img src="https://img.shields.io/badge/License-AGPL--3.0-blue?style=for-the-badge" alt="License">
  <img src="https://img.shields.io/badge/Python-3.14+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-4eb8a9?style=for-the-badge" alt="Platform">
  <img src="https://img.shields.io/badge/Status-Alpha-orange?style=for-the-badge" alt="Status">
</p>

<h1 align="center">🐺 GrimmBot (Alpha Version)</h1>

⚠️**LICENSE NOTICE**⚠️

**IN ORDER TO USE THIS SOFTWARE, YOU MUST READ, UNDERSTAND AND AGREE TO THE THE GNU AGPL V3 LICENSE INCLUDED IN THIS REPOSITORY.**

<p align="center">
  <strong>The AI agent that writes its own tools, learns from its failures, and actually controls a computer. With persistent memory and scheduling. </strong>
</p>

<p align="center">
  <em>Not another chatbot wrapper. Not another API playground.<br>A full autonomous agent with a live virtual desktop, a browser, a terminal, and a brain that evolves.</em>
</p>

<p align="center">
  <a href="#-quickstart-under-2-minutes">Quickstart</a> •
  <a href="#-what-makes-grimmbot-different">Why GrimmBot</a> •
  <a href="#%EF%B8%8F-the-interface">Interface</a> •
  <a href="#-how-adaptation-works">Adaptation</a> •
  <a href="#-security">Security</a> •
  <a href="#-faq">FAQ</a>
</p>

> **📌 This is a closed-contribution project.** GrimmBot is not accepting external pull requests or feature contributions at this time. You are welcome to fork, study, and use the code under the terms of the AGPL-3.0 license.

---

## 💡 The Problem

Most AI agents are limited by the tools and prompt they're shipped with. If they fail and hit an error, they don't permanently learn how to avoid it. 

**GrimmBot is different.**

---

## 🧬 What Makes GrimmBot Different

<table>
<tr>
<td width="50%">

### 🖥️ Real Computer Control
GrimmBot doesn't just call APIs. It controls a real Chromium browser, moves the mouse, types on the keyboard, reads the screen — and you watch it all happen live through a beautiful web dashboard. Runs natively on Windows or in a hardened Docker sandbox.

</td>
<td width="50%">

### 🧠 It Learns. Permanently.
When GrimmBot hits an error, it doesn't just retry. It activates an **Error Analysis Engine** that reflects on what went wrong and writes a permanent rule into its own brain (`adaptation.json`). Next time? It doesn't make the same mistake. 

</td>
</tr>
<tr>
<td>

### 🛠️ It Builds Its Own Tools And Improves its System Prompt
Need GrimmBot to do something it wasn't built for? It will write a brand new Python tool *on the fly*, register it, and use it immediately. You don't need to code anything. Tell it what you need and it creates the capability itself.

If you need the agent to do certain specialized tasks, it can even improve its own system prompt to suit your needs. Of course, this needs approval on your part.

</td>
<td>

### 🛡️ Smart Security (`commssafeguard`)
Runs with domain allowlists, command allowlists, and a smart communication filter. The `commssafeguard` automatically detects "Send", "Post", or "Submit" buttons and pauses for your approval. Your host machine is protected by layers of approval-based tool execution.

</td>
</tr>
</table>

---

## 🎬 Demos

### Custom Tool Creation
> *GrimmBot is asked to perform a task it has no built-in tool for. Watch it write, register, and immediately use a brand new Python tool — all autonomously.*

<!-- PLACEHOLDER: Record a screen capture of GrimmBot receiving a task, creating a custom tool via create_custom_tool(), and then using it to complete the task. Show the chat panel on the left and the live VNC desktop on the right. -->

https://github.com/user-attachments/assets/PLACEHOLDER-custom-tool-demo.mp4

---

### Adaptation in Action
> *GrimmBot encounters an error, reflects on it, writes a permanent rule to adaptation.json, and then succeeds on the retry using the new rule.*

<!-- PLACEHOLDER: Record a screen capture showing GrimmBot failing a task, the Error Analysis Engine activating, a rule being written to adaptation.json, and then the agent succeeding on the next attempt. -->

https://github.com/user-attachments/assets/PLACEHOLDER-adaptation-demo.mp4

---

### Live Desktop Control
> *Watch GrimmBot open a browser, navigate to a website, interact with page elements, and report back — all in real-time through the web dashboard.*

<!-- PLACEHOLDER: Record a screen capture of the full web interface. Show the user typing a prompt like "Go to Wikipedia and find the population of Tokyo", then watch the VNC panel as GrimmBot opens Chromium, navigates, reads the DOM, and returns the answer in chat. -->

https://github.com/user-attachments/assets/PLACEHOLDER-desktop-control-demo.mp4

---

## ⚡ Quickstart (Under 2 Minutes)

**Prerequisites:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.

**1. Clone and configure:**
```bash
git clone https://github.com/Grimm67123/GrimmBot.git
cd GrimmBot
```

**2. Create your `.env` file:**
```ini
LITELLM_API_KEY=sk-your-api-key-here
LLM_MODEL=gemini/gemini-2.5-flash
ALLOWED_DOMAINS=*
ALLOWED_COMMANDS=*
```

**3. Launch:**
```bash
docker-compose up --build 
```

**4. Open your browser:**
> **http://localhost:5000**

Accept the license & security disclaimer, and you're in. That's it. No Python environment setup, no dependency hell, no configuration nightmares. To turn it on after building, do docker compose up. To turn it off, do docker compose down.

---

## 🖥️ The Interface

GrimmBot ships with a premium, dark-mode web interface — not a terminal.

| Chat Panel | Live Workspace |
|:---|:---|
| A sleek chat UI where you instruct the agent, approve actions, and see results in real-time. Includes a command palette, throttle controls, and emergency stop. | A live noVNC stream of GrimmBot's virtual desktop. Watch it open browsers, type into forms, navigate websites, and run terminal commands — all in real-time. |

**Built-in chat commands:**
| Command | What it does |
|---------|-------------|
| `!help` | Show all commands |
| `!throttle 3` | Slow the agent down (3s between steps) so you can watch it work |
| `!commssafeguard` | Require your approval before the agent types or presses Enter / Send |
| `!login <url>` | Open a URL in the agent's browser for manual login via VNC |
| `!reset` | Wipe the agent's short-term memory |
| `!files` | List all files the agent has created |
| `!tools` | Show every tool the agent has available |
| `!custom-tools` | List tools the agent has built for itself |

---

## 🧬 How Adaptation Works

This is GrimmBot's secret weapon. Here's a real scenario:

1. You tell GrimmBot: *"Watch Amazon for when this product drops below $50."*
2. Other agents would call the LLM in a loop — burning through your API credits every 10 seconds just to read a price tag. Something a 5-line Python script could do.
3. **GrimmBot adapts.** It writes a custom monitoring tool, registers it, and goes to sleep. The tool runs a lightweight loop checking the DOM. Zero API calls. Zero wasted tokens. When the price drops, it wakes up and tells you.
4. It even *remembers* it built this tool. Next time you ask something similar, it already knows the pattern.

Every lesson it learns gets saved to `adaptation.json` — a file that lives on your machine. You can read it, edit it, or share it with others.


---

## 🔧 Full Tool Arsenal

GrimmBot ships with **50+ built-in tools** across these categories:

| Category | Capabilities |
|----------|-------------|
| 🖱️ **Desktop** | Click, double-click, drag, scroll, type, press hotkeys, take screenshots |
| 🌐 **Browser** | Open/close Chromium, navigate URLs, read DOM, click elements by ID, manage tabs and profiles |
| 📁 **Files** | Read, write, patch, insert, delete lines, search across files, convert documents |
| 💻 **Shell** | Execute commands, install packages, compile code, run scripts |
| 🧠 **Memory** | Persistent, human-readable `memory.json` store that survives restarts |
| 📅 **Scheduling** | One-time, daily, and interval-based autonomous task execution |
| 🛠️ **Self-Modification** | Create, list, and delete custom tools at runtime |


---

## 📋 FAQ

<details>
<summary><strong>What LLMs does GrimmBot support?</strong></summary>
<br>
GrimmBot uses <a href="https://github.com/BerriAI/litellm">LiteLLM</a> under the hood, which means it supports <strong>every major provider</strong>: OpenAI, Anthropic, Google Gemini, Mistral, Groq, Ollama (local models), and more. Just set the <code>LLM_MODEL</code> and <code>LITELLM_API_KEY</code> in your <code>.env</code> file.
</details>
<summary><strong>Can it run local/offline models?</strong></summary>
<br>
Yes. Point <code>LLM_MODEL</code> at an Ollama endpoint or any OpenAI-compatible local server. Vision features require a model that supports image inputs.
</details>

<details>
<summary><strong>How do I test it?</strong></summary>
<br>
Do pip install pytest. After turning on and building GrimmBot (through docker-compose up --build) run "pytest tests/ -v" in the terminal inside the GrimmBot folder. Watch it pass every test. 
206: </strong>
</details>

<details>
<summary><strong>Can I see what it's doing in real-time?</strong></summary>
<br>
Yes — the right panel of the web UI is a live noVNC feed of the agent's virtual desktop. You can watch it click, type, and browse.
---

<p align="center">
  <strong>If GrimmBot impressed you, consider giving it a ⭐</strong><br>
  <em>It helps others discover the project and motivates continued development.</em>
</p>
