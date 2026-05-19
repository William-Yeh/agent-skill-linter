# The Checklist Manifesto — HOW-TOs Mapped to agent-skill-linter

Source: 《清單革命》(*The Checklist Manifesto*) by Atul Gawande, Ch. 6 「清單工廠」 (The Checklist Factory) and Ch. 7 「上路」 (The Test).

This doc extracts the *concrete* HOW-TOs the book gives for designing and shipping a working checklist, then maps each one to where (or whether) the current linter enforces it. The goal is to (a) audit coverage of the book's principles, and (b) surface gaps that could justify new rules or workflow steps.

Three coverage columns are used throughout:

| Column | Meaning |
|---|---|
| **Linter rule** | Statically enforced by `skill-lint.py check` (rules 1–25). |
| **Semantic step** | Caught in Steps 5–9 of the agent triage workflow in `skill/SKILL.md`. The current set is enumerated in `references/semantic-rules.md`. |
| **Gap** | Neither enforced nor reviewed; candidate for a new rule or step. |

---

## HOW #1 — Choose the execution mode up front: READ-DO vs. DO-CONFIRM

> 「你必須決定採用操作確認模式，或是大家一起一步步照著清單來做。前者是由團隊成員根據他們的記憶與經驗分頭去檢查各個項目，然後暫停，最後確認該做的是否都做了；後者則像食譜，唸一項做一項。」 — Ch. 6, 「清單是簡便、迅速解決問題的工具」

Two modes, picked per task: DO-CONFIRM for fluid, expertise-driven work (the WHO surgery checklist landed here — "彈性、團隊成員能在關鍵之處停下來" Ch. 7 §1); READ-DO for tight, unforgiving sequences (cargo-door pressurization, fuel-icing recovery — Ch. 6).

**Mapping to agent skills:**

| Coverage | Where |
|---|---|
| Linter rule | — none — |
| Semantic step | Implicit in Step 9: the workflow gate question "does every substantive step state how the agent knows it is done?" presumes the skill author already chose a mode; it does not ask *which*. |
| Gap | **Yes.** No rule asks the skill to declare its mode. A natural fit would be: if `SKILL.md` contains `### Step N` headings, expect a short preamble like "(READ-DO)" or "(DO-CONFIRM, pause at X)" so the agent knows whether to follow the steps literally or to use them as a confirmation pass after acting. |

---

## HOW #2 — Set explicit pause points (Pause Points)

> 「首先，你得確定使用清單的暫停點（例如警示燈亮起或是引擎故障）。」 — Ch. 6, 「清單是簡便、迅速解決問題的工具」

The WHO surgery checklist has exactly three pause points: *before anesthesia / before incision / before patient leaves the OR* (Ch. 7, 「拍板定案的WHO手術清單共有十九個查核項目」). Each is tied to a physical, observable event — not a vague "review your work" moment.

**Mapping to agent skills:**

| Coverage | Where |
|---|---|
| Linter rule | Rule 16 (`references/semantic-rules.md`) — Step-conditional headings (`Step N`, `Phase N`, `After…`, `Once…`) with body >30 lines. Heading-level signal for "this section is conditional on a trigger". |
| Semantic step | Step 8 — "would an agent look up this section reactively rather than read it upfront?" forces reactive content under `references/`, which is itself a pause-point pattern (load only when the trigger fires). Also Step 8 second sub-question (Rule 27) — flags conditional sections whose trigger is vague rather than naming an observable event. |
| Gap | Closed in v0.15.0 by Rule 27 (Step 8 sub-question on observable triggers). |

---

## HOW #3 — Hard length limit: 5–9 items per pause point, 60–90 seconds to execute

> 「清單列的項目不可太多，最好是在五項到九項之間，因為這樣最容易記憶。」 「但從暫停點開始，六十到九十秒後，人的專注力就會降低，開始省略某些步驟，因此清單必須列出最關鍵的項目。」 — Ch. 6

This is the book's most cited HOW. The WHO checklist's three pause points contain 7 / 7 / 5 items respectively — all within the 5–9 band. Boorman's reason isn't ergonomic preference; it's a hard cognitive ceiling.

**Mapping to agent skills:**

| Coverage | Where |
|---|---|
| Linter rule | Rule 9 (Info) — SKILL.md body < 500 lines. This is a *body-length* heuristic, not a per-pause-point count. |
| Semantic step | — none — |
| Gap | **Yes.** No rule counts items per `### Step N` block. A new rule could fire a Warning when any single step contains >9 actionable bullets (or >9 numbered sub-steps), citing the 5–9 principle. This would catch "kitchen-sink" steps that bury the critical items. The book is explicit that adding *more* makes the checklist *less* effective — the same is true of agent prompts ("中間遺忘 / lost in the middle"). |

