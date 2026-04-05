<p align="center">
  <img src="https://img.shields.io/badge/License-AGPL--3.0-blue?style=for-the-badge" alt="License">
  <img src="https://img.shields.io/badge/Python-3.14+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20MacOS-4eb8a9?style=for-the-badge" alt="Platform">
  <img src="https://img.shields.io/badge/Status-Alpha-orange?style=for-the-badge" alt="Status">
</p>

<h1 align="center">🐺 GrimmBot </h1>

⚠️**LICENSE NOTICE**⚠️

**IN ORDER TO USE THIS SOFTWARE, YOU MUST READ, UNDERSTAND AND AGREE TO THE THE GNU AGPL V3 LICENSE INCLUDED IN THIS REPOSITORY.**

<p align="center">
  <strong>The self-improving sandboxed AI agent that adapts to failure, with persistent memory and scheduling. </strong>
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
When GrimmBot hits an error, it doesn't just retry. It activates an **Error Analysis Engine** that makes it reflect on what went wrong and writes a permanent rule into a special file (`adaptation.json`). Next time? It doesn't make the same mistake. 

</td>
</tr>
<tr>
<td>

### 🛠️ It Builds New Tools For Itself When Necessary
Need GrimmBot to do something it wasn't built for? It will write a brand new Python tool *on the fly*, register it, and use it immediately. You don't need to code anything. Tell it what you need and it creates the capability itself.

</td>
<td>

### 🛡️ Security 
It has quite a few security features, such as the fact that it runs in a Docker container, has human approval prompts for certain actions, along with command and domain whitelists (in the .env file).
</td>
</tr>
</table>

---

## 🖼️ Gallery

> *GrimmBot's UI when you go to localhost:5000*

<img width="1363" height="637" alt="UI" src="https://github.com/user-attachments/assets/668d2343-f1f6-4f1b-91a8-588de3ac446d" />

---

### Adaptation in Action
> *GrimmBot encounters an error, reflects on it, writes a permanent rule to adaptation.json, and then succeeds on the retry using the new rule.*

<img width="1356" height="634" alt="Adaptation In Action" src="https://github.com/user-attachments/assets/0e0bd5cf-76d4-45d4-931e-d36286ea2b28" />

---

### Custom Tool Creation
> *See GrimmBot prompt the user for permission to create a custom tool that extracts a .zip file*

<img width="1350" height="615" alt="Custom Tool Creation Approval Prompt" src="https://github.com/user-attachments/assets/978797a1-ce22-40f2-bc06-1f7dfc4ec3a2" />

---

## ⚡ How to run it:

**Prerequisites:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.

**1. Clone and configure:**
```bash
git clone https://github.com/Grimm67123/GrimmBot.git
cd GrimmBot
```

**2. Create your `.env` file:**
```ini
LITELLM_API_KEY=your-api-key-here
LLM_MODEL=provider/example-model-name
ALLOWED_DOMAINS=*
ALLOWED_COMMANDS=*
```

**3. Launch:**
```bash
docker-compose up --build 
```

**4. Open your browser in order to talk with it:**
> **http://localhost:5000**

Docker automatically creates a data folder and a wormhole folder in the folder where the docker-compose.yml file is kept. These folders are mapped to the corresponding folders in the Docker container. You can send and receive files to and from the agent through the wormhole folder. Whenver the agent adapts to an error or failure of some sort, it creates an adaptation.json file which gets mapped to the data folder on the host and saves a rule on how to avoid that error/failure in the future to that file. When it creates a custom tool, it creates a custom_tool.json file which gets mapped to the data folder on the host and the custom tools get saved there. Same goes for memory whenever it remembers something. BE CAUTIOUS WITH THE FILES IN THE WORMHOLE AND DATA FOLDER!

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
| 🛠️ **Self-Improvement** | Create and save custom tools at runtime |
| 🧬 **Adaptation** | When encountered with an error or failure, it reflects on it and saves a rule on how to avoid it to adaptation.json |

---

## 📋 FAQ

<details>
<summary><strong>What LLMs does GrimmBot support?</strong></summary>
<br>
GrimmBot uses <a href="https://github.com/BerriAI/litellm">LiteLLM</a> under the hood, which means it supports <strong>every major provider</strong>: OpenAI, Anthropic, Google Gemini, Mistral, Groq, Ollama (local models), and more. Just set the <code>LLM_MODEL</code> and <code>LITELLM_API_KEY</code> in your <code>.env</code> file.
</details>
<details>
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
