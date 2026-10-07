## 3-minute recording script

Keep the tool, memo and a terminal open. Speak in your own words; these are talking points.

**0:00-0:30 Task**
"Neha wants breaches by agent and shift, weekly. The email isn't a spec, so before coding I read the policy and the thread. Three things mattered: first response is measured from creation, the export is UTC while shifts are IST, and breaches are reported against the resolving agent. Finance has frozen hiring, and the morning team is already demoralised, so I wanted something fair as well as correct."

**0:30-1:15 First version**
"My first prompt asked the assistant to read every file and list the data quality issues before writing code. It found 616 duplicate tickets from the migration. My first calculation was simple: breach rate by the agent's rostered shift. It said Morning was at 32 percent and Day at 8, which matched what Neha expected."

**1:15-2:00 What changed**
"That didn't feel finished, so I split breaches by the hour the ticket arrived. Tickets arriving overnight breached 79 percent of the time since July 2025 and about 10 percent before. All of those were answered between 6 and 10 in the morning, when the Morning shift starts, and the roster shows Night assignments ending in June 2025. So the morning team inherits the overnight queue. I kept the agent view but added a rate that excludes overnight arrivals, and a minimum-volume flag."

**2:00-2:30 Discarded**
"I dropped a language-model summary because it adds nothing the numbers can't say, and I didn't want an AI computing breaches. The summary text is a template on the numbers. I also dropped an estimate for the cost of overnight cover, since the data doesn't price it, and the CSAT analysis, which wasn't asked for."

**2:30-3:00 Final**
"Here's the dashboard: overview, agents, shifts, ticket evidence. On the validation tab, 500 random tickets were recomputed separately with no differences, plus 10 unit tests. That checks the code, not my reading of the policy, and I say so. The target is overnight breaches from 79 to 40 percent, which is about Rs 65,000 a quarter in credits, excluding the cost of the cover."