---

## HOW #4 — Use the trade's jargon, not plain prose

> 「清單的用字遣詞要簡單、明確，使用業界最熟悉的語言。」 — Ch. 6

The pilots' "氧氣檢查" → "測試過了，百分之百純氧" exchange is one token of trade vocabulary, not a paragraph. The book argues jargon *compresses* the checklist; verbose translations *bloat* it.

**Mapping to agent skills:**

| Coverage | Where |
|---|---|
| Linter rule | Rule 11 (Warning) — `description` starts with "Use when…". Forces a routing-vocabulary convention. |
| Semantic step | Step 5 — flags descriptions that "Enumerate what the skill checks" or "Read as a feature summary or workflow overview". |
| Gap | Partial. Rules 11 + Step 5 cover the *description* field, but not the body of `### Step N` blocks. Steps written in prose ("Please consider examining whether…") versus jargon ("Run `skill-lint.py check`, then read Errors first") have very different agent-execution profiles. A future check could flag steps without an imperative verb in the opening clause. |

---

## HOW #5 — Layout must fit on one page / one screen; no page-turning

> 「最好單頁就可全部列印出來，同時避免擠成一堆或使用不必要的顏色。」 — Ch. 6

The physical constraint maps directly to the agent's context window. A checklist that requires scrolling defeats its purpose during a pause point.

**Mapping to agent skills:**

| Coverage | Where |
|---|---|
| Linter rule | Rule 9 (Info) — body < 500 lines. Rule 14 (Warning) — embedded template fences (4-backtick) must move to `references/`. Rule 15 (Warning) — reference-tier headings move to `references/`. |
| Semantic step | Step 8 — progressive-disclosure judgment. |
| Gap | Closed. The progressive-disclosure rule stack (9 / 14 / 15 / 16 / Step 8) is *exactly* this principle applied to LLM context windows: keep the upfront page short; defer reactive content to lazy-loaded references. |

---

## HOW #6 — Distinguish hard steps (prevent dumb errors) from communication steps (handle the unknown)

> 「硬性步驟（預防笨蛋錯誤）：不可妥協的檢查點（如：病人名字對不對、有沒有抗生素）。溝通步驟（應對未知風險）：清單中必須強制加入『團隊自我介紹』與『開放式討論』。」 — Ch. 6 + Ch. 7

The book is explicit that the WHO checklist deliberately retains the "team introduction" step despite weak evidence, because it changes the team's *ability to speak up* mid-procedure (the Jordanian glove-change anecdote in Ch. 7 is the canonical illustration: the nurse felt licensed to correct a male surgeon because the checklist had already established voice).

**Mapping to agent skills:**

| Coverage | Where |
|---|---|
| Linter rule | Hard checks = Rules 1, 2, 24, 25 (Errors). |
| Semantic step | Communication-style review = Steps 5–9 (the agent reads, judges, asks questions). |
| Gap | Partially closed by design — the linter/semantic split *is* the hard-step / communication-step split. The gap is that there is no place in the workflow where the agent is told to verify the *communication scaffolding* of the skill itself: does the skill define how the agent escalates when stuck, asks the human, or hands back control? See HOW #8. |

---

## HOW #7 — Field-test the draft; the office version is always wrong

> 「不管我們再怎麼小心，花多少心血，製作出來的清單仍必須在現實世界中試驗，而且實際運用將會比我們預期的要來得複雜。他說，最初擬好的清單最後往往改得面目全非。」 — Ch. 6
>
> 「波音團隊花了半個月的時間不斷測試和修正，清單終於得以拍板定案。」 — Ch. 6, 「飛行清單的故事」

The WHO team ran London → Hong Kong → 8-hospital pilots before publishing (Ch. 7 §1). Boorman runs every revised pilot checklist through the simulator before pushing it to airlines (Ch. 6 §3).

**Mapping to agent skills:**

| Coverage | Where |
|---|---|
| Linter rule | Rule 5 (Warning) — CI workflow must exist. Rule 7 (Warning, Partial) — Usage section requires *starter prompts* (these are the skill's pilot scenarios). |
| Semantic step | Step 6 — "do starter prompts reflect genuine, distinct trigger scenarios?" This is the linter's nearest analogue to "field-tested". |
| Gap | **Yes.** No rule asks whether the skill ships any **fixture or test corpus** for its behavior (the agent equivalent of Boorman's simulator). For Python-script skills this could be `tests/`; for prompt-only skills, a `references/examples.md` of input/output pairs. The book's strongest claim — "辦公室冷氣房裡寫出來的第一版清單，絕對是垃圾" — has no enforcement here. |

---

## HOW #8 — Build in fallback for the unknown: hand back control after 3 tries

> The book frames this through the team-introduction practice and through Boorman's emphasis that crews *follow the checklist even when they think the warning is a false alarm* — discipline beats intuition. The reference text the user supplied makes this explicit for AI agents:
>
> "若連續嘗試同一工具失敗 3 次，立刻報錯並將控制權交還給人類，不可繼續消耗 Token。"

This is the book's "stop and pull the cord" mechanism applied to LLM tool loops.

**Mapping to agent skills:**

| Coverage | Where |
|---|---|
| Linter rule | — none — |
| Semantic step | Step 9 third sub-question (Rule 26) — flags workflows that loop on tool output without a retry cap or named fallback. |
| Gap | Closed in v0.15.0 by Rule 26 (Step 9 sub-question on bounded retries). |

---

## HOW #9 — Pause point ≠ checklist invocation: name the trigger event

> 「規定在某個特定動作發生『前』或『後』，團隊必須絕對停下來看清單。」 — From the user's synthesis; concretized in the book by examples: "劃刀前 (Time Out)", "飛機關閉艙門後".

The checklist is *worthless* without a clear, unmissable trigger. Boorman's example: pilots don't reach for the cargo-door checklist when the light blinks; they reach for it because they were *trained* that the blinking light is itself the trigger. Training plus a named event.

**Mapping to agent skills:**

| Coverage | Where |
|---|---|
| Linter rule | Rule 11 (Warning) — `description` starts with "Use when…". This *is* the trigger field. |
| Semantic step | Step 5 — flags descriptions that read as feature summaries instead of routing signals. |
| Gap | Closed for skill-level triggers; open for step-level triggers (see HOW #2 gap). |

---

## HOW #10 — Iterate from the data the moment it arrives

> 「波爾曼及其小組仍會把報告仔細過濾，擷取重點，之後將原來使用的標準清單加以修正，再提供給機師。」「在波音發布公告之後，不到一個月，新的清單已出現在機師手中。」 — Ch. 6, 「飛行清單的故事」 (the Delta 777 cold-fuel save proves the loop closes)

Gawande contrasts this with medicine: 17 years to adopt a known-good pneumococcal protocol because the knowledge wasn't compressed into a "簡單、實用而且有系統的表格" (Ch. 6).

**Mapping to agent skills:**

| Coverage | Where |
|---|---|
| Linter rule | Rule 5 (Warning) — CI workflow. Rule 24 / 25 (Errors, plugin mode) — plugin-manifest sanity ensures the skill ships at all. |
| Semantic step | Step 6 — starter prompts must reflect *real* scenarios, which implies the author has observed them. |
| Gap | Soft gap. The linter does not check whether the skill has a versioning convention (`metadata.version` is in Rule 3 territory but the bump cadence isn't enforced) or a CHANGELOG. A weak Info-level rule could nudge skills with `### Step N` workflows to also publish a `references/examples.md` of resolved cases, mirroring Boorman's incident-log → checklist-edit loop. |

---

## Summary: where the book pushes us next

The current rule set — linter rules 1–25 plus a parallel set of semantic rules documented in `references/semantic-rules.md` — encodes most of the book's HOWs, with strongest coverage on **progressive disclosure** (HOW #5), **trigger-as-description** (HOW #9), **bounded retries** (HOW #8, added in v0.15.0), and **observable conditional triggers** (HOW #2, added in v0.15.0).

Remaining under-covered HOWs:

1. **HOW #1** — Skills should declare execution mode (READ-DO vs. DO-CONFIRM). Deferred: most agent skills are DO-CONFIRM by default; add only if mode confusion is observed in real failures.
2. **HOW #3** — Per-step item limit (5–9 actionable items / step). Deferred: already enforced indirectly by Rule 9 + Rules 14/15 (progressive disclosure).
3. **HOW #7** — Skills should ship a fixture/test corpus. Deferred: best as part of a `pre-publish-checklist` flow or `--strict` mode, not as a default rule.

The remaining gaps are intentional — each was judged lower-leverage-per-line than the additions made. Following the book's "去蕪存菁" principle: add only when violations cause real incidents.

**Recommendation, in checklist-manifesto style:**

```
SKILL DESIGN PAUSE POINT — before publish (DO-CONFIRM)

1. Mode declared           READ-DO or DO-CONFIRM
2. Pause points named      observable trigger event
3. ≤ 9 items per step      count under each ### Step N
4. Body fits one screen    Rule 9 / 14 / 15
5. Trade jargon, not prose imperative verb opens each step
6. Test corpus present     references/examples.md or tests/
7. Retry cap + fallback    if the skill loops a tool
```

Seven items. One screen. The book would approve.
